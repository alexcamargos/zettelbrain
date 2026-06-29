"""Unit tests for the setup configuration utility.

Validates the setup automation under different parameters, ensuring directory creation,
file updates, skills folder syncing/compilation, and correct exit codes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

import setup


def test_get_repo_root() -> None:
    """Test that get_repo_root returns a valid Path directory containing pyproject.toml.

    Returns:
        None

    """
    root = setup.get_repo_root()
    assert isinstance(root, Path)
    assert (root / "pyproject.toml").exists()


def test_configure_gemini_success(mocker: MockerFixture) -> None:
    """Test Gemini configuration success path with skills syncing.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mock_repo_root = Path("/fake/root")

    mocker.patch.object(Path, "mkdir")
    mocker.patch.object(Path, "unlink")
    mocker.patch.object(Path, "rename")

    # Mock exists check for various files
    def exists_mock(self: Path) -> bool:
        if self.name == "settings.json":
            return False  # Force creation of default settings
        return self.name in ("skills", ".cursorrules")

    mocker.patch.object(Path, "exists", exists_mock)

    # Mock files inside skills/ to sync
    fake_skill_a = Path("/fake/root/skills/skill_a.md")
    fake_skill_b = Path("/fake/root/skills/skill_b.md")
    mocker.patch.object(Path, "glob", return_value=[fake_skill_a, fake_skill_b])

    mock_read = mocker.patch.object(Path, "read_text", return_value="fake skill content")
    mock_write = mocker.patch.object(Path, "write_text")

    exit_code = setup.configure_gemini(mock_repo_root)

    assert exit_code == 0
    # Should create settings.json and write the two synced skills
    assert mock_write.call_count == 3
    # Check read called for source skills
    mock_read.assert_any_call(encoding="utf-8")
    # Path.rename called for .cursorrules -> .cursorrules.bak

    Path.rename.assert_called_once()


def test_bootstrap_local_workspace_creates_ignored_directories(mocker: MockerFixture) -> None:
    """Test local workspace bootstrap creates every ignored runtime directory."""
    mock_repo_root = Path("/fake/root")
    mocker.patch.object(Path, "exists", return_value=False)
    mock_mkdir = mocker.patch.object(Path, "mkdir")

    exit_code = setup.bootstrap_local_workspace(mock_repo_root)

    assert exit_code == 0
    assert mock_mkdir.call_count == len(setup.LOCAL_WORKSPACE_DIRS)
    for call_args in mock_mkdir.call_args_list:
        assert call_args.kwargs == {"parents": True, "exist_ok": True}


def test_bootstrap_local_workspace_skips_existing_directories(
    mocker: MockerFixture,
) -> None:
    """Test local workspace bootstrap is idempotent for existing directories."""
    mock_repo_root = Path("/fake/root")
    mocker.patch.object(Path, "exists", return_value=True)
    mock_mkdir = mocker.patch.object(Path, "mkdir")

    exit_code = setup.bootstrap_local_workspace(mock_repo_root)

    assert exit_code == 0
    mock_mkdir.assert_not_called()


def test_bootstrap_local_workspace_os_error(mocker: MockerFixture) -> None:
    """Test local workspace bootstrap handles filesystem errors."""
    mock_repo_root = Path("/fake/root")
    mocker.patch.object(Path, "exists", return_value=False)
    mocker.patch.object(Path, "mkdir", side_effect=OSError("Permission denied"))

    exit_code = setup.bootstrap_local_workspace(mock_repo_root)

    assert exit_code == 1


