#!/usr/bin/env python3
"""Aplikasi GUI Desktop Lintas-OS — Penguji Jawaban Lomba Coding Python Penggalang.

Otomatis memilih antarmuka terbaik:
- Linux: GTK 3 (PyGObject) jika tersedia, fallback ke Tkinter
- Windows: Tkinter (bawaan Python resmi Windows)
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import threading

ROOT_DIR = pathlib.Path(__file__).resolve().parent
LATIHAN_DIR = ROOT_DIR / "latihan"
KUNCI_DIR = ROOT_DIR / "kunci_jawaban"
MODUL_DIR = ROOT_DIR / "modul"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from penguji.core import (  # noqa: E402
    SOAL_TITLES,
    CaseResult,
    FileResult,
    find_soal_files,
    grade_file,
)


def open_path_in_os(target: pathlib.Path) -> None:
    """Buka folder/file di File Manager bawaan OS (Linux & Windows)."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(target))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(target)])
    except Exception:
        pass


def format_actual_detail(res: FileResult, case: CaseResult) -> str:
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
    return actual_txt


# ==============================================================================
# BACKEND 1: GTK 3 (Native Linux Desktop)
# ==============================================================================
def run_gtk_gui(initial_arg: pathlib.Path | None = None) -> None:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk, Pango

    app_css = b"""
    .score-card {
        background-color: rgba(127, 127, 127, 0.10);
        border: 1px solid rgba(127, 127, 127, 0.25);
        border-radius: 8px;
        padding: 10px 14px;
    }
    .score-big { font-size: 20px; font-weight: 700; }
    .score-ok { color: #16a34a; }
    .score-mid { color: #d97706; }
    .score-bad { color: #dc2626; }
    .juknis-ok { color: #16a34a; font-weight: 600; }
    .juknis-warn { color: #ea580c; font-weight: 700; }
    .section-title { font-weight: 700; font-size: 12px; }
    """

    class PengujiGtkWindow(Gtk.Window):
        def __init__(self) -> None:
            super().__init__(title="Penguji Lomba Coding Python — Penggalang")
            self.set_default_size(1040, 680)
            self.set_position(Gtk.WindowPosition.CENTER)
            self.set_border_width(10)

            provider = Gtk.CssProvider()
            provider.load_from_data(app_css)
            screen = Gdk.Screen.get_default()
            if screen is not None:
                Gtk.StyleContext.add_provider_for_screen(
                    screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )

            self.current_mode: str | None = None
            self.current_target: pathlib.Path | None = None
            self.row_details: list[tuple[FileResult, CaseResult]] = []
            self.is_running = False

            root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            self.add(root_box)

            toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
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
            self.combo_soal.append("auto", "Otomatis")
            for num, title in SOAL_TITLES.items():
                self.combo_soal.append(str(num), f"Soal {num} — {title}")
            self.combo_soal.set_active_id("auto")
            toolbar.pack_start(self.combo_soal, False, False, 0)

            toolbar.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 4)

            self.btn_latihan = Gtk.Button.new_with_label("Uji Latihan")
            self.btn_latihan.connect("clicked", lambda _: self.run_folder(LATIHAN_DIR))
            toolbar.pack_start(self.btn_latihan, False, False, 0)

            self.btn_kunci = Gtk.Button.new_with_label("Uji Kunci (Demo)")
            self.btn_kunci.connect("clicked", lambda _: self.run_folder(KUNCI_DIR))
            toolbar.pack_start(self.btn_kunci, False, False, 0)

            btn_modul = Gtk.Button.new_with_label("Buka Modul PDF")
            btn_modul.connect("clicked", lambda _: open_path_in_os(MODUL_DIR))
            toolbar.pack_start(btn_modul, False, False, 0)

            self.btn_rerun = Gtk.Button.new_with_label("Uji Ulang")
            self.btn_rerun.set_sensitive(False)
            self.btn_rerun.connect("clicked", self.on_rerun)
            toolbar.pack_end(self.btn_rerun, False, False, 0)

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

            paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
            paned.set_position(300)
            root_box.pack_start(paned, True, True, 0)

            self.store = Gtk.ListStore(str, str, str, str, str, str, str, int)
            self.tree = Gtk.TreeView(model=self.store)
            self.tree.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)

            col_defs = [
                ("File", 0, 170, None),
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

            self.tree.get_selection().connect("changed", self.on_row_selected)

            scroll_tree = Gtk.ScrolledWindow()
            scroll_tree.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scroll_tree.set_shadow_type(Gtk.ShadowType.IN)
            scroll_tree.add(self.tree)
            paned.pack1(scroll_tree, True, False)

            detail_grid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            detail_grid.set_margin_top(6)
            paned.pack2(detail_grid, True, False)

            self.buf_input = self._make_text_panel(detail_grid, "Input Uji")
            self.buf_actual = self._make_text_panel(detail_grid, "Output Siswa / Error")
            self.buf_expected = self._make_text_panel(detail_grid, "Kunci Jawaban")

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
            return int(active) if active and active != "auto" else None

        def _set_busy(self, busy: bool) -> None:
            self.is_running = busy
            for btn in (self.btn_file, self.btn_folder, self.btn_latihan, self.btn_kunci):
                btn.set_sensitive(not busy)
            self.btn_rerun.set_sensitive((not busy) and self.current_target is not None)
            if busy:
                self.progress.set_fraction(0.25)

        def on_pick_file(self, _w: Gtk.Widget) -> None:
            dlg = Gtk.FileChooserDialog(
                title="Pilih File Jawaban Python (.py)",
                parent=self,
                action=Gtk.FileChooserAction.OPEN,
            )
            dlg.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
            if LATIHAN_DIR.is_dir():
                dlg.set_current_folder(str(LATIHAN_DIR))
            flt = Gtk.FileFilter()
            flt.set_name("File Python (*.py)")
            flt.add_pattern("*.py")
            dlg.add_filter(flt)
            if dlg.run() == Gtk.ResponseType.OK:
                path = pathlib.Path(dlg.get_filename())
                dlg.destroy()
                self.run_single_file(path)
            else:
                dlg.destroy()

        def on_pick_folder(self, _w: Gtk.Widget) -> None:
            dlg = Gtk.FileChooserDialog(
                title="Pilih Folder Jawaban Tim",
                parent=self,
                action=Gtk.FileChooserAction.SELECT_FOLDER,
            )
            dlg.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
            if ROOT_DIR.is_dir():
                dlg.set_current_folder(str(ROOT_DIR))
            if dlg.run() == Gtk.ResponseType.OK:
                folder = pathlib.Path(dlg.get_filename())
                dlg.destroy()
                self.run_folder(folder)
            else:
                dlg.destroy()

        def on_rerun(self, _w: Gtk.Widget) -> None:
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
            self._start_worker([(path, self._selected_soal_override())], f"File: {path}")

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
                        results.append(grade_file(path, soal_num))
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
                        summary = (
                            "Output kosong — klik baris untuk melihat kunci"
                            if not c.actual
                            else "Output berbeda — klik baris untuk bandingkan"
                        )
                    else:
                        summary = c.error_message.splitlines()[-1] if c.error_message else "Terjadi error"

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
            res, case = self.row_details[model[tree_iter][7]]
            self.buf_input.set_text(case.input_data)
            self.buf_actual.set_text(format_actual_detail(res, case))
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

    win = PengujiGtkWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    if initial_arg is not None:
        if initial_arg.is_file():
            GLib.idle_add(win.run_single_file, initial_arg)
        elif initial_arg.is_dir():
            GLib.idle_add(win.run_folder, initial_arg)
    Gtk.main()


# ==============================================================================
# BACKEND 2: TKINTER / TTK (Windows 10/11 & Linux Fallback)
# ==============================================================================
def run_tk_gui(initial_arg: pathlib.Path | None = None) -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    class PengujiTkApp:
        def __init__(self, root: tk.Tk) -> None:
            self.root = root
            self.root.title("Penguji Lomba Coding Python — Penggalang")
            self.root.geometry("1040x680")
            self.root.minsize(820, 540)

            style = ttk.Style()
            for theme in ("vista", "clam", "default"):
                if theme in style.theme_names():
                    style.theme_use(theme)
                    break

            self.current_mode: str | None = None
            self.current_target: pathlib.Path | None = None
            self.row_details: dict[str, tuple[FileResult, CaseResult]] = {}
            self.is_running = False

            main = ttk.Frame(root, padding=10)
            main.pack(fill="both", expand=True)

            # Toolbar
            bar = ttk.Frame(main)
            bar.pack(fill="x", pady=(0, 8))

            self.btn_file = ttk.Button(bar, text="Pilih File (.py)", command=self.on_pick_file)
            self.btn_file.pack(side="left", padx=(0, 6))

            self.btn_folder = ttk.Button(bar, text="Pilih Folder Tim", command=self.on_pick_folder)
            self.btn_folder.pack(side="left", padx=(0, 8))

            ttk.Label(bar, text="Soal:").pack(side="left", padx=(0, 4))
            self.soal_var = tk.StringVar(value="Otomatis")
            soal_opts = ["Otomatis"] + [f"Soal {n} — {t}" for n, t in SOAL_TITLES.items()]
            self.combo_soal = ttk.Combobox(
                bar, textvariable=self.soal_var, values=soal_opts, state="readonly", width=32
            )
            self.combo_soal.pack(side="left", padx=(0, 10))

            self.btn_latihan = ttk.Button(
                bar, text="Uji Latihan", command=lambda: self.run_folder(LATIHAN_DIR)
            )
            self.btn_latihan.pack(side="left", padx=(0, 6))

            self.btn_kunci = ttk.Button(
                bar, text="Uji Kunci (Demo)", command=lambda: self.run_folder(KUNCI_DIR)
            )
            self.btn_kunci.pack(side="left", padx=(0, 6))

            ttk.Button(
                bar, text="Buka Modul PDF", command=lambda: open_path_in_os(MODUL_DIR)
            ).pack(side="left", padx=(0, 6))

            self.btn_rerun = ttk.Button(bar, text="Uji Ulang", command=self.on_rerun, state="disabled")
            self.btn_rerun.pack(side="right")

            # Kartu Skor
            card = ttk.Frame(main, relief="groove", padding=(12, 8))
            card.pack(fill="x", pady=(0, 8))

            left = ttk.Frame(card)
            left.pack(side="left", fill="x", expand=True)

            self.lbl_target = ttk.Label(
                left, text="Pilih file .py atau folder jawaban siswa untuk memulai pengujian."
            )
            self.lbl_target.pack(anchor="w")

            self.lbl_juknis = ttk.Label(
                left, text="Aturan Juknis: semua input() wajib kosong tanpa teks di dalam kurung."
            )
            self.lbl_juknis.pack(anchor="w", pady=(3, 0))

            self.lbl_score = tk.Label(card, text="—", font=("Segoe UI", 18, "bold"))
            self.lbl_score.pack(side="right", padx=(12, 4))

            self.progress = ttk.Progressbar(main, mode="determinate", maximum=100)
            self.progress.pack(fill="x", pady=(0, 8))

            # Paned window
            paned = ttk.Panedwindow(main, orient="vertical")
            paned.pack(fill="both", expand=True)

            # Tabel hasil
            tree_frame = ttk.Frame(paned)
            paned.add(tree_frame, weight=3)

            cols = ("file", "soal", "uji", "status", "waktu", "ringkasan")
            self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
            headers = [
                ("file", "File", 160),
                ("soal", "Soal", 220),
                ("uji", "Uji", 65),
                ("status", "Status", 95),
                ("waktu", "Waktu", 70),
                ("ringkasan", "Ringkasan", 290),
            ]
            for cid, text, w in headers:
                self.tree.heading(cid, text=text)
                self.tree.column(cid, width=w, anchor="w")

            self.tree.tag_configure("LULUS", foreground="#15803d")
            self.tree.tag_configure("SALAH", foreground="#b91c1c")
            self.tree.tag_configure("ERROR", foreground="#b91c1c")
            self.tree.tag_configure("TIMEOUT", foreground="#b45309")

            ysb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=ysb.set)
            self.tree.pack(side="left", fill="both", expand=True)
            ysb.pack(side="right", fill="y")
            self.tree.bind("<<TreeviewSelect>>", self.on_row_selected)

            # Detail 3 kolom
            detail_frame = ttk.Frame(paned, padding=(0, 6, 0, 0))
            paned.add(detail_frame, weight=2)
            for col_idx in range(3):
                detail_frame.columnconfigure(col_idx, weight=1)
            detail_frame.rowconfigure(1, weight=1)

            self.txt_input = self._make_text_box(detail_frame, "Input Uji", 0)
            self.txt_actual = self._make_text_box(detail_frame, "Output Siswa / Error", 1)
            self.txt_expected = self._make_text_box(detail_frame, "Kunci Jawaban", 2)

        def _make_text_box(self, parent: ttk.Frame, title: str, col: int) -> tk.Text:
            ttk.Label(parent, text=title, font=("Segoe UI", 9, "bold")).grid(
                row=0, column=col, sticky="w", padx=4, pady=(0, 3)
            )
            frame = ttk.Frame(parent)
            frame.grid(row=1, column=col, sticky="nsew", padx=4)
            txt = tk.Text(frame, wrap="word", font=("Consolas", 10), state="disabled", height=10)
            sb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            txt.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            return txt

        def _set_text(self, widget: tk.Text, value: str) -> None:
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", value)
            widget.configure(state="disabled")

        def _selected_soal_override(self) -> int | None:
            val = self.soal_var.get()
            if val.startswith("Soal "):
                return int(val.split()[1])
            return None

        def _set_busy(self, busy: bool) -> None:
            self.is_running = busy
            st = "disabled" if busy else "normal"
            for btn in (self.btn_file, self.btn_folder, self.btn_latihan, self.btn_kunci):
                btn.configure(state=st)
            self.btn_rerun.configure(
                state="normal" if (not busy and self.current_target is not None) else "disabled"
            )

        def on_pick_file(self) -> None:
            fname = filedialog.askopenfilename(
                title="Pilih File Jawaban Python (.py)",
                initialdir=str(LATIHAN_DIR if LATIHAN_DIR.is_dir() else ROOT_DIR),
                filetypes=[("File Python", "*.py"), ("Semua File", "*.*")],
            )
            if fname:
                self.run_single_file(pathlib.Path(fname))

        def on_pick_folder(self) -> None:
            dname = filedialog.askdirectory(
                title="Pilih Folder Jawaban Tim",
                initialdir=str(ROOT_DIR),
            )
            if dname:
                self.run_folder(pathlib.Path(dname))

        def on_rerun(self) -> None:
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
            self._start_worker([(path, self._selected_soal_override())], f"File: {path}")

        def run_folder(self, folder: pathlib.Path) -> None:
            if self.is_running:
                return
            self.current_mode = "folder"
            self.current_target = folder
            files = find_soal_files(folder)
            if not files:
                messagebox.showerror(
                    "Pengujian Tidak Dapat Dijalankan",
                    f"Tidak ditemukan file soal1..soal4 (*.py) di:\n{folder}",
                )
                return
            self._start_worker([(f, None) for f in files], f"Folder: {folder}")

        def _start_worker(self, items: list[tuple[pathlib.Path, int | None]], label: str) -> None:
            self._set_busy(True)
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.row_details.clear()
            self._set_text(self.txt_input, "")
            self._set_text(self.txt_actual, "")
            self._set_text(self.txt_expected, "")
            self.lbl_target.configure(text=f"Sedang menguji {label} ...")
            self.progress["value"] = 10

            def worker() -> None:
                results: list[FileResult] = []
                error_msg: str | None = None
                try:
                    for idx, (path, soal_num) in enumerate(items, start=1):
                        results.append(grade_file(path, soal_num))
                        pct = int((idx / len(items)) * 100)
                        self.root.after(0, lambda p=pct: self.progress.configure(value=p))
                except Exception as exc:
                    error_msg = str(exc)
                self.root.after(0, lambda: self._finish_worker(results, label, error_msg))

            threading.Thread(target=worker, daemon=True).start()

        def _finish_worker(
            self, results: list[FileResult], label: str, error_msg: str | None
        ) -> None:
            self._set_busy(False)
            if error_msg:
                self.progress["value"] = 0
                messagebox.showerror("Pengujian Tidak Dapat Dijalankan", error_msg)
                return

            self.progress["value"] = 100
            self.lbl_target.configure(text=label)

            bad_files = [
                f"{r.path.name} (baris {', '.join(map(str, r.bad_input_lines))})"
                for r in results
                if r.bad_input_lines
            ]
            if bad_files:
                self.lbl_juknis.configure(
                    text="PERINGATAN JUKNIS — input() berisi teks pada: " + "; ".join(bad_files),
                    foreground="#c2410c",
                )
            else:
                self.lbl_juknis.configure(
                    text="Aturan Juknis aman: semua input() kosong tanpa teks prompt.",
                    foreground="#15803d",
                )

            total_score = sum(r.score for r in results)
            max_score = min(len(results) * 25, 100)
            color = (
                "#15803d"
                if (total_score == max_score and not bad_files)
                else ("#b45309" if total_score > 0 else "#b91c1c")
            )
            self.lbl_score.configure(text=f"{total_score} / {max_score}", fg=color)

            labels = {
                "LULUS": "LULUS",
                "SALAH": "SALAH",
                "ERROR": "ERROR",
                "TIMEOUT": "TIMEOUT",
            }
            first_fail_iid: str | None = None
            first_iid: str | None = None
            for r in results:
                for c in r.cases:
                    if c.status == "LULUS":
                        summary = f"Cocok persis (Skor soal: {r.score}/25)"
                    elif c.status == "SALAH":
                        summary = (
                            "Output kosong — klik baris untuk melihat kunci"
                            if not c.actual
                            else "Output berbeda — klik baris untuk bandingkan"
                        )
                    else:
                        summary = c.error_message.splitlines()[-1] if c.error_message else "Terjadi error"

                    iid = self.tree.insert(
                        "",
                        "end",
                        values=(
                            r.path.name,
                            f"Soal {r.soal_num}: {r.soal_title}",
                            f"Uji #{c.index}",
                            labels.get(c.status, c.status),
                            f"{c.elapsed_ms} ms",
                            summary,
                        ),
                        tags=(c.status,),
                    )
                    self.row_details[iid] = (r, c)
                    if first_iid is None:
                        first_iid = iid
                    if first_fail_iid is None and c.status != "LULUS":
                        first_fail_iid = iid

            pick = first_fail_iid or first_iid
            if pick:
                self.tree.selection_set(pick)
                self.tree.focus(pick)

        def on_row_selected(self, _event: object) -> None:
            sel = self.tree.selection()
            if not sel:
                return
            res, case = self.row_details[sel[0]]
            self._set_text(self.txt_input, case.input_data)
            self._set_text(self.txt_actual, format_actual_detail(res, case))
            self._set_text(self.txt_expected, case.expected)

    root = tk.Tk()
    app = PengujiTkApp(root)
    if initial_arg is not None:
        if initial_arg.is_file():
            root.after(150, lambda: app.run_single_file(initial_arg))
        elif initial_arg.is_dir():
            root.after(150, lambda: app.run_folder(initial_arg))
    root.mainloop()


def main() -> None:
    initial_arg = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    if not sys.platform.startswith("win"):
        try:
            import gi  # noqa: F401

            run_gtk_gui(initial_arg)
            return
        except Exception:
            pass
    try:
        run_tk_gui(initial_arg)
    except Exception as exc:
        print(
            "[ERROR] GUI membutuhkan GTK 3 (python3-gi di Linux) atau Tkinter (bawaan Python Windows).\n"
            f"Detail: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
