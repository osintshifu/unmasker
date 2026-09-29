"""What a release publishes, held by the suite rather than by habit.

Each of these was a gap before it was a test. A tag reached PyPI in the same
second its CI run started, so no test had finished. A source distribution built
in a working checkout carried the local notes lying beside the project. And the
one check against a parked `if False:` sat in a pre-commit configuration that
nothing ran.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"


def _workflow(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def _job(workflow: str, name: str) -> str:
    """One job of a workflow, from its key to the next job's."""
    found = re.search(rf"(?ms)^  {name}:\n.*?(?=^  [a-z-]+:\n|\Z)", workflow)
    assert found, f"release.yml has no job {name!r}"
    return found.group(0)


def test_a_tag_publishes_only_a_commit_that_passed_ci_and_heads_master():
    workflow = _workflow("release.yml")
    ci, verify, build, publish = (
        _job(workflow, name) for name in ("ci", "verify", "build", "publish")
    )

    assert '--commit "$GITHUB_SHA"' in ci
    assert "--exit-status" in ci
    assert "    needs: ci\n" in verify
    assert 'test "$(git rev-parse HEAD)" = "$(git rev-parse origin/master)"' in verify
    for check in ("pyproject.toml", "src/unmasker/__init__.py", "ruff check .", "pytest", "mypy"):
        assert check in verify, check
    assert "    needs: verify\n" in build
    assert "    needs: build\n" in publish


def test_pypi_and_the_release_page_get_the_files_that_were_checked():
    """Built once. A second build of the same commit is a second set of files,
    and nothing says they match the ones that were installed and run."""
    workflow = _workflow("release.yml")

    assert "actions/upload-artifact@" in _job(workflow, "build")
    for name in ("publish", "github-release"):
        job = _job(workflow, name)
        assert "actions/download-artifact@" in job, name
        assert "python -m build" not in job, name


def test_every_action_is_pinned_to_a_commit():
    """A tag such as `v4` is moved by whoever controls the action, and the next
    run executes whatever it then points at, with this repository's token."""
    refs = [
        ref
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for ref in re.findall(r"(?m)^\s*- uses: [^@\s]+@([^\s#]+)", path.read_text("utf-8"))
    ]

    assert refs
    assert all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in refs), refs


def _listed() -> set[str]:
    """What `pyproject.toml` says a source distribution carries."""
    config = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = config.split("[tool.hatch.build.targets.sdist]")[1].split("\n[")[0]
    return set(re.findall(r'"([^"]+)"', block))


def _tracked() -> list[str]:
    try:
        listed = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    return [name for name in listed.decode("utf-8").split("\0") if name]


def test_a_source_distribution_is_the_tracked_tree():
    """Both directions. A tracked file the list leaves out is missing from the
    release, and a listed path nothing tracks is a local file on its way to
    PyPI. Either way, adding a path means adding it here deliberately."""
    listed, tracked = _listed(), _tracked()

    def under(name: str, entry: str) -> bool:
        return name == entry or name.startswith(entry + "/")

    left_out = [name for name in tracked if not any(under(name, e) for e in listed)]
    untracked = [entry for entry in listed if not any(under(name, entry) for name in tracked)]
    assert not left_out, left_out
    assert not untracked, untracked


def test_no_guard_is_left_parked_in_the_source():
    """`if False:` is how a watched failure gets parked while the test that
    proves it is written, and ruff's selected rules (E, F, I, UP, B) do not flag
    it. One such guard reached the working tree in `jpeg.py` and disabled the
    start-of-scan check, so `dimensions()` read a frame header out of compressed
    data. The test caught it; nothing else would have."""
    parked = [
        f"{path.relative_to(ROOT)}:{number}"
        for path in sorted((ROOT / "src").rglob("*.py"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if "if False:" in line
    ]

    assert not parked, parked