def test_configure_gemini_orphan_cleanup(mocker: MockerFixture) -> None:
    """Test Gemini configuration cleans up orphan skills.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mock_repo_root = Path("/fake/root")

    mocker.patch.object(Path, "mkdir")
    mocker.patch.object(Path, "rename")
    mock_unlink = mocker.patch.object(Path, "unlink")

    # Mock exists
    def exists_mock(self: Path) -> bool:
        return self.name in ("settings.json", "skills")

    mocker.patch.object(Path, "exists", exists_mock)

    # Glob mock
    fake_source_skill = Path("/fake/root/skills/active.md")
    fake_existing_skills = [
        Path("/fake/root/.gemini/skills/active.md"),
        Path("/fake/root/.gemini/skills/orphan.md"),
    ]

    def glob_mock(self: Path, pattern: str) -> list[Path]:
        if "skills" in self.parts and ".gemini" not in self.parts:
            return [fake_source_skill]
        return fake_existing_skills

    mocker.patch.object(Path, "glob", glob_mock)
    mocker.patch.object(Path, "read_text", return_value="active content")
    mocker.patch.object(Path, "write_text")

    exit_code = setup.configure_gemini(mock_repo_root)

    assert exit_code == 0
    # orphan.md should be deleted (unlinked)
    mock_unlink.assert_called_once()


def test_configure_cursor_success(mocker: MockerFixture) -> None:
    """Test Cursor configuration success path with rules compilation.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mock_repo_root = Path("/fake/root")

    mocker.patch.object(Path, "mkdir")
    mocker.patch.object(Path, "unlink")

    # Mock exists
    def exists_mock(self: Path) -> bool:
        if self.name == "mcp.json":
            return False
        return self.name in ("ZETTELBRAIN.md", "skills")

    mocker.patch.object(Path, "exists", exists_mock)

    # Mock skills files
    fake_skill_1 = Path("/fake/root/skills/1_start.md")
    fake_skill_2 = Path("/fake/root/skills/2_recall.md")
    mocker.patch.object(Path, "glob", return_value=[fake_skill_1, fake_skill_2])

    def read_text_mock(self: Path, encoding: str = "utf-8") -> str:
        if self.name == "ZETTELBRAIN.md":
            return "Master rules content"
        if self.name == "1_start.md":
            return "Start workflow"
        if self.name == "2_recall.md":
            return "Recall workflow"
        return ""

    mocker.patch.object(Path, "read_text", read_text_mock)
    mock_write = mocker.patch.object(Path, "write_text")

    exit_code = setup.configure_cursor(mock_repo_root)

    assert exit_code == 0
    # Writes mcp.json and compiled .cursorrules
    assert mock_write.call_count == 2
    # Verify concatenated content in .cursorrules write call
    compiled_rules_call = mock_write.call_args_list[1][0][0]
    assert "Master rules content" in compiled_rules_call
    assert "# Integrated Skills Workflow" in compiled_rules_call
    assert "Start workflow" in compiled_rules_call
    assert "Recall workflow" in compiled_rules_call


def test_configure_cursor_missing_gemini_md(mocker: MockerFixture) -> None:
    """Test Cursor configuration when ZETTELBRAIN.md does not exist.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mock_repo_root = Path("/fake/root")

    mocker.patch.object(Path, "mkdir")
    mocker.patch.object(Path, "unlink")

    def exists_mock(self: Path) -> bool:
        if self.name == "mcp.json":
            return True
        if self.name == "ZETTELBRAIN.md":
            return False
        return False

    mocker.patch.object(Path, "exists", exists_mock)
    mock_write = mocker.patch.object(Path, "write_text")

    exit_code = setup.configure_cursor(mock_repo_root)

    assert exit_code == 0
    # No writing should occur
    mock_write.assert_not_called()


def test_main_no_arguments(mocker: MockerFixture) -> None:
    """Test main function behavior when no arguments are provided.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mocker.patch.object(sys, "argv", ["setup.py"])
    with pytest.raises(SystemExit) as excinfo:
        setup.main()

    assert excinfo.value.code == 1


def test_main_invalid_argument(mocker: MockerFixture) -> None:
    """Test main function behavior with an unrecognized provider argument.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mocker.patch.object(sys, "argv", ["setup.py", "invalid_provider"])
    with pytest.raises(SystemExit) as excinfo:
        setup.main()

    assert excinfo.value.code == 1


def test_main_gemini_argument(mocker: MockerFixture) -> None:
    """Test main function executes Gemini configuration correctly.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mocker.patch.object(sys, "argv", ["setup.py", "gemini"])
    mock_configure = mocker.patch("setup.configure_gemini", return_value=0)

    with pytest.raises(SystemExit) as excinfo:
        setup.main()

    mock_configure.assert_called_once()
    assert excinfo.value.code == 0


def test_main_bootstrap_argument(mocker: MockerFixture) -> None:
    """Test main function executes local bootstrap correctly."""
    mocker.patch.object(sys, "argv", ["setup.py", "bootstrap"])
    mock_bootstrap = mocker.patch("setup.bootstrap_local_workspace", return_value=0)

    with pytest.raises(SystemExit) as excinfo:
        setup.main()

    mock_bootstrap.assert_called_once()
    assert excinfo.value.code == 0


