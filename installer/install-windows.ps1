# ==============================================================================
# Installer 1-Klik Koding Penggalang untuk Windows 10 / 11
# Memasang: Python 3, Sublime Text 4 + Helper Python & Ruff,
#           Modul PDF, Paket 4 Soal, Kunci Jawaban, CLI (cek) & GUI (cekgui).
# ==============================================================================
param(
    [switch]$NoSublime,
    [string]$InstallDir = "$env:USERPROFILE\koding-penggalang"
)

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path (Join-Path $ScriptDir "payload")) {
    $SrcRoot = Join-Path $ScriptDir "payload"
} elseif (Test-Path (Join-Path $ScriptDir "cek_jawaban.py")) {
    $SrcRoot = $ScriptDir
} else {
    $SrcRoot = Split-Path -Parent $ScriptDir
}

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }

Write-Host "================================================================" -ForegroundColor White
Write-Host "  INSTALLER KODING PENGGALANG (WINDOWS) — PYTHON 3 + SUBLIME" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor White
Write-Host "  Folder tujuan : $InstallDir"
Write-Host "  Sublime Text  : $(if ($NoSublime) { 'Lewati (-NoSublime)' } else { 'Ya (beserta Python Helper & Ruff)' })"
Write-Host "================================================================" -ForegroundColor White
Write-Host ""

$HasWinget = [bool](Get-Command winget -ErrorAction SilentlyContinue)

# 1. Periksa / pasang Python 3
Write-Info "Memeriksa Python 3..."
$PyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PyCmd -or ($PyCmd.Source -like "*WindowsApps*")) {
    if ($HasWinget) {
        Write-Info "Memasang Python 3.12 melalui winget (resmi)..."
        winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    } else {
        Write-Warn "winget tidak tersedia. Silakan unduh Python 3 resmi di https://www.python.org/downloads/ (centang 'Add python.exe to PATH')."
    }
}
$PyExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($PyExe) {
    Write-Ok "Python 3 siap: $(& $PyExe --version 2>&1)"
} else {
    Write-Warn "Python belum terdeteksi di PATH. Jika baru dipasang, tutup dan buka kembali terminal setelah instalasi selesai."
}

# 2. Periksa / pasang Sublime Text 4
if (-not $NoSublime) {
    Write-Info "Memeriksa Sublime Text 4..."
    $SublPaths = @(
        "$env:ProgramFiles\Sublime Text\sublime_text.exe",
        "$env:ProgramFiles\Sublime Text 3\sublime_text.exe"
    )
    $HasSubl = ($SublPaths | Where-Object { Test-Path $_ }).Count -gt 0 -or [bool](Get-Command subl -ErrorAction SilentlyContinue)
    if ($HasSubl) {
        Write-Ok "Sublime Text sudah terpasang."
    } elseif ($HasWinget) {
        Write-Info "Memasang Sublime Text 4 melalui winget (resmi)..."
        winget install --id SublimeHQ.SublimeText.4 -e --source winget --accept-package-agreements --accept-source-agreements
        Write-Ok "Sublime Text 4 selesai dipasang."
    } else {
        Write-Warn "Sublime Text belum terpasang dan winget tidak tersedia. Unduh di https://www.sublimetext.com/download"
    }

    # Pasang Ruff
    if ($PyExe) {
        Write-Info "Memasang Ruff (pemeriksa & perapi kode Python offline)..."
        & $PyExe -m pip install --user --quiet ruff
        Write-Ok "Ruff siap digunakan."
    }
}

# 3. Salin seluruh paket Koding Penggalang
Write-Info "Menyalin Modul PDF, Latihan 4 Soal, Kunci Jawaban, CLI & GUI ke $InstallDir..."
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$Items = @("modul", "latihan", "kunci_jawaban", "penguji", "cek_jawaban.py", "cek_jawaban_gui.py", "README.md")
foreach ($item in $Items) {
    $src = Join-Path $SrcRoot $item
    $dst = Join-Path $InstallDir $item
    if (Test-Path $src) {
        if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
        Copy-Item -Recurse -Force $src $dst
    }
}
Write-Ok "Paket Koding Penggalang terpasang di $InstallDir"

