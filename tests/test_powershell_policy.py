from pathlib import Path

import pytest

from kepenk.engine import PolicyEngine
from kepenk.models import Action
from kepenk.policy import load_policy


POLICY_PATH = Path(__file__).resolve().parents[1] / "examples" / "powershell" / "kepenk.yaml"


@pytest.fixture(scope="module")
def engine() -> PolicyEngine:
    return PolicyEngine(load_policy(POLICY_PATH))


@pytest.mark.parametrize(
    "command",
    [
        'pwsh -NoProfile -Command "Remove-Item C:\\work -Recurse -Force"',
        "pwsh -Command 'ri C:\\temp -r -Force'",
        "cmd /c rd C:\\work /s /q",
    ],
)
def test_destructive_windows_deletes_are_denied(engine: PolicyEngine, command: str) -> None:
    decision = engine.evaluate(Action(type="shell", command=command))
    assert decision.effect == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "git push origin main",
        'pwsh -NoProfile -Command "Publish-Module -Path .\\dist"',
        "dotnet nuget push package.nupkg --source nuget.org",
        "npm publish",
    ],
)
def test_remote_or_publish_actions_require_approval(
    engine: PolicyEngine, command: str
) -> None:
    decision = engine.evaluate(Action(type="shell", command=command))
    assert decision.effect == "approval"


@pytest.mark.parametrize(
    "command",
    [
        'pwsh -NoProfile -Command "Invoke-Pester"',
        "dotnet test",
        'pwsh -NoProfile -Command "Get-ChildItem src"',
        'pwsh -NoProfile -Command "Get-Content README.md"',
        "git status --short",
    ],
)
def test_tests_and_read_only_inspection_are_allowed(
    engine: PolicyEngine, command: str
) -> None:
    decision = engine.evaluate(Action(type="shell", command=command))
    assert decision.effect == "allow"


def test_non_recursive_remove_item_uses_default_approval(engine: PolicyEngine) -> None:
    decision = engine.evaluate(
        Action(type="shell", command='pwsh -Command "Remove-Item .\\build.log"')
    )
    assert decision.effect == "approval"
