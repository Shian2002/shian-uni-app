from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_artifact_metadata_requirements_cover_all_platforms_and_non_secret_fields():
    config = read_text("configs/release/artifact-metadata-requirements.json")

    for expected in [
        "android",
        "ios",
        "harmony",
        "macos",
        "windows",
        "build-metadata.json",
        "artifactPath",
        "artifactSha256",
        "deviceTestEvidence",
        "reviewAccountDelivery",
        "noReviewerPasswords",
    ]:
        assert expected in config


def test_artifact_metadata_checker_validates_hashes_and_rejects_secrets():
    source = read_text("scripts/release_artifact_metadata_check.mjs")

    for expected in [
        "RELEASE_ARTIFACT_METADATA_STRICT",
        "configs/release/artifact-metadata-requirements.json",
        "release-artifact-metadata",
        "artifactSha256 与实际文件不一致",
        "mobileprovision",
        "验证码",
        "examples.json",
        "build-metadata.json",
        "const evidenceFields",
        "requiredFieldMissing",
        "metadata[field] === undefined",
        "current-release-scope.json",
        "deferredPlatforms",
        "readiness: 'deferred'",
        "DEFERRED",
    ]:
        assert expected in source


def test_artifact_metadata_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/README.md")

    assert '"release:artifact-metadata": "node scripts/release_artifact_metadata_check.mjs"' in package_json
    assert "npm run release:artifact-metadata" in ci
    assert "release:artifact-metadata" in release_check
    assert "release:artifact-metadata" in finalize
    assert "artifactMetadata" in readiness
    assert "artifactMetadata" in release_package
    assert "latestArtifactMetadata" in summary
    assert "release:artifact-metadata" in docs
