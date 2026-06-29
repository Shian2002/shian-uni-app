import importlib.util
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_production_smoke_does_not_embed_default_login_credentials():
    script = (ROOT / "scripts" / "production_smoke.py").read_text(encoding="utf-8")

    assert 'default=os.environ.get("SMOKE_NORMAL_USER")' in script
    assert 'default=os.environ.get("SMOKE_NORMAL_PASSWORD")' in script
    assert 'default=os.environ.get("SMOKE_ADMIN_USER")' in script
    assert 'default=os.environ.get("SMOKE_ADMIN_PASSWORD")' in script
    assert '"shian"' not in script
    assert '"asdzxc"' not in script
    assert "https://shianjieyouwu.com" in script


def test_online_ops_defaults_use_https_domain_for_production_checks():
    monitor = (ROOT / "scripts" / "production_monitor.sh").read_text(encoding="utf-8")
    preflight = (ROOT / "scripts" / "preflight_release.sh").read_text(encoding="utf-8")
    online_regression = (ROOT / "scripts" / "online_regression.mjs").read_text(encoding="utf-8")
    user_acceptance = (ROOT / "scripts" / "user_acceptance_full.mjs").read_text(encoding="utf-8")

    assert 'BASE_URL="${BASE_URL:-https://shianjieyouwu.com}"' in monitor
    assert 'BASE_URL="${BASE_URL:-https://shianjieyouwu.com}"' in preflight
    assert "process.env.REGRESSION_BASE_URL || 'https://shianjieyouwu.com'" in online_regression
    assert "process.env.REGRESSION_BASE_URL || 'https://shianjieyouwu.com'" in user_acceptance


def test_production_alert_runs_database_audit_when_db_path_is_configured(tmp_path):
    module = _load_module("production_alert", ROOT / "scripts" / "production_alert.py")
    db_path = tmp_path / "live.db"
    db_path.write_bytes(b"not sqlite")

    failures = module.collect_failures(
        base_url="http://example.test",
        service="xuan-cet-flask",
        backup_dir=str(tmp_path),
        backup_max_age_hours=30,
        disk_path="/",
        disk_threshold=99,
        since="15 min ago",
        db_audit_path=str(db_path),
        checks={
            "health": lambda _base_url: None,
            "service": lambda _service: None,
            "disk": lambda _path, _threshold: None,
            "backup": lambda _backup_dir, _max_age_hours: None,
            "logs": lambda _service, _since: None,
        },
    )

    assert any("数据库审计" in item or "db_audit" in item for item in failures)


def test_deploy_runs_preflight_by_default_and_allows_explicit_skip():
    script = (ROOT / "deploy-to-server.sh").read_text(encoding="utf-8")

    assert "SKIP_PREFLIGHT" in script
    assert "scripts/preflight_release.sh" in script
    assert "SKIP_PREFLIGHT=1" in script


def test_online_regression_checks_deep_health():
    script = (ROOT / "scripts" / "online_regression.mjs").read_text(encoding="utf-8")

    assert "checkDeepHealth" in script
    assert "/api/health/deep" in script


def test_online_regression_oauth_mocks_logged_in_side_requests():
    script = (ROOT / "scripts" / "online_regression.mjs").read_text(encoding="utf-8")

    assert "**/api/user/bindings" in script
    assert "**/api/bindings" in script
    assert "**/api/comprehensive/options" in script
    assert "**/api/points/log**" in script


def test_baidu_backup_script_dry_run_validates_without_uploading(tmp_path):
    backup = tmp_path / "tianji-20260604.db"
    backup.write_bytes(b"sqlite backup")

    result = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts" / "upload_baidu_backup.sh"),
            "--backup",
            str(backup),
            "--dry-run",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "DRY-RUN" in result.stdout
    assert "bypy upload" in result.stdout