# 4. Pasang Helper Sublime Text untuk Windows
$BundleDir = Join-Path $SrcRoot "installer\sublime_bundle\User"
if ((-not $NoSublime) -and (Test-Path $BundleDir)) {
    Write-Info "Memasang konfigurasi Sublime Text Python Helper (F5/F6, Ctrl+., Shift+Alt+F)..."
    $SublUser = Join-Path $env:APPDATA "Sublime Text\Packages\User"
    New-Item -ItemType Directory -Force -Path $SublUser | Out-Null

    $CopyFiles = @(
        "Adaptive.sublime-theme",
        "GitHub Dark Colorblind.sublime-color-scheme",
        "GitHub Dark.sublime-color-scheme",
        "Preferences.sublime-settings",
        "Python.sublime-settings",
        "python_ruff_helper.py",
        "PythonSnippets"
    )
    foreach ($f in $CopyFiles) {
        $s = Join-Path $BundleDir $f
        if (Test-Path $s) { Copy-Item -Recurse -Force $s (Join-Path $SublUser $f) }
    }
    Copy-Item -Force (Join-Path $BundleDir "Default (Linux).sublime-keymap") (Join-Path $SublUser "Default (Windows).sublime-keymap")
    Copy-Item -Force (Join-Path $BundleDir "Python3-Windows.sublime-build") (Join-Path $SublUser "Python3.sublime-build")
    Write-Ok "Helper Sublime Text terpasang di $SublUser"
}

# 5. Buat perintah global cek.cmd, cekall.cmd, cekgui.cmd dan tambahkan ke PATH User
$BinDir = Join-Path $env:LOCALAPPDATA "KodingPenggalang\bin"
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

Set-Content -Path (Join-Path $BinDir "cek.cmd") -Encoding ASCII -Value "@echo off`r`npython `"$InstallDir\cek_jawaban.py`" %*`r`n"
Set-Content -Path (Join-Path $BinDir "cekall.cmd") -Encoding ASCII -Value "@echo off`r`npython `"$InstallDir\cek_jawaban.py`" all %*`r`n"
Set-Content -Path (Join-Path $BinDir "cekgui.cmd") -Encoding ASCII -Value "@echo off`r`nstart `"`" pythonw `"$InstallDir\cek_jawaban_gui.py`" %*`r`n"

$UserPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if (-not $UserPath) { $UserPath = "" }
if ($UserPath -notlike "*$BinDir*") {
    $NewPath = if ($UserPath.EndsWith(";") -or $UserPath -eq "") { "$UserPath$BinDir" } else { "$UserPath;$BinDir" }
    [System.Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
}
Write-Ok "Perintah terminal 'cek', 'cekall', dan 'cekgui' ditambahkan ke PATH."

# 6. Buat Pintasan Desktop (.lnk)
try {
    $Desktop = [Environment]::GetFolderPath("Desktop")
    $Wsh = New-Object -ComObject WScript.Shell

    $ScGui = $Wsh.CreateShortcut((Join-Path $Desktop "Penguji Koding Penggalang.lnk"))
    $ScGui.TargetPath = "pythonw.exe"
    $ScGui.Arguments = "`"$InstallDir\cek_jawaban_gui.py`""
    $ScGui.WorkingDirectory = $InstallDir
    $ScGui.Description = "Aplikasi Penguji Jawaban Lomba Coding Python Penggalang"
    $ScGui.Save()

    $ScMod = $Wsh.CreateShortcut((Join-Path $Desktop "Modul PDF & Soal Koding Penggalang.lnk"))
    $ScMod.TargetPath = (Join-Path $InstallDir "modul")
    $ScMod.Description = "Buka folder Modul Belajar, Referensi Cepat, dan Paket 4 Soal PDF"
    $ScMod.Save()

    Write-Ok "Pintasan Desktop berhasil dibuat."
} catch {
    Write-Warn "Gagal membuat pintasan Desktop: $_"
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor White
Write-Host "  INSTALASI SELESAI 100%!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor White
Write-Host "  Folder Modul PDF : $InstallDir\modul\"
Write-Host "  Folder Latihan   : $InstallDir\latihan\"
Write-Host "  Kunci Jawaban    : $InstallDir\kunci_jawaban\"
Write-Host "  Buka GUI Penguji : klik ikon 'Penguji Koding Penggalang' di Desktop"
Write-Host "  Cek via CMD/PS   : cek 1  |  cekall  |  cekgui"
Write-Host "================================================================" -ForegroundColor White
