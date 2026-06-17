# 发行产物收件与校验

> 更新时间：2026-06-15  
> 目标：把 HBuilderX、Xcode、DevEco、Windows 打包机产出的安装包统一收进本地证据链，避免散落在聊天、桌面或不同机器上。

## 收件目录

把外部生成的安装包或构建记录放到：

```text
artifacts/release-inbox/
```

推荐结构：

```text
artifacts/release-inbox/
  v1.0.0/
    android/
      shian-v1.0.0-release.apk
      shian-v1.0.0-google-play.aab
      build-metadata.json
    ios/
      testflight-build-100.md
      shian-v1.0.0.ipa
      build-metadata.json
    harmony/
      shian-v1.0.0.hap
      build-metadata.json
    macos/
      shian-v1.0.0-arm64.dmg
      shian-v1.0.0-arm64.zip
      build-metadata.json
    windows/
      shian-v1.0.0-setup.exe
      shian-v1.0.0.msi
      build-metadata.json
```

`artifacts/` 已被 `.gitignore` 排除，安装包不会进入 Git。GitHub Releases 上传的是人工确认后的 release 资产，不是 Git commit。

## 校验命令

普通扫描：

```bash
npm run release:intake
```

严格模式：

```bash
npm run release:intake -- --strict
```

输出目录：

```text
artifacts/release-artifact-intake/<timestamp>-v1.0.0/
```

每次输出：

- `report.json`：平台状态、文件大小、SHA-256、硬缺口。
- `README.md`：人工可读收件报告。
- `checksums.sha256`：二进制安装包 hash。

安装包回传后还要校验元数据：

```bash
npm run release:artifact-metadata
```

严格模式：

```bash
npm run release:artifact-metadata -- --strict
```

每个平台目录的 `build-metadata.json` 只记录非敏感字段：版本、commit、构建工具、构建人或机器标识、构建时间、安装包路径、SHA-256、签名/公证状态、真机截图路径、审核账号交付方式。不要写审核账号密码、验证码、证书、签名密钥、keystore、p12、mobileprovision 或后台 token。

## 禁止放入 inbox 的材料

这些材料只能留在本机安全目录或密钥管理系统，不能放入 `artifacts/release-inbox/`，也不能进入 GitHub：

- Android keystore、`.jks`、`.keystore`。
- Apple `.p12`、`.mobileprovision`、Developer ID 证书。
- Windows 签名证书、私钥、`.pem`、`.key`。
- `.env`、短信/邮件/支付/AI 密钥。
- 真实用户数据、生产数据库、验证码日志。

脚本发现上述文件名会直接失败。

## 和 finalize 的关系

完整收口命令：

```bash
npm run release:finalize
```

`release:finalize` 会先跑 `release:intake`，再生成：

- 平台打包交接包。
- 发行产物元数据报告。
- 真实用户测试包。
- readiness 报告。
- GitHub Release 草稿包。
- 商店提交材料包。

当前批次只要 Android APK/AAB、Windows EXE/MSI、macOS DMG/ZIP、`build-metadata.json` 元数据或当前批次真实用户回收报告缺失，最终结论仍必须是 `not-ready`。iOS IPA/TestFlight 构建记录和鸿蒙 HAP/AppGallery 包已 deferred，后续恢复 active 后再纳入 strict 结论。
