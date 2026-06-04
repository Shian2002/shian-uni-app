import subprocess


def test_patch_tab_dom_is_idempotent_on_installed_uni_h5():
    result = subprocess.run(
        ["node", "scripts/patch-tab-dom.js"],
        cwd=".",
        text=True,
        capture_output=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stdout + result.stderr
