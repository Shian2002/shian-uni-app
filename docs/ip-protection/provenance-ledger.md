# 项目权属与证据台账

本文档用于在代码库内固定项目形成过程、源代码证据、版本证据和运营主体变更边界。它不参与前端构建，不向终端用户展示。

## 一、项目标识

- 项目名称：时安解忧屋 / xuan-cet-tai
- 软件申请建议名称：时安解忧屋综合服务平台
- 版本建议：V1.0.0
- 项目形态：uni-app H5 + Flask API + SQLite 数据库
- 主要模块：首页综合 AI、八字、奇门、紫微、塔罗、择吉、用户中心、积分会员、付费内容、后台管理、运维脚本

## 二、源代码形成记录

当前仓库 Git 历史可作为源代码形成和持续迭代的技术证据。正式举证时应以完整 Git 仓库、远程仓库记录、服务器部署记录和导出的证据包共同使用。

早期提交记录：

| 时间 | 提交 | 作者 | 说明 |
| --- | --- | --- | --- |
| 2026-05-23 20:05:12 +08:00 | `ffc61b5c165f9aa5c18d59c0dafb2df2a347b4e9` | JunJunXu `<904752171@qq.com>` | 完整的时安解忧屋项目（前端 uni-app H5） |
| 2026-05-23 20:33:48 +08:00 | `f205987684088c133805bcf07aa8cad14922d46c` | JunJunXu `<904752171@qq.com>` | 修复控制台两个错误：FAQ toggle守卫 + 塔罗对话列表类型检查 |
| 2026-05-23 20:39:58 +08:00 | `fa3dcd05c6d82a83a1f134048672e18f7557369e` | JunJunXu `<904752171@qq.com>` | 修复移动端导航栏按钮溢出检测：改用视口宽度作为边界 |
| 2026-05-24 01:56:30 +08:00 | `a669d892fb3e379f691dffbb9e944bebe55df707` | JunJunXu `<904752171@qq.com>` | feat: 积分中心页面 + TopNav积分显示 |
| 2026-05-25 00:56:29 +08:00 | `32bf799720cfdcf4936e33e8bccea742a2217795` | JunJunXu `<904752171@qq.com>` | feat: 奇门AI流式解读 + 积分中心UI修复 + 通用历史记录侧边栏 |

当前已知基线提交：

| 时间 | 提交 | 作者 | 说明 |
| --- | --- | --- | --- |
| 2026-06-13 23:21:32 +08:00 | `b6bb2e48b0800a920332cd036e937f447a21e9f3` | JunJunXu `<904752171@qq.com>` | fix: improve mobile liuyao artifact layout |
| 2026-06-17 10:34:07 +08:00 | `abb3095ac0a8e0f36cdcac5d26b1ad17f50a1d28` | JunJunXu `<904752171@qq.com>` | chore: track release app icon assets |
| 2026-06-17 18:43:48 +08:00 | `58c77ebea7aedc48818953afa079e9d2044c8ed5` | Shian2002 `<285371818+Shian2002@users.noreply.github.com>` | Fix agent entry auth flow |

## 三、Logo 与图形标识记录

Logo 是项目知识产权证据链的一部分，后续网站、HBuilderX、DCloud 云打包、Xcode、DevEco、桌面端和商店后台只使用同一原始符号的格式化派生图，不使用第三方图形、图库素材、未授权字体或外部生成图替换。

当前 logo 资产：

- 原始透明符号留档：`src/static/images/logo-mark-transparent.png`
- 网站和桌面实底源图：`src/static/images/logo.png`
- 商店和移动端 1024 母图：`src/static/app-icons/app-icon-1024.png`
- 桌面端派生图标：`desktop/assets/icon.png`、`desktop/assets/icon.icns`、`desktop/assets/icon.ico`
- 配置和检查入口：`configs/release/app-icons.json`、`scripts/app_icon_asset_check.mjs`

派生规则：

- 原始透明符号用于权属和形态留档，保留在 Git 历史和当前仓库文件中。
- 网站 favicon、apple touch icon、移动端 requiredIcons 和桌面端 icon 仅做尺寸、格式、实底背景和平台适配处理。
- 应用上传图必须是不透明 PNG，避免商店、浏览器或打包工具在深色背景下识别成黑图或空图。
- 每次修改 logo 或图标派生图后，先运行 `npm run release:app-icons` 并保留 `artifacts/app-icons/*/report.json`。

## 四、源程序范围

可用于证明软件源程序组成的主要目录：

