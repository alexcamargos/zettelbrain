"""Automation utility for configuring LLM ZettelBrain for Gemini CLI or Cursor IDE.

Allows switching configuration profiles seamlessly by managing .cursorrules and client settings
for Model Context Protocol (MCP) servers.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

LOCAL_WORKSPACE_DIRS = (
    "raw/articles",
    "raw/assets",
    "raw/papers",
    "raw/youtube",
    "zettelbrain/assets",
    "zettelbrain/drafts",
    "zettelbrain/literature",
    "zettelbrain/permanent",
    "zettelbrain/presentations",
    "zettelbrain/syntheses",
    "zettelbrain/visual",
    "logs",
    ".state",
    ".pageindex",
)


def get_repo_root() -> Path:
    """Resolve the repository root directory.

    Returns:
        Path: The absolute path of the repository root.

    """
    return Path(__file__).resolve().parents[1]


def bootstrap_local_workspace(repo_root: Path) -> int:
    """Create ignored local workspace directories after a fresh clone.

    These directories hold source material, vault notes, logs and local state. They
    are intentionally ignored by Git, so clones need an explicit bootstrap step.
    """
    print("[-] Bootstrapping ignored local workspace directories...")

    try:
        created = []
        existing = []
        for relative_path in LOCAL_WORKSPACE_DIRS:
            path = repo_root / relative_path
            if path.exists():
                existing.append(relative_path)
                continue
            path.mkdir(parents=True, exist_ok=True)
            created.append(relative_path)

        if created:
            print("[+] Created directories:")
            for relative_path in created:
                print(f"    - {relative_path}/")
        else:
            print("[~] No directories needed creation.")

        if existing:
            print(f"[~] Already present: {len(existing)} directories.")

        print("\n[OK] Local workspace bootstrap completed successfully!")
        return 0

    except OSError as exc:
        print(f"[ERROR] Failed to bootstrap local workspace: {exc}", file=sys.stderr)
        return 1


def configure_gemini(repo_root: Path) -> int:
    """Configure settings for the Gemini CLI client.

    Creates the .gemini directory and settings.json if missing, syncs all skills
    from the root skills/ folder into .gemini/skills/, and deactivates Cursor rules
    (.cursorrules) to avoid configuration conflicts.

    Args:
        repo_root: The root path of the repository.

    Returns:
        int: The exit code (0 for success, 1 for failure).

    """
    print("[-] Configuring the Gemini CLI environment...")

    try:
        # Ensure .gemini/settings.json exists
        gemini_dir = repo_root / ".gemini"
        gemini_dir.mkdir(parents=True, exist_ok=True)
        settings_file = gemini_dir / "settings.json"

        default_settings = {
            "mcpServers": {
                "ZettelBrain": {
                    "command": "uv",
                    "args": ["run", "src/mcp/server.py"],
                    "timeout": 600000,
                }
            }
        }

        if not settings_file.exists():
            settings_file.write_text(
                json.dumps(default_settings, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"[+] Configuration file created at: {settings_file.relative_to(repo_root)}")
        else:
            print(
                f"[~] Configuration file already exists at: {settings_file.relative_to(repo_root)}"
            )

        # Sync skills from root to .gemini/skills
        source_skills_dir = repo_root / "skills"
        gemini_skills_dir = gemini_dir / "skills"
        gemini_skills_dir.mkdir(parents=True, exist_ok=True)

        if source_skills_dir.exists():
            source_files = list(source_skills_dir.glob("*.md"))
            copied_count = 0
            for src_file in source_files:
                dest_file = gemini_skills_dir / src_file.name
                dest_file.write_text(src_file.read_text(encoding="utf-8"), encoding="utf-8")
                copied_count += 1
            print(
                "[+] Synchronized "
                f"{copied_count} skills to {gemini_skills_dir.relative_to(repo_root)}"
            )

            # Clean up orphan skills
            dest_names = {f.name for f in source_files}
            removed_count = 0
            for existing_file in gemini_skills_dir.glob("*.md"):
                if existing_file.name not in dest_names:
                    existing_file.unlink()
                    removed_count += 1
            if removed_count > 0:
                print(
                    "[+] Removed "
                    f"{removed_count} orphan skills from {gemini_skills_dir.relative_to(repo_root)}"
                )
        else:
            print("[!] Warning: master skills folder not found at the project root.")

        # Deactivate .cursorrules to prevent agent confusion in Gemini CLI
        cursorrules = repo_root / ".cursorrules"
        if cursorrules.exists():
            cursorrules_bak = repo_root / ".cursorrules.bak"
            if cursorrules_bak.exists():
                cursorrules_bak.unlink()
            cursorrules.rename(cursorrules_bak)
            print(f"[+] Cursor rules disabled: {cursorrules.name} -> {cursorrules_bak.name}")

        print("\n[OK] Gemini CLI environment configured successfully!")
        print("    -> Run your Gemini CLI agent normally.")
        return 0

    except OSError as exc:
        print(f"[ERROR] Failed to configure the Gemini CLI environment: {exc}", file=sys.stderr)
        return 1


def configure_cursor(repo_root: Path) -> int:
    """Configure settings for the Cursor IDE client.

    Creates the .cursor directory and mcp.json if missing, and compiles the
    master rules (ZETTELBRAIN.md) along with all workflows from the skills/ folder
    into a single .cursorrules file.

    Args:
        repo_root: The root path of the repository.

    Returns:
        int: The exit code (0 for success, 1 for failure).

    """
    print("[-] Configuring the Cursor IDE environment...")

    try:
        # Ensure .cursor/mcp.json exists
        cursor_dir = repo_root / ".cursor"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        mcp_file = cursor_dir / "mcp.json"

        default_mcp = {
            "mcpServers": {
                "ZettelBrain": {
                    "command": "uv",
                    "args": ["run", "src/mcp/server.py"],
                }
            }
        }

        if not mcp_file.exists():
            mcp_file.write_text(
                json.dumps(default_mcp, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"[+] Cursor MCP file created at: {mcp_file.relative_to(repo_root)}")
        else:
            print(f"[~] Cursor MCP file already exists at: {mcp_file.relative_to(repo_root)}")

        # Compile ZETTELBRAIN.md + all files in skills/ into .cursorrules
        master_rules = repo_root / "ZETTELBRAIN.md"
        cursorrules = repo_root / ".cursorrules"
        cursorrules_bak = repo_root / ".cursorrules.bak"

        # If backup exists, we can delete it since we are creating a new .cursorrules
        if cursorrules_bak.exists():
            cursorrules_bak.unlink()

        if master_rules.exists():
            rules_content = master_rules.read_text(encoding="utf-8")

            # Collect and append skills
            source_skills_dir = repo_root / "skills"
            skills_content = []
            if source_skills_dir.exists():
                for src_file in sorted(source_skills_dir.glob("*.md")):
                    content = src_file.read_text(encoding="utf-8")
                    skills_content.append(content)

            full_content = rules_content
            if skills_content:
                full_content += "\n\n---\n\n# Integrated Skills Workflow\n\n"
                full_content += "\n\n---\n\n".join(skills_content)

            cursorrules.write_text(full_content, encoding="utf-8")
            print(
                "[+] Rules compiled successfully: "
                f"{master_rules.name} + skills/ -> {cursorrules.name}"
            )
        else:
            print(
                "[!] Warning: ZETTELBRAIN.md was not found at the project root. "
                "Could not generate Cursor rules."
            )

        print("\n[OK] Cursor IDE environment configured successfully!")
        print("    -> Open Cursor and configure MCP in Cursor Settings > Features > MCP.")
        print(f"       Use {mcp_file.relative_to(repo_root)} as a reference.")
        return 0

    except OSError as exc:
        print(f"[ERROR] Failed to configure the Cursor environment: {exc}", file=sys.stderr)
        return 1


def clean_environment(repo_root: Path) -> int:
    """Remove all client-specific configurations and rules files.

    Recursively deletes the .gemini and .cursor folders, and deletes the
    .cursorrules and .cursorrules.bak files from the repository root.

    Args:
        repo_root: The root path of the repository.

    Returns:
        int: The exit code (0 for success, 1 for failure).

    """
    print("[-] Removing tool links and configuration files...")

    gemini_dir = repo_root / ".gemini"
    cursor_dir = repo_root / ".cursor"
    cursorrules = repo_root / ".cursorrules"
    cursorrules_bak = repo_root / ".cursorrules.bak"

    try:
        cleaned = []

        # Delete .gemini directory
        if gemini_dir.exists():
            shutil.rmtree(gemini_dir)
            cleaned.append(f"{gemini_dir.name}/")

        # Delete .cursor directory
        if cursor_dir.exists():
            shutil.rmtree(cursor_dir)
            cleaned.append(f"{cursor_dir.name}/")

        # Delete .cursorrules
        if cursorrules.exists():
            cursorrules.unlink()
            cleaned.append(cursorrules.name)

        # Delete .cursorrules.bak
        if cursorrules_bak.exists():
            cursorrules_bak.unlink()
            cleaned.append(cursorrules_bak.name)

        if cleaned:
            print(f"[+] Successfully removed: {', '.join(cleaned)}")
        else:
            print("[~] No configuration files or folders were found to remove.")

        print("\n[OK] Directory cleaned successfully and detached from tool links!")
        return 0

    except OSError as exc:
        print(f"[ERROR] Failed to clean the environment: {exc}", file=sys.stderr)
        return 1


def main() -> None:
    """Entry point for the setup utility.

    Parses command line arguments and triggers corresponding client configurations.

    Returns:
        None

    """
    repo_root = get_repo_root()
    args = sys.argv[1:]

    if not args:
        print("Erro: Nenhum provedor especificado.", file=sys.stderr)
        print("Uso: uv run install [bootstrap|local|gemini|cursor|clean]", file=sys.stderr)
        sys.exit(1)

    provider = args[0].lower().strip()
    if provider in ("bootstrap", "local"):
        sys.exit(bootstrap_local_workspace(repo_root))
    elif provider == "gemini":
        sys.exit(configure_gemini(repo_root))
    elif provider == "cursor":
        sys.exit(configure_cursor(repo_root))
    elif provider in ("clean", "uninstall"):
        sys.exit(clean_environment(repo_root))
    else:
        print(f"Erro: Provedor '{provider}' desconhecido.", file=sys.stderr)
        print("Uso: uv run install [bootstrap|local|gemini|cursor|clean]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
