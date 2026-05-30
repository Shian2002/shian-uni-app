# Codex Handoff — 线上数据库优先优化

We are continuing from this handoff. Read this document first, inspect the current repo state, verify what still applies, and continue from the next steps without assuming the old chat context is available.

## Repo

- Path: `/Users/junj/WorkBuddy/2026-05-12-task-96/uniapp多平台Hbuilder/xuan-cet-tai`
- Branch: `master`
- Target: `http://119.29.128.18/`

## Current Goal

按“线上数据库优先”的路线执行：先保护线上 SQLite 数据，再跑性能、视觉、代码风险和产品方向审查。

## Completed

- 找到上下文维护 skill：`/Users/junj/.codex/skills/keep-codex-fast/SKILL.md`
- 按 skill 规则跑了只读报告，没有清理本地 Codex 状态。
- 验证线上登录：`shian/asdzxc` 成功。
- 验证线上 `/api/membership`：`points = 833`。
- 验证线上 `/api/points/log`：包含 `restore_high_points +773` 和 `restore_points +40`。
- 审计远端 DB：
  - 当前线上库：`/opt/xuan-cet/backend/tianji.db`
  - 高积分来源库：`/home/lighthouse/tianji/flask-source/backend/tianji.db`
  - 线上当前库和来源库各有独有数据，不能整库覆盖。
- 修改 `scripts/deploy.sh`：
  - `DATABASE_URL` 指向 `/opt/xuan-cet/backend/tianji.db`
  - 复制后端时排除 `tianji.db*`
  - 重启前备份 `tianji.db.bak-deploy-<timestamp>`
- 验证：
  - `bash -n scripts/deploy.sh deploy-to-server.sh download-from-server.sh`
  - Python AST syntax check for `backend/app.py` and `backend/models.py`
  - `npm run build:h5`

## Important Facts

- `gstack browse` initially returned `NEEDS_SETUP`; user authorized agent to execute the route end to end.
- Current repo had `.gitignore` dirty before these edits, adding `.gstack/`.
- `/review` on `master` may stop because the skill treats the base branch as not reviewable unless there is a feature diff.
- `/design-review` requires a clean working tree before it runs fixes. For report-only visual checking, prefer using browse screenshots and writing a report manually if the skill gates on dirty state.

## Next Steps

1. Commit or otherwise preserve the current data-safety changes so the working tree is clean.
2. Build gstack browse if still needed.
3. Run `/benchmark` baseline for:
   - `/`
   - profile / personal center
   - bazi
   - comprehensive AI
   - tarot
4. Run visual report on desktop/mobile without code fixes unless explicitly approved.
5. Run code risk review if there is a branch diff; otherwise do a source-risk scan focused on deploy/database/points/auth.
6. Summarize risks and recommended follow-up work.

## Do Not Do

- Do not overwrite `/opt/xuan-cet/backend/tianji.db`.
- Do not sync the old source DB into production wholesale.
- Do not delete Codex sessions/logs/worktrees as part of `keep-codex-fast`; first run is report-only.
