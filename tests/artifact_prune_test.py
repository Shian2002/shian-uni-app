import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_artifact_prune_keeps_release_inbox_and_ip_evidence_out_of_managed_set():
    package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    source = (ROOT / "scripts" / "prune_old_artifacts.mjs").read_text(encoding="utf-8")

    assert package_json["scripts"]["artifacts:prune"] == "node scripts/prune_old_artifacts.mjs"
    assert package_json["scripts"]["artifacts:prune:apply"] == "node scripts/prune_old_artifacts.mjs --apply"
    assert "const managedDirs = [" in source
    managed_block = source.split("const managedDirs = [", 1)[1].split("]", 1)[0]
    assert "'release-inbox'" not in managed_block
    assert "'current-downloads'" not in managed_block
    assert "'ip-evidence'" not in managed_block
    assert "'soft-copyright-application'" not in managed_block
    assert "'platform-backend-matrix'" in managed_block
    assert "'final-package-plan'" in managed_block
    assert "'final-package-preflight'" in managed_block
    assert "'final-package-completeness'" in managed_block
    assert "'current-index'" in managed_block
    assert "'release-finalize'" in managed_block
    assert "'package-binary-cleanup'" in managed_block
    assert "rmSync(item.path, { recursive: true, force: true })" in source
    assert "if (!apply) continue" in source
