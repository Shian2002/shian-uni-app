# 时安解忧屋桌面端

本目录是 macOS、Windows 第一版 Electron 桌面壳。业务代码仍然来自主仓 uni-app H5 构建产物，不复制账号、积分、AI、排盘或支付逻辑。

## 本地安装

```bash
npm run desktop:install
```

## 开发预览

```bash
npm run desktop:dev
```

脚本会先执行 `npm run build:h5`，再用 Electron 加载 `dist/build/h5/index.html`。如果本地构建产物不存在，会回退到 `SHIAN_DESKTOP_URL`，默认 `http://localhost:5173`。

## 打安装包

```bash
npm run desktop:build
```

产物输出到 `desktop/release/`，可上传 GitHub Releases。签名证书、notarization 密钥、Windows 证书不得提交到 Git。

## macOS DMG 校验

```bash
npm run desktop:verify-macos
```

脚本会在 macOS 上只读挂载 `desktop/release/时安解忧屋-1.0.0-arm64.dmg`，检查包内 `.app`、`Info.plist`、主可执行文件和 `icon.icns` 是否存在。它不签名、不公证、不上传 Release；正式公开下载前仍要补 Apple Developer ID 签名、notarization 和用户首次打开截图。

## 图标

桌面端图标来自主项目 logo：`src/static/images/logo.png`。打包前需要保留以下非敏感资源：

- `desktop/assets/icon.png`：运行时窗口图标。
- `desktop/assets/icon.icns`：macOS `.app` / DMG 图标。
- `desktop/assets/icon.ico`：Windows NSIS 安装包图标。

这些文件只保存公开 logo，不包含证书、密钥或签名材料。

## 第一版范围

- macOS 输出 DMG。
- Windows 输出 NSIS 安装包。
- 暂不接入自动更新。
- 暂不上 Mac App Store 或 Microsoft Store。
