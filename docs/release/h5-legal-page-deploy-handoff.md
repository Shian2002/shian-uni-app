# H5 法律页部署交接

> 更新时间：2026-06-15  
> 目标域名：`https://shianjieyouwu.com/`

## 当前结论

- HTTPS 域名已可访问。
- ICP 备案号 `粤ICP备2026072162号-1` 已在营销页页脚和关于页展示。
- 本地 H5 构建产物已包含 `pages/legal/index` 法律页正文。
- 当前线上站点还没有部署包含法律页正文的最新版 H5 产物，`LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls` 仍为 not-ready。
- 未经确认不要把 `configs/release/legal-urls.json` 的 `status` 改为 `ready`。

## 本地待部署证据

```text
dist/build/h5/assets/pages-legal-index.DvjrvxOS.js
SHA-256: c35419c6d5e40e878b5098bfa61aff8ad5caa8d96318993b4f8f430161e05bff
```

本地构建产物已包含以下审核关键字：

- 隐私政策、账号注销、数据删除、第三方服务、联系我们。
- 用户协议、不构成医疗、法律、金融、积分与付费、知识产权、账号注销。

## 部署前检查

```bash
npm run lint
npm run typecheck
python3 -m pytest -q tests/store_materials_test.py tests/domain_https_test.py tests/release_package_hard_blocks_test.py
npm run build:h5
npm run store:legal-urls
npm run domain:https
npm run h5:legal-deploy-status
```

## 部署命令

部署属于外部生产动作，执行前需要明确确认。

这次只需要更新 H5 法律页产物时，优先走 H5-only 部署：

```bash
DRY_RUN=1 npm run deploy:h5
CONFIRM_H5_DEPLOY=shianjieyouwu.com npm run deploy:h5
```

该脚本只同步 `dist/build/h5/index.html`、`dist/build/h5/assets`、`dist/build/h5/static` 到服务器，不同步后端代码、不重启后端服务。部署前会备份当前线上 H5 静态资源，部署后会运行 `npm run h5:legal-deploy-status -- --strict`、`LEGAL_URL_CHECK_SCOPE=website LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict` 和线上监控检查。商店提审严格检查默认跳过，需要上架前再显式加 `STORE_SUBMISSION_CHECK=1`。

默认不会上传 `static/alipay-recharge.jpg`，避免商店审核包混入外部充值素材。若正式官网需要同步充值二维码，必须显式加 `INCLUDE_RECHARGE_ASSETS=1`。

如果同时包含后端代码、数据库或服务配置改动，再走完整部署：

```bash
bash deploy-to-server.sh
```

完整部署脚本会同步后端代码、前端产物并重启后端服务，执行前必须确保后端 Python 改动已处理清楚。

## 部署后放行检查

```bash
LEGAL_URL_CHECK_SCOPE=website LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict
npm run domain:https -- --strict
npm run h5:legal-deploy-status -- --strict
npm run release:package
npm run release:summary
```

网站 H5 上线只要求法律页线上可访问、正文完整、HTTPS 和 ICP 页脚证据可核验。只有准备提交商店时，才运行 `STORE_SUBMISSION_CHECK=1 CONFIRM_H5_DEPLOY=shianjieyouwu.com npm run deploy:h5` 或 `LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict`；线上法律 URL 严格验证、APP 备案或不适用说明、负责人别名和商店后台截图都完成后，才能把相关发行台账标记为 ready。

## 回滚命令

H5-only 部署会先在服务器 `BACKUP_DIR=/home/lighthouse/backups/xuan-cet/h5` 下保存 `h5-deploy-*.tar.gz`。如果部署后法律页、首页或静态资源异常，使用最近备份回滚：

```bash
CONFIRM_H5_ROLLBACK=shianjieyouwu.com npm run rollback:h5
```

如需指定某个备份包：

```bash
ROLLBACK_ARCHIVE=/home/lighthouse/backups/xuan-cet/h5/h5-deploy-YYYYMMDD-HHMMSS.tar.gz CONFIRM_H5_ROLLBACK=shianjieyouwu.com npm run rollback:h5
```

回滚脚本只恢复 H5 静态资源，不修改后端代码、不重启后端服务。回滚后会以 `https://shianjieyouwu.com/` 为默认目标运行线上监控检查。
