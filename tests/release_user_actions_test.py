from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_user_actions_script_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    product_audit = read_text("scripts/product_launch_audit.mjs")
    docs = read_text("docs/release/README.md")
    gap_plan = read_text("docs/release/current-gap-plan.md")
    handoff = read_text("docs/release/user-action-handoff.md")
    acceptance = read_text("docs/release/platform-acceptance-matrix.md")
    github_maintenance = read_text("docs/release/github-maintenance.md")

    assert '"release:user-actions": "node scripts/release_user_action_handoff.mjs"' in package_json
    assert "npm run release:user-actions" in ci
    assert "release:user-actions" in release_check
    assert "release:user-actions" in readiness
    assert "release-user-actions" in release_package
    assert "User Action Handoff" in release_package
    assert "release:user-actions" in finalize
    assert "release-user-actions" in finalize
    assert "release:user-actions" in summary
    assert "latestUserActions" in summary
    assert "evidence.user-actions" in product_audit
    assert "latestUserActionsReport" in product_audit
    assert "userRequired 和 approvalRequired 必须为 0" in product_audit
    assert "scripts/release_user_action_handoff.mjs" in release_check
    assert "npm run release:user-actions" in docs
    assert "安装包/人工事项/真实用户" in docs
    assert "user-action-handoff.md" in docs
    assert "user-action-handoff.md" in gap_plan
    assert "最后必须你做" in docs
    assert "需要你确认后我才能做" in handoff
    assert "最后必须你做" in handoff
    assert "CONFIRM_H5_DEPLOY=shianjieyouwu.com npm run deploy:h5" in handoff
    assert "userRequired" in handoff
    assert "approvalRequired" in handoff
    assert "release:user-actions" in acceptance
    assert "userRequired" in acceptance
    assert "approvalRequired" in acceptance
    assert "release:user-actions" in github_maintenance
    assert "userRequired/approvalRequired" in github_maintenance


def test_release_user_actions_splits_agent_approval_and_user_work():
    source = read_text("scripts/release_user_action_handoff.mjs")

    for expected in [
        "release-user-actions",
        "我可以继续做",
        "需要你确认后我才能做",
        "最后必须你做",
        "approval.h5-legal-deploy",
        "CONFIRM_H5_DEPLOY=shianjieyouwu.com npm run deploy:h5",
        "user.developer-accounts",
        "user.store-evidence",
        "user.app-record",
        "user.real-user-testing",
        "user.platform-artifacts",
        "user.store-submission",
        "current-release-scope.json",
        "activePlatformIds",
        "deferredPlatformIds",
        "inCurrentScope",
        "当前批次真实用户真机回收",
        "当前批次安装包和桌面签名证据",
        "mobileBuildEnv",
        "hbuilderxMobileResources",
        "mobileBuildRequests",
        "mobileAppResourcePacket",
        "移动端环境",
        "HBuilderX",
        "CLI 启动环境不兼容",
        "需要登录/发行权限",
        "不在 GitHub 保存账号密码、验证码、证书、签名密钥、后台 token、身份证件原件或真实用户隐私",
    ]:
        assert expected in source

    assert "agentCanContinue: actions.filter((item) => item.owner === 'agent' && item.status !== 'ready').length" in source
