# 平台打包交接说明

> 更新时间：2026-06-15  
> 目标：把 Android、iOS、鸿蒙、macOS、Windows 的外部打包动作变成可交接、可回填、可归档的材料包。当前批次只推进 Android、macOS、Windows；iOS 和鸿蒙保留交接模板，后续恢复。

## 生成命令

```bash
npm run platform:handoff
npm run mobile:build-requests
```

输出目录：

```text
artifacts/platform-build-handoffs/<timestamp>-v1.0.0/
```

每次生成会包含：

- `README.md`：本次交接包总览。
- `manifest.json`：commit、当前构建产物、截图候选、登录 smoke、Agent 入口验收和 Release 包引用。
- `android.md`：应用宝、华为、小米、OPPO、vivo、Google Play 的 APK/AAB 打包交接。
- `ios.md`：TestFlight/App Store 的构建、App Privacy、IAP 边界和截图交接。
- `harmony.md`：华为 AppGallery / 鸿蒙测试包交接。
- `macos.md`：macOS ZIP/DMG、签名、notarization 和 smoke 交接。
- `windows.md`：Windows EXE/MSI、安装/卸载和 Windows 10/11 测试交接。
- `mobile:build-requests` 会额外生成 `artifacts/mobile-build-requests/<timestamp>-v1.0.0/`，把 Android、iOS、鸿蒙的构建请求拆成可发给打包人的 `android.md`、`ios.md`、`harmony.md` 和 JSON。

## 交接边界

- 交接包只保存非敏感配置、构建命令、hash、截图清单和回填要求。
- keystore、jks、p12、mobileprovision、Developer ID、Windows 签名证书和商店后台账号密码都不得进入 GitHub。
- 当前批次 Android 和 Windows 的实际安装包需要对应平台环境生成；本地 H5 自动截图只能作为拍摄参考，不能替代真机截图。iOS 和鸿蒙实际包后续批次再生成。
- 移动端请求包会把线上登录 smoke、时安 agent 入口验收、法律 URL、隐私披露和商店材料检查引用进去；缺这些证据时请求包仍会生成，但会标明缺口。
- 打包完成后，把安装包放入 `artifacts/release-inbox/`，执行 `npm run release:intake` 生成 SHA-256 和收件报告，再把商店后台状态、审核编号和真实用户回收结果补回 Release / store packet / real-user result。

## 放行关系

`platform:handoff` 不代表可上架，只代表外部平台打包任务已经可执行。正式放行仍以这些门禁为准：

```bash
npm run release:readiness -- --strict
npm run release:intake -- --strict
npm run product:launch-audit -- --strict
```

当前批次只要 Android APK/AAB、Windows 安装包、桌面/macOS 包、真实用户回收或商店后台提交记录缺失，严格模式必须继续失败。iOS TestFlight 和鸿蒙包后续恢复 active 后再纳入。
