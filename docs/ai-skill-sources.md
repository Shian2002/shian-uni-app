# AI 技能来源接入说明

本项目已按当前工作流接入以下本机技能来源。技能安装在 `~/.codex/skills/`，不随业务代码发布。

## 已安装技能

- `addyosmani-*`：来自 `addyosmani/agent-skills`，共 23 个工程生命周期技能，覆盖需求、计划、增量实现、TDD、评审、安全、性能、CI/CD、发布等。
- `graphify-codebase`：来自 `safishamsi/graphify`，用于把代码、文档、数据库 schema 和部署脚本整理成可查询图谱。CLI 已安装在 `~/.codex/tools/graphify-venv/`。
- `ui-ux-pro-max`：来自 `nextlevelbuilder/ui-ux-pro-max-skill`，用于 UI/UX、移动端 H5、Vue/uni-app 页面设计和可访问性检查。
- `wshobson-agent-marketplace`：来自 `wshobson/agents`，作为专用 agent/plugin 的目录来源，只按需挑选，不整包启用。
- `agent-rules-books`：来自 `ciembor/agent-rules-books`，用于代码评审、重构、架构边界、数据可靠性和发布检查。

## 本项目使用原则

- 涉及生产、数据库、部署、账号积分时，仍以 `docs/ops-runbook.md`、部署脚本和线上验活为最高优先级。
- 前端页面改版时优先结合 `ui-ux-pro-max`，但最终必须跑本项目现有构建和页面验活。
- 代码结构、数据库关系或部署链路不清时，优先用 `graphify-codebase` 建图或查询。
- 复杂功能改动可组合使用 `addyosmani-spec-driven-development`、`addyosmani-planning-and-task-breakdown`、`addyosmani-incremental-implementation` 和 `addyosmani-test-driven-development`。
- 合并或发布前可用 `addyosmani-code-review-and-quality`、`addyosmani-security-and-hardening`、`addyosmani-ci-cd-and-automation`、`addyosmani-shipping-and-launch` 做补充检查。

## 已验证命令

```bash
python3 ~/.codex/skills/ui-ux-pro-max/src/ui-ux-pro-max/scripts/search.py "mobile app navigation accessibility" --stack vue -n 5
/Users/junj/.codex/tools/graphify-venv/bin/python -c "import graphify; print('ok')"
```
