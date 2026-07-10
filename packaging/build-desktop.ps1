# Phase 6 — assemble and build the Multimedia Downloader V4.0 desktop package.
#
# Run from Version4.0/:  npm run package     (or: powershell -File packaging/build-desktop.ps1)
#
# Steps:
#   1. Build the Python engine as a standalone sidecar (PyInstaller onedir).
#   2. Stage ffmpeg.exe next to the sidecar exe (Tauri bundles the folder as a resource;
#      the sidecar auto-resolves this ffmpeg when frozen — see engine_sidecar.resolve_ffmpeg).
#   3. `tauri build` — compiles the Rust shell, builds the frontend, produces installers.
#   4. Copy the installers to the project's Packaged/ folder.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot          # …/Version4.0
$ffmpegSrc = "D:\Code\Multimedia_Downloader\ffmpeg\ffmpeg.exe"
$packagedOut = "D:\Code\Multimedia_Downloader\Packaged\Version4.0_Packaged"

Set-Location $root

Write-Host "==> [1/4] Building Python engine sidecar (PyInstaller)…" -ForegroundColor Cyan
python -m PyInstaller packaging/engine_sidecar.spec --noconfirm `
    --distpath packaging/dist --workpath packaging/build
if (-not (Test-Path "packaging/dist/engine_sidecar/engine_sidecar.exe")) {
    throw "sidecar build failed — engine_sidecar.exe not found"
}

Write-Host "==> [2/4] Staging ffmpeg.exe alongside the sidecar…" -ForegroundColor Cyan
if (-not (Test-Path $ffmpegSrc)) {
    throw "ffmpeg.exe not found at $ffmpegSrc — place a Windows ffmpeg build there first"
}
Copy-Item $ffmpegSrc "packaging/dist/engine_sidecar/ffmpeg.exe" -Force

Write-Host "==> [3/4] tauri build (frontend + Rust shell + installers)…" -ForegroundColor Cyan
npm run tauri build

Write-Host "==> [4/4] Copying installers to $packagedOut…" -ForegroundColor Cyan
New-Item -ItemType Directory -Force $packagedOut | Out-Null
# Clear stale installers so the folder always reflects the current build only.
Get-ChildItem $packagedOut -Include *.exe, *.msi -File -ErrorAction SilentlyContinue | Remove-Item -Force
$bundleDir = "src-tauri/target/release/bundle"
if (Test-Path $bundleDir) {
    $installers = Get-ChildItem $bundleDir -Recurse -Include *.exe, *.msi
    if ($installers) {
        $installers | ForEach-Object { Copy-Item $_.FullName $packagedOut -Force; Write-Host "   copied $($_.Name)" }
        Write-Host "Done. Installers in $packagedOut" -ForegroundColor Green
    } else {
        Write-Warning "no .exe/.msi found under $bundleDir — check the tauri build output above"
    }
} else {
    Write-Warning "bundle dir not found ($bundleDir) — check the tauri build output above"
}
