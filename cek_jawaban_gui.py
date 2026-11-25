#!/usr/bin/env python3
"""Aplikasi GUI Desktop (GTK 3) — Penguji Jawaban Lomba Coding Python Penggalang."""

from __future__ import annotations

import pathlib
import sys
import threading

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk, Pango  # noqa: E402

ROOT_DIR = pathlib.Path(__file__).resolve().parent
LATIHAN_DIR = ROOT_DIR / "latihan"
KUNCI_DIR = ROOT_DIR / "kunci_jawaban"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from penguji.core import (  # noqa: E402
    SOAL_TITLES,
    CaseResult,
    FileResult,
    find_soal_files,
    grade_file,
)

APP_CSS = b"""
.score-card {
    background-color: rgba(127, 127, 127, 0.10);
    border: 1px solid rgba(127, 127, 127, 0.25);
    border-radius: 8px;
    padding: 10px 14px;
}
.score-big {
    font-size: 20px;
    font-weight: 700;
}
.score-ok { color: #16a34a; }
.score-mid { color: #d97706; }
.score-bad { color: #dc2626; }
.juknis-ok {
    color: #16a34a;
    font-weight: 600;
}
.juknis-warn {
    color: #ea580c;
    font-weight: 700;
}
.section-title {
    font-weight: 700;
    font-size: 12px;
}
"""


class PengujiWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="Penguji Lomba Coding Python — Penggalang")
        self.set_default_size(1020, 680)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(10)

        self._apply_css()

        self.current_mode: str | None = None  # "file" or "folder"
        self.current_target: pathlib.Path | None = None
        self.row_details: list[tuple[FileResult, CaseResult]] = []
        self.is_running = False

        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(root_box)

        # 1. Toolbar aksi
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        root_box.pack_start(toolbar, False, False, 0)

        self.btn_file = Gtk.Button.new_with_label("Pilih File (.py)")
        self.btn_file.connect("clicked", self.on_pick_file)
        toolbar.pack_start(self.btn_file, False, False, 0)

        self.btn_folder = Gtk.Button.new_with_label("Pilih Folder Tim")
        self.btn_folder.connect("clicked", self.on_pick_folder)
        toolbar.pack_start(self.btn_folder, False, False, 0)

        lbl_soal = Gtk.Label(label="Soal:")
        toolbar.pack_start(lbl_soal, False, False, 4)

        self.combo_soal = Gtk.ComboBoxText()
        self.combo_soal.append("auto", "Otomatis (dari nama file)")
        for num, title in SOAL_TITLES.items():
            self.combo_soal.append(str(num), f"Soal {num} — {title}")
        self.combo_soal.set_active_id("auto")
        toolbar.pack_start(self.combo_soal, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar.pack_start(sep, False, False, 4)

        self.btn_latihan = Gtk.Button.new_with_label("Uji Latihan")
        self.btn_latihan.connect("clicked", lambda _: self.run_folder(LATIHAN_DIR))
        toolbar.pack_start(self.btn_latihan, False, False, 0)

        self.btn_kunci = Gtk.Button.new_with_label("Uji Kunci (Demo)")
        self.btn_kunci.connect("clicked", lambda _: self.run_folder(KUNCI_DIR))
        toolbar.pack_start(self.btn_kunci, False, False, 0)

        self.btn_rerun = Gtk.Button.new_with_label("Uji Ulang")
        self.btn_rerun.set_sensitive(False)
        self.btn_rerun.connect("clicked", self.on_rerun)
        toolbar.pack_end(self.btn_rerun, False, False, 0)

        # 2. Kartu Ringkasan Skor & Juknis
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        card.get_style_context().add_class("score-card")
        root_box.pack_start(card, False, False, 0)

        left_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        card.pack_start(left_info, True, True, 0)

        self.lbl_target = Gtk.Label(
            label="Pilih file .py atau folder jawaban siswa untuk memulai pengujian."
        )
        self.lbl_target.set_xalign(0.0)
        self.lbl_target.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        left_info.pack_start(self.lbl_target, False, False, 0)

        self.lbl_juknis = Gtk.Label(
            label="Aturan Juknis: semua input() wajib kosong tanpa teks di dalam kurung."
        )
        self.lbl_juknis.set_xalign(0.0)
        left_info.pack_start(self.lbl_juknis, False, False, 0)

        self.lbl_score = Gtk.Label(label="—")
        self.lbl_score.get_style_context().add_class("score-big")
        card.pack_end(self.lbl_score, False, False, 4)

        self.progress = Gtk.ProgressBar()
        self.progress.set_fraction(0.0)
        root_box.pack_start(self.progress, False, False, 0)

        # 3. Area Utama (Atas: Tabel Hasil, Bawah: Detail Perbandingan)
        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        paned.set_position(300)
        root_box.pack_start(paned, True, True, 0)

        # Tabel kasus uji
        # Kolom: file_name, soal_str, uji_str, status_text, waktu_str, ringkasan, color_hex, detail_idx
        self.store = Gtk.ListStore(str, str, str, str, str, str, str, int)
        self.tree = Gtk.TreeView(model=self.store)
        self.tree.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)

        col_defs = [
            ("File", 0, 175, None),
            ("Soal", 1, 220, None),
            ("Uji", 2, 70, None),
            ("Status", 3, 105, 6),
            ("Waktu", 4, 75, None),
            ("Ringkasan", 5, 280, None),
        ]
        for title, idx, width, color_col in col_defs:
            renderer = Gtk.CellRendererText()
            if idx == 3:
                renderer.set_property("weight", Pango.Weight.BOLD)
            col = Gtk.TreeViewColumn(title, renderer, text=idx)
            if color_col is not None:
                col.add_attribute(renderer, "foreground", color_col)
            col.set_min_width(width)
            col.set_resizable(True)
            self.tree.append_column(col)

        sel = self.tree.get_selection()
        sel.connect("changed", self.on_row_selected)

        scroll_tree = Gtk.ScrolledWindow()
        scroll_tree.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll_tree.set_shadow_type(Gtk.ShadowType.IN)
        scroll_tree.add(self.tree)
        paned.pack1(scroll_tree, True, False)

        # Panel detail 3 kolom: Input Uji | Output Siswa | Kunci Jawaban
        detail_grid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        detail_grid.set_margin_top(6)
        paned.pack2(detail_grid, True, False)

        self.buf_input = self._make_text_panel(detail_grid, "Input Uji")
        self.buf_actual = self._make_text_panel(detail_grid, "Output Siswa / Error")
        self.buf_expected = self._make_text_panel(detail_grid, "Kunci Jawaban")

    def _apply_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(APP_CSS)
        screen = Gdk.Screen.get_default()
        if screen is not None:
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _make_text_panel(self, parent: Gtk.Box, title: str) -> Gtk.TextBuffer:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        parent.pack_start(box, True, True, 0)

        lbl = Gtk.Label(label=title)
        lbl.set_xalign(0.0)
        lbl.get_style_context().add_class("section-title")
        box.pack_start(lbl, False, False, 0)

        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_cursor_visible(False)
        tv.set_monospace(True)
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.set_left_margin(8)
        tv.set_right_margin(8)
        tv.set_top_margin(6)
        tv.set_bottom_margin(6)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.add(tv)
        box.pack_start(sw, True, True, 0)
        return tv.get_buffer()

    def _selected_soal_override(self) -> int | None:
        active = self.combo_soal.get_active_id()
        if active and active != "auto":
            return int(active)
        return None

    def _set_busy(self, busy: bool) -> None:
        self.is_running = busy
        for btn in (self.btn_file, self.btn_folder, self.btn_latihan, self.btn_kunci):
            btn.set_sensitive(not busy)
        self.btn_rerun.set_sensitive((not busy) and self.current_target is not None)
        if busy:
            self.progress.set_fraction(0.25)

    def on_pick_file(self, _widget: Gtk.Widget) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Pilih File Jawaban Python (.py)",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )
        if LATIHAN_DIR.is_dir():
            dialog.set_current_folder(str(LATIHAN_DIR))

        flt = Gtk.FileFilter()
        flt.set_name("File Python (*.py)")
        flt.add_pattern("*.py")
        dialog.add_filter(flt)

        if dialog.run() == Gtk.ResponseType.OK:
            path = pathlib.Path(dialog.get_filename())
            dialog.destroy()
            self.run_single_file(path)
        else:
            dialog.destroy()

    def on_pick_folder(self, _widget: Gtk.Widget) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Pilih Folder Jawaban Tim",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )
        if ROOT_DIR.is_dir():
            dialog.set_current_folder(str(ROOT_DIR))

        if dialog.run() == Gtk.ResponseType.OK:
            folder = pathlib.Path(dialog.get_filename())
            dialog.destroy()
            self.run_folder(folder)
        else:
            dialog.destroy()

    def on_rerun(self, _widget: Gtk.Widget) -> None:
        if not self.current_target:
            return
        if self.current_mode == "file":
            self.run_single_file(self.current_target)
        elif self.current_mode == "folder":
            self.run_folder(self.current_target)

    def run_single_file(self, path: pathlib.Path) -> None:
        if self.is_running:
            return
        self.current_mode = "file"
        self.current_target = path
        soal_override = self._selected_soal_override()
        self._start_worker([(path, soal_override)], f"File: {path}")

    def run_folder(self, folder: pathlib.Path) -> None:
        if self.is_running:
            return
        self.current_mode = "folder"
        self.current_target = folder
        files = find_soal_files(folder)
        if not files:
            self._show_error(f"Tidak ditemukan file soal1..soal4 (*.py) di:\n{folder}")
            return
        self._start_worker([(f, None) for f in files], f"Folder: {folder}")

    def _start_worker(self, items: list[tuple[pathlib.Path, int | None]], label: str) -> None:
        self._set_busy(True)
        self.store.clear()
        self.row_details.clear()
        self.buf_input.set_text("")
        self.buf_actual.set_text("")
        self.buf_expected.set_text("")
        self.lbl_target.set_text(f"Sedang menguji {label} ...")

        def worker() -> None:
            results: list[FileResult] = []
            error_msg: str | None = None
            try:
                for idx, (path, soal_num) in enumerate(items, start=1):
                    res = grade_file(path, soal_num)
                    results.append(res)
                    GLib.idle_add(self.progress.set_fraction, idx / len(items))
            except Exception as exc:
                error_msg = str(exc)
            GLib.idle_add(self._finish_worker, results, label, error_msg)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_worker(
        self, results: list[FileResult], label: str, error_msg: str | None
    ) -> bool:
        self._set_busy(False)
        if error_msg:
            self.progress.set_fraction(0.0)
            self._show_error(error_msg)
            return False

        self.progress.set_fraction(1.0)
        self.lbl_target.set_text(label)

        bad_files = [
            f"{r.path.name} (baris {', '.join(map(str, r.bad_input_lines))})"
            for r in results
            if r.bad_input_lines
        ]
        ctx_j = self.lbl_juknis.get_style_context()
        ctx_j.remove_class("juknis-ok")
        ctx_j.remove_class("juknis-warn")
        if bad_files:
            ctx_j.add_class("juknis-warn")
            self.lbl_juknis.set_text(
                "⚠ PERINGATAN JUKNIS — input() berisi teks pada: " + "; ".join(bad_files)
            )
        else:
            ctx_j.add_class("juknis-ok")
            self.lbl_juknis.set_text("✓ Aturan Juknis aman: semua input() kosong tanpa teks prompt.")

        total_score = sum(r.score for r in results)
        max_score = min(len(results) * 25, 100)
        self.lbl_score.set_text(f"{total_score} / {max_score}")
        ctx_s = self.lbl_score.get_style_context()
        for cls in ("score-ok", "score-mid", "score-bad"):
            ctx_s.remove_class(cls)
        if total_score == max_score and not bad_files:
            ctx_s.add_class("score-ok")
        elif total_score > 0:
            ctx_s.add_class("score-mid")
        else:
            ctx_s.add_class("score-bad")

        color_map = {
            "LULUS": ("✓ LULUS", "#16a34a"),
            "SALAH": ("✗ SALAH", "#dc2626"),
            "ERROR": ("! ERROR", "#dc2626"),
            "TIMEOUT": ("⏱ TIMEOUT", "#d97706"),
        }

        first_fail_idx: int | None = None
        for r in results:
            for c in r.cases:
                status_lbl, hex_col = color_map.get(c.status, (c.status, "#64748b"))
                if c.status == "LULUS":
                    summary = f"Cocok persis (Skor soal: {r.score}/25)"
                elif c.status == "SALAH":
                    if not c.actual:
                        summary = "Output kosong — klik baris untuk melihat kunci"
                    else:
                        summary = "Output berbeda — klik baris untuk bandingkan"
                else:
                    summary = (c.error_message.splitlines()[-1] if c.error_message else "Terjadi error")

                detail_idx = len(self.row_details)
                self.row_details.append((r, c))
                if first_fail_idx is None and c.status != "LULUS":
                    first_fail_idx = detail_idx

                self.store.append(
                    [
                        r.path.name,
                        f"Soal {r.soal_num}: {r.soal_title}",
                        f"Uji #{c.index}",
                        status_lbl,
                        f"{c.elapsed_ms} ms",
                        summary,
                        hex_col,
                        detail_idx,
                    ]
                )

        if self.row_details:
            target_idx = first_fail_idx if first_fail_idx is not None else 0
            self.tree.set_cursor(Gtk.TreePath.new_from_indices([target_idx]))

        return False

    def on_row_selected(self, selection: Gtk.TreeSelection) -> None:
        model, tree_iter = selection.get_selected()
        if tree_iter is None:
            return
        detail_idx = model[tree_iter][7]
        res, case = self.row_details[detail_idx]

        self.buf_input.set_text(case.input_data)
        if case.status in ("ERROR", "TIMEOUT"):
            actual_txt = case.error_message
            if case.actual:
                actual_txt = f"{case.actual}\n\n--- Error ---\n{case.error_message}"
        elif not case.actual:
            actual_txt = "(kosong — program belum mencetak apa pun)"
        else:
            actual_txt = case.actual

        if res.bad_input_lines:
            baris = ", ".join(map(str, res.bad_input_lines))
            actual_txt = (
                f"[PERINGATAN JUKNIS: input() berisi teks di baris {baris}]\n\n" + actual_txt
            )

        self.buf_actual.set_text(actual_txt)
        self.buf_expected.set_text(case.expected)

    def _show_error(self, message: str) -> None:
        dlg = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Pengujian Tidak Dapat Dijalankan",
        )
        dlg.format_secondary_text(message)
        dlg.run()
        dlg.destroy()


def main() -> None:
    win = PengujiWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    if len(sys.argv) > 1:
        arg_path = pathlib.Path(sys.argv[1]).resolve()
        if arg_path.is_file():
            GLib.idle_add(win.run_single_file, arg_path)
        elif arg_path.is_dir():
            GLib.idle_add(win.run_folder, arg_path)

    Gtk.main()


if __name__ == "__main__":
    main()
