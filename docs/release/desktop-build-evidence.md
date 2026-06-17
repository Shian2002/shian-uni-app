# 桌面端构建证据

> 更新时间：2026-06-17  
> 范围：macOS/Windows 第一版先走官网或 GitHub Releases 下载，不作为 Mac App Store / Microsoft Store 正式商店包。

## 2026-06-15 macOS arm64 测试包

- 平台：macOS arm64
- 产物：`desktop/release/时安解忧屋-1.0.0-arm64.app.zip`
- DMG：`desktop/release/时安解忧屋-1.0.0-arm64.dmg`
- release inbox：`artifacts/release-inbox/v1.0.0/macos/shian-v1.0.0-macos-arm64.dmg`
- 大小：117,246,240 bytes
- SHA-256：`41139db26d5ff5fd92f0269fce5c8a77cb795eaae7b239c80f84d95cd2f45a23`
- DMG SHA-256：`b9475eeef1a98bdaf918c4517d53fecba9f97fd2ccae5fed5c64a43f7df40dc8`
- manifest：`artifacts/release-manifests/2026-06-15T10-47-52-088-current-worktree.json`
- 打包后 smoke：`artifacts/desktop-smoke/2026-06-15T02-33-13-363Z/report.json`
- 桌面下载交付包：`artifacts/desktop-downloads/2026-06-15T10-55-05-183-v1.0.0/README.md`
- 截图：
  - `artifacts/desktop-smoke/2026-06-15T02-33-13-363Z/desktop-marketing-home.png`
  - `artifacts/desktop-smoke/2026-06-15T02-33-13-363Z/desktop-login-modal.png`
  - `artifacts/desktop-smoke/2026-06-15T02-33-13-363Z/desktop-agent-app.png`
- 构建命令：

```bash
ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/ npm --prefix desktop install --cache .npm-cache
ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/ npm run desktop:pack
ditto -c -k --sequesterRsrc --keepParent "desktop/release/mac-arm64/时安解忧屋.app" "desktop/release/时安解忧屋-1.0.0-arm64.app.zip"
npm run desktop:build:mac:arm64
npm run release:manifest
DESKTOP_SMOKE_EXECUTABLE="<repo>/desktop/release/mac-arm64/时安解忧屋.app/Contents/MacOS/时安解忧屋" npm run desktop:smoke
```

## 2026-06-15 Windows x64 NSIS 测试包

- 平台：Windows x64
- 产物：`desktop/release/时安解忧屋 Setup 1.0.0.exe`
- release inbox：`artifacts/release-inbox/v1.0.0/windows/shian-v1.0.0-windows-x64-nsis.exe`
- 大小：100,937,242 bytes
- SHA-256：`ffe71b3f57d1e03e721f7f8bc868da81c0ac60b205fe89369a7376f60f9254b8`
- 签名状态：未配置 Windows 代码签名证书。
- 构建命令：

```bash
npm run desktop:build:win:x64
```

本机同时验证：

- `desktop/release/win-unpacked/时安解忧屋.exe` 为 `PE32+ executable (GUI) x86-64, for MS Windows`。
- NSIS 安装器为 `desktop/release/时安解忧屋 Setup 1.0.0.exe`。
- 安装器已复制到 release inbox，后续由 `npm run release:intake` 生成收件报告。
- 本次重打包已使用 `desktop/assets/icon.ico`，与 macOS 同源于主项目 logo。

注意：这只证明当时 Windows x64 安装器曾构建成功，不证明已在 Windows 10/11 真机安装、卸载、登录和窗口缩放验收通过。

## 2026-06-17 Windows x64 最新状态

