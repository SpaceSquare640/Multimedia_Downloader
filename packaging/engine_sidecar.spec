# PyInstaller spec — build the Python engine as a standalone sidecar.
#
# onedir (not onefile): the Tauri shell spawns a NEW sidecar process per
# operation, so onefile's unpack-to-temp on every spawn would be slow. onedir
# starts fast and is bundled into the app via Tauri `bundle.resources`.
#
# Build (from Version4.0/):  pyinstaller packaging/engine_sidecar.spec --noconfirm
# Output:                    packaging/dist/engine_sidecar/engine_sidecar.exe

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []

# yt-dlp lazily imports hundreds of site extractors — pull them all in so the
# frozen build can download from any supported platform.
_d, _b, _h = collect_all("yt_dlp")
datas += _d
binaries += _b
hiddenimports += _h

# i18n JSON locale files, loaded at runtime by i18n/__init__.py (which is
# frozen-aware and looks for a bundled `locales/` dir).
datas += [("../locales", "locales")]

a = Analysis(
    ["../engine_sidecar.py"],
    pathex=[".."],            # so local packages (engine, ai, i18n) resolve
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest"],  # not needed by the sidecar
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="engine_sidecar",
    console=True,             # stdio protocol — must keep a console/std streams
    disable_windowed_traceback=False,
    strip=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="engine_sidecar",
)