- `src/pages/`
- `src/components/`
- `src/package-tools/`
- `src/package-user/`
- `src/api/`
- `src/store/`
- `src/utils/`
- `backend/`
- `database/schema.sql`
- `scripts/`
- `docs/superpowers/`
- `docs/ops-runbook.md`
- `docs/security-duty-checklist.md`

不应作为权属证明源程序提交的内容：

- `.env`、密钥、支付证书、生产配置
- `backend/tianji.db`、用户上传文件、生产用户数据
- `node_modules/`、`dist/`、缓存、构建产物
- `artifacts/private-owner-notes/` 中的个人私有说明

## 五、已生成证据材料

以下材料位于 `.gitignore` 覆盖的 `artifacts/` 目录，不会自动提交到 Git。正式举证时应保留原文件、哈希校验文件和生成时间。

知识产权证据包：

- `artifacts/ip-evidence/20260617-191500/xuan-cet-tai-source-20260617-191500.tar.gz`
- `artifacts/ip-evidence/20260617-191500/evidence-metadata.txt`
- `artifacts/ip-evidence/20260617-191500/archived-files.txt`
- `artifacts/ip-evidence/20260617-191500/SHA256SUMS.txt`

Git 历史证据包：

- `artifacts/ip-evidence/20260617-191500-git-history/xuan-cet-tai-git-history.bundle`
- `artifacts/ip-evidence/20260617-191500-git-history/git-log.txt`
- `artifacts/ip-evidence/20260617-191500-git-history/git-status.txt`
- `artifacts/ip-evidence/20260617-191500-git-history/SHA256SUMS.txt`

软件著作权申请辅助材料：

- `artifacts/soft-copyright-application/20260617-191500/时安解忧屋综合服务平台V1.0.0-源程序鉴别材料.pdf`
- `artifacts/soft-copyright-application/20260617-191500/时安解忧屋综合服务平台V1.0.0-软件设计说明书.pdf`
- `artifacts/soft-copyright-application/20260617-191500/时安解忧屋综合服务平台V1.0.0-软件设计说明书.docx`
- `artifacts/soft-copyright-application/20260617-191500/软著申请字段草稿.md`

材料页数核对：

- 源程序鉴别材料：60 页
- 软件设计说明书：64 页

本轮软著字段草稿记录：

- 当前提交哈希：`58c77ebea7aedc48818953afa079e9d2044c8ed5`
- 抽取范围：约 253 个源文件、108634 行文本
- 新增覆盖范围：`configs/release/`、`desktop/`、`android-shell/`、根目录发布/回滚/启动脚本、多端发行和图标检查脚本

## 六、运营主体变更边界

如果后续 ICP 备案、微信支付、公众号/小程序、客服、开票或推广账号切换到公司主体，应保留以下边界：

1. 公司作为网站主办单位、支付结算主体、客服和推广主体。
2. 运营主体变更不等于软件著作权、商标权、作品著作权或源代码所有权转让。
3. 对外材料可以写“公司负责运营”，不应写“公司拥有本软件全部知识产权”。
4. 若公司需要独占运营、知识产权转让、以公司名义申请软著/商标或进行融资交割，应另行签署正式书面文件。

相关仓库文档：

- `docs/ip-protection/operation-subject-change-note.md`
- `docs/ip-protection/ownership-operation-memo-template.md`
- `docs/ip-protection/trademark-filing-payment-checklist.md`

## 七、后续举证建议

每次发生重要变化时，应新增一条记录：

- 主体变更：记录变更日期、变更事项、变更前后主体、对应 Git 提交哈希和截图。
- 大版本发布：记录版本号、Git tag、发布包、线上地址、测试报告和证据包哈希。
- 软著/商标：记录申请号、申请日期、权利人、申请文件和回执。
- 收益/支付：记录支付主体变化、合同/备忘录、收款账号和分配口径。

建议命令：

```bash
git log --reverse --format='%h %H %ad %an %ae %s' --date=iso-strict
bash scripts/create_ip_evidence_package.sh
/Users/junj/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/generate_soft_copyright_materials.py
```

## 八、注意事项

- 不要把个人身份证件、验证码、软著账号、支付密钥、生产数据库或用户数据提交到 Git。
- 不要把 `artifacts/private-owner-notes/` 发给公司或上传到共享仓库。
- 如果仓库需要交付公司，交付前应先确认哪些文档属于团队可见材料，哪些属于个人私有材料。
- 若发生争议，应同时保留 Git 仓库、远程仓库审计记录、服务器部署记录、域名注册记录、支付/备案变更记录、聊天记录和证据包哈希。