- 已清理旧桌面交付副本释放磁盘空间，并使用无签名/无发布环境重新执行 Windows x64 NSIS 打包。
- GitHub Electron release 直连在本机超时；本次成功构建使用国内 Electron 镜像：`ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/ DESKTOP_WINDOWS_REBUILD_SKIP_H5=1 DESKTOP_WINDOWS_REBUILD_TIMEOUT_MS=600000 npm run desktop:build:win:x64:safe`。
- 后续 Windows x64 标准重建入口：`npm run desktop:build:win:x64:safe`；若 GitHub 下载再次卡住，优先带上 `ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/`；只校验当前安装器时使用 `DESKTOP_WINDOWS_REBUILD_VERIFY_CURRENT=1 npm run desktop:build:win:x64:safe`，或等价执行 `npm run desktop:build:win:x64:safe -- --verify-current`。
- 最新安装器：`desktop/release/时安解忧屋 Setup 1.0.0.exe`
- 最新 SHA-256：`5bda487d68965132e54c6eafa39b4b8387ff939417a3fd41c9f30a74601fe98c`
- 最新重建报告：`artifacts/desktop-windows-rebuild/2026-06-17T00-36-43-805-v1.0.0/report.json`
- 最新 Windows 个人试用包：`artifacts/desktop-windows-user-packets/2026-06-17T00-43-04-716-v1.0.0/`
- 最新桌面下载包：`artifacts/desktop-downloads/2026-06-17T00-43-12-839-v1.0.0/`
- 最新 try-now：`artifacts/try-now/2026-06-17T00-43-29-882-v1.0.0/`
- 当前固定下载入口：`artifacts/current-downloads/shian-current-windows-x64.exe`，SHA-256 `5bda487d68965132e54c6eafa39b4b8387ff939417a3fd41c9f30a74601fe98c`。
- `npm run desktop:windows-user-packet` 和 `npm run desktop:bundle` 已加入新鲜度检查：如果 Windows 安装器早于最新 `dist/build/h5/index.html`，会标记为未通过。
- 当前最新检查结论：Windows x64 NSIS 测试包已重新生成并通过新鲜度检查，可进入 Windows 10/11 真机安装、登录、窗口缩放和卸载回收。

## 当前结论

- Electron 壳通过本地 `127.0.0.1` 静态服务加载当前 H5 构建产物，已生成 macOS `.app` 并压缩为 GitHub Releases 可上传 zip。
- 桌面端业务逻辑不复制登录实现；当前登录仍复用线上 H5/后端现有登录逻辑，桌面壳只负责加载构建产物。
- 桌面端图标已改用主项目 logo：`src/static/images/logo.png` 生成 `desktop/assets/icon.png`、`desktop/assets/icon.icns`、`desktop/assets/icon.ico`，macOS/Windows 打包配置均指向这些图标资产。
- 已生成 macOS arm64 DMG，并复制到 release inbox，可作为 GitHub Releases 内测下载包候选。
- Windows x64 NSIS 测试安装器已重新生成并通过新鲜度检查，可作为 GitHub Releases 内测安装包候选；正式公开前仍需 Windows 代码签名和 Windows 10/11 真机安装/卸载验收。
- 已新增 `npm run desktop:bundle`，可把当前 macOS/Windows 桌面包整理为 URL 友好的下载文件名，并生成 `checksums.sha256` 和 `manifest.json`。
- 已新增 `npm run desktop:verify-macos`，可在 macOS 上只读挂载 DMG，检查包内 `.app`、`Info.plist`、主可执行文件和 `icon.icns`，报告输出到 `artifacts/desktop-macos-install/*/report.json`。
- 已新增 `npm run desktop:macos-user-packet`，可生成当前优先给本人试用的 macOS 交付包，集中包含 DMG、备用 `.app.zip`、截图、checksum、manifest 和打开说明，输出到 `artifacts/desktop-macos-user-packets/*/`。
- 已新增 `npm run desktop:windows-user-packet`，可生成 Windows 内部试用包，集中包含 NSIS 安装器、页面预览、截图、checksum、manifest 和 Windows 10/11 真机安装/卸载回收清单，输出到 `artifacts/desktop-windows-user-packets/*/`。
- 最新桌面下载交付包：`artifacts/desktop-downloads/2026-06-17T00-43-12-839-v1.0.0/`，包含当前 macOS DMG、macOS app zip 和重新生成的 Windows x64 NSIS。
- 已直接打开打包后的 `.app` 做 smoke：营销首页、旧登录弹窗、时安 agent 应用态三张截图通过。
- 桌面端发布状态统一执行 `npm run desktop:release-status`，报告输出到 `artifacts/desktop-release-status/*/report.json`；当前必须保持未通过，直到签名、公证和真机安装/卸载截图补齐。
- 当前机器没有有效 Apple Developer ID 证书，electron-builder 跳过了 macOS 代码签名；本次产物状态为未签名测试包。
- 该 zip/DMG 适合作为内部测试、GitHub Releases 测试版或官网临时下载包，不适合作为正式商店签名包。

## 仍需补齐

- 使用有效 Apple Developer ID 重新签名并 notarize。
- 记录 DMG 安装、首次打开、安全提示、窗口缩放截图。
- 在 Windows 10/11 环境安装 `shian-v1.0.0-windows-x64-nsis.exe`，记录安装、卸载、开始菜单、窗口缩放、登录弹窗和时安 agent 截图。
- 对桌面端运行真实登录、积分会员页、退出重开三条真实用户流程。
- DMG、ZIP、EXE、MSI 生成后统一放入 `artifacts/release-inbox/v1.0.0/macos/` 或 `artifacts/release-inbox/v1.0.0/windows/`，执行 `npm run release:intake` 生成 SHA-256 后再进入 GitHub Release 草稿包。
