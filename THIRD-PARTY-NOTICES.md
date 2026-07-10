# Third-Party Notices

**Language / 語言 / 语言:** [English](#english) · [繁體中文](#繁體中文) · [简体中文](#简体中文)

This project (`SpaceSquare640/Multimedia_Downloader`) is licensed under the
MIT License (see `LICENSE`). It bundles or depends on the third-party
components listed below, each under its **own** license — those components
are **not** covered by this project's MIT license.

---

## English

### ffmpeg — GNU General Public License v3.0 (GPLv3)

V4.0's packaged desktop installers bundle a Windows build of
[ffmpeg](https://ffmpeg.org) so users don't need to install it separately.

- **Build**: `ffmpeg-8.0.1-full_build` by [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
- **Build configuration** includes `--enable-gpl --enable-version3
  --enable-libx264 --enable-libx265` (and other GPL-licensed components),
  which makes this specific build **GPLv3-licensed** (not LGPL).
- **License text**: the full GPLv3 text is included at
  [`third-party/LICENSE-ffmpeg-GPLv3.txt`](third-party/LICENSE-ffmpeg-GPLv3.txt)
  in this repository.
- **Source code availability**: FFmpeg's complete source code is publicly
  available at <https://ffmpeg.org/download.html> (official source) and the
  exact Windows build scripts/configuration used for the bundled binary are
  published by gyan.dev at <https://github.com/GyanD/codexffmpeg>. This
  written notice constitutes our offer to provide the corresponding source
  for the exact bundled build on request, per GPLv3 §6.
- ffmpeg is invoked by this project as a **separate subprocess** (never
  statically or dynamically linked into our own binaries) — this project's
  own source code is licensed independently under MIT and is not itself
  subject to the GPL.

### yt-dlp — The Unlicense (public domain equivalent)

The download engine uses [yt-dlp](https://github.com/yt-dlp/yt-dlp),
released under [The Unlicense](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE) —
public domain equivalent, no attribution legally required, credited here
regardless.

### Other dependencies

The frontend (Svelte, Vite, Tailwind CSS, lucide-svelte) and desktop shell
(Tauri, and their Rust/npm dependency trees) are each distributed under
permissive open-source licenses (MIT/Apache-2.0/ISC) by their respective
authors. See each package's own repository for full license text.

---

## 繁體中文

### ffmpeg — GNU 通用公共授權 v3.0（GPLv3）

V4.0 的桌面安裝檔內建了 Windows 版 [ffmpeg](https://ffmpeg.org)，讓使用者
免另外安裝。

- **建置版本**：[gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 的
  `ffmpeg-8.0.1-full_build`
- **建置設定**包含 `--enable-gpl --enable-version3 --enable-libx264
  --enable-libx265`（及其他 GPL 授權元件），使這個特定版本為
  **GPLv3 授權**（非 LGPL）。
- **授權全文**：GPLv3 完整條文附於本 repo
  [`third-party/LICENSE-ffmpeg-GPLv3.txt`](third-party/LICENSE-ffmpeg-GPLv3.txt)。
- **原始碼取得方式**：FFmpeg 完整原始碼公開於
  <https://ffmpeg.org/download.html>（官方原始碼），本次 bundled 版本所用
  的 Windows 建置腳本/設定由 gyan.dev 公開於
  <https://github.com/GyanD/codexffmpeg>。此聲明即為依 GPLv3 第 6 條，就
  本次 bundled 建置版本提供對應原始碼的書面承諾。
- ffmpeg 在本專案中以**獨立子行程**呼叫（從未靜態或動態連結進我方執行
  檔）——本專案自身的原始碼獨立以 MIT 授權，不受 GPL 拘束。

### yt-dlp — The Unlicense（等同公共領域）

下載引擎使用 [yt-dlp](https://github.com/yt-dlp/yt-dlp)，以
[The Unlicense](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE) 釋出
——等同公共領域，法律上不強制需要標註出處，此處仍列出以示感謝。

### 其他相依套件

前端（Svelte、Vite、Tailwind CSS、lucide-svelte）與桌面殼（Tauri，及其
Rust/npm 相依樹）皆由各自作者以寬鬆的開源授權（MIT/Apache-2.0/ISC）釋出。
詳細授權條文請參閱各套件自己的 repository。

---

## 简体中文

### ffmpeg — GNU 通用公共许可证 v3.0（GPLv3）

V4.0 的桌面安装包内置了 Windows 版 [ffmpeg](https://ffmpeg.org)，使用户
免另外安装。

- **构建版本**：[gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 的
  `ffmpeg-8.0.1-full_build`
- **构建配置**包含 `--enable-gpl --enable-version3 --enable-libx264
  --enable-libx265`（及其他 GPL 授权组件），使这个特定版本为
  **GPLv3 授权**（非 LGPL）。
- **授权全文**：GPLv3 完整条文附于本 repo
  [`third-party/LICENSE-ffmpeg-GPLv3.txt`](third-party/LICENSE-ffmpeg-GPLv3.txt)。
- **源代码获取方式**：FFmpeg 完整源代码公开于
  <https://ffmpeg.org/download.html>（官方源代码），本次内置版本所用的
  Windows 构建脚本/配置由 gyan.dev 公开于
  <https://github.com/GyanD/codexffmpeg>。此声明即为依 GPLv3 第 6 条，就
  本次内置构建版本提供对应源代码的书面承诺。
- ffmpeg 在本项目中以**独立子进程**调用（从未静态或动态链接进我方可执行
  文件）——本项目自身的源代码独立以 MIT 授权，不受 GPL 约束。

### yt-dlp — The Unlicense（等同公共领域）

下载引擎使用 [yt-dlp](https://github.com/yt-dlp/yt-dlp)，以
[The Unlicense](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE) 发布
——等同公共领域，法律上不强制要求署名，此处仍列出以示感谢。

### 其他依赖

前端（Svelte、Vite、Tailwind CSS、lucide-svelte）与桌面壳（Tauri，及其
Rust/npm 依赖树）均由各自作者以宽松的开源许可证（MIT/Apache-2.0/ISC）发
布。详细许可证条文请参阅各软件包自己的仓库。
