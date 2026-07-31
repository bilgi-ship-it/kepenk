from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "release.yml"
COMMIT_PIN = re.compile(r"^[0-9a-f]{40}$")


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_is_tag_only() -> None:
    workflow = _workflow_text()

    assert 'tags:\n      - "v*.*.*"' in workflow
    assert "workflow_dispatch" not in workflow
    assert "pull_request" not in workflow


def test_external_actions_are_pinned_to_commit_shas() -> None:
    uses = re.findall(r"^\s*uses:\s*([^\s#]+)", _workflow_text(), flags=re.MULTILINE)

    assert uses
    for reference in uses:
        _, separator, revision = reference.rpartition("@")
        assert separator == "@"
        assert COMMIT_PIN.fullmatch(revision), reference


def test_trusted_publishing_is_scoped_to_release_job() -> None:
    workflow = _workflow_text()
    publish_job = workflow.split("  pypi-publish:\n", 1)[1]

    assert "environment:\n      name: pypi" in publish_job
    assert "id-token: write" in publish_job
    assert "pypa/gh-action-pypi-publish@" in publish_job
    assert workflow.count("id-token: write") == 1


def test_release_checks_tag_and_package_version_match() -> None:
    workflow = _workflow_text()

    assert 'expected_tag = f"v{version}"' in workflow
    assert 'actual_tag = os.environ["GITHUB_REF_NAME"]' in workflow
    assert "actual_tag != expected_tag" in workflow