def test_main_local_argument(mocker: MockerFixture) -> None:
    """Test main function supports local as a bootstrap alias."""
    mocker.patch.object(sys, "argv", ["setup.py", "local"])
    mock_bootstrap = mocker.patch("setup.bootstrap_local_workspace", return_value=0)

    with pytest.raises(SystemExit) as excinfo:
        setup.main()

    mock_bootstrap.assert_called_once()
    assert excinfo.value.code == 0


def test_main_cursor_argument(mocker: MockerFixture) -> None:
    """Test main function executes Cursor configuration correctly.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mocker.patch.object(sys, "argv", ["setup.py", "cursor"])
    mock_configure = mocker.patch("setup.configure_cursor", return_value=0)

    with pytest.raises(SystemExit) as excinfo:
        setup.main()

    mock_configure.assert_called_once()
    assert excinfo.value.code == 0


def test_configure_gemini_os_error(mocker: MockerFixture) -> None:
    """Test Gemini configuration handles OSError gracefully and returns code 1.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mock_repo_root = Path("/fake/root")
    mocker.patch.object(Path, "mkdir", side_effect=OSError("Permission denied"))

    exit_code = setup.configure_gemini(mock_repo_root)
    assert exit_code == 1


def test_configure_cursor_os_error(mocker: MockerFixture) -> None:
    """Test Cursor configuration handles OSError gracefully and returns code 1.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mock_repo_root = Path("/fake/root")
    mocker.patch.object(Path, "mkdir", side_effect=OSError("Permission denied"))

    exit_code = setup.configure_cursor(mock_repo_root)
    assert exit_code == 1


def test_clean_environment_success(mocker: MockerFixture) -> None:
    """Test clean_environment successfully deletes files and folders.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mock_repo_root = Path("/fake/root")
    mocker.patch.object(Path, "exists", return_value=True)
    mock_rmtree = mocker.patch("shutil.rmtree")
    mock_unlink = mocker.patch.object(Path, "unlink")

    exit_code = setup.clean_environment(mock_repo_root)

    assert exit_code == 0
    # Should call rmtree twice (.gemini/ and .cursor/)
    assert mock_rmtree.call_count == 2
    # Should call unlink twice (.cursorrules and .cursorrules.bak)
    assert mock_unlink.call_count == 2


def test_clean_environment_empty(mocker: MockerFixture) -> None:
    """Test clean_environment when no tool-specific files exist.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mock_repo_root = Path("/fake/root")
    mocker.patch.object(Path, "exists", return_value=False)
    mock_rmtree = mocker.patch("shutil.rmtree")
    mock_unlink = mocker.patch.object(Path, "unlink")

    exit_code = setup.clean_environment(mock_repo_root)

    assert exit_code == 0
    mock_rmtree.assert_not_called()
    mock_unlink.assert_not_called()


def test_clean_environment_os_error(mocker: MockerFixture) -> None:
    """Test clean_environment handles OSError gracefully.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mock_repo_root = Path("/fake/root")
    mocker.patch.object(Path, "exists", return_value=True)
    mocker.patch("shutil.rmtree", side_effect=OSError("Permission denied"))

    exit_code = setup.clean_environment(mock_repo_root)

    assert exit_code == 1


def test_main_clean_argument(mocker: MockerFixture) -> None:
    """Test main function executes clean configuration correctly.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mocker.patch.object(sys, "argv", ["setup.py", "clean"])
    mock_clean = mocker.patch("setup.clean_environment", return_value=0)

    with pytest.raises(SystemExit) as excinfo:
        setup.main()

    mock_clean.assert_called_once()
    assert excinfo.value.code == 0


def test_main_uninstall_argument(mocker: MockerFixture) -> None:
    """Test main function executes uninstall configuration correctly.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        None

    """
    mocker.patch.object(sys, "argv", ["setup.py", "uninstall"])
    mock_clean = mocker.patch("setup.clean_environment", return_value=0)

    with pytest.raises(SystemExit) as excinfo:
        setup.main()

    mock_clean.assert_called_once()
    assert excinfo.value.code == 0
