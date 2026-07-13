"""Profile command - manage named Jenkins connection profiles"""

import os
import re
import sys
from pathlib import Path
from typing import Optional

from jenkins_tools.core import Command, JenkinsConfig

_VALID_PROFILE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


class ProfileCommand(Command):
    """Manage named Jenkins connection profiles (multi-site support)"""

    def __init__(self, args=None, base_dir: Optional[Path] = None):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:]).
                  First element is the subcommand: list | use | current
            base_dir: Override for ~/.jenkins-inspector (test injection only;
                      production callers always omit this)
        """
        self.args = args or []
        self.base_dir = base_dir or JenkinsConfig.default_base_dir()

    def execute(self) -> int:
        """Execute profile command"""
        if not self.args:
            print("Error: Missing subcommand", file=sys.stderr)
            print("Usage: jenkee profile <list|use|current>", file=sys.stderr)
            return 1

        subcommand = self.args[0]
        rest = self.args[1:]

        if subcommand == "list":
            return self._list()
        elif subcommand == "use":
            return self._use(rest)
        elif subcommand == "current":
            return self._current()
        else:
            print(f"Error: Unknown profile subcommand '{subcommand}'", file=sys.stderr)
            print("Usage: jenkee profile <list|use|current>", file=sys.stderr)
            return 1

    def _list(self) -> int:
        """List all configured profiles, marking which one is active"""
        profiles_dir = self.base_dir / "profiles"
        active_name = self._active_name_hint()

        names = ["default"]
        if profiles_dir.exists():
            names += sorted(p.stem for p in profiles_dir.glob("*.env"))

        print("Available profiles:")
        for name in names:
            marker = " (active)" if name == (active_name or "default") else ""
            print(f"  {name}{marker}")
        return 0

    def _use(self, rest: list[str]) -> int:
        """Switch the persistent active profile"""
        if not rest:
            print("Error: Missing profile name", file=sys.stderr)
            print("Usage: jenkee profile use <name>", file=sys.stderr)
            print("       jenkee profile use --default", file=sys.stderr)
            return 1

        current_profile_path = self.base_dir / "current_profile"
        target = rest[0]

        if target == "--default":
            if current_profile_path.exists():
                try:
                    current_profile_path.unlink()
                except OSError as exc:
                    print(f"Error: could not remove {current_profile_path} ({exc})", file=sys.stderr)
                    print(f"Remove it manually: rm -rf {current_profile_path}", file=sys.stderr)
                    return 1
            print("✓ Switched to default profile")
            print(f"  Using: {self.base_dir / '.env'}")
            return 0

        if not _VALID_PROFILE_NAME.match(target) or target == "default":
            print(f"Error: Invalid profile name '{target}'", file=sys.stderr)
            print("Profile names may only contain letters, digits, '-' and '_', "
                  "and cannot be 'default'.", file=sys.stderr)
            return 1

        profile_path = self.base_dir / "profiles" / f"{target}.env"
        if not profile_path.exists():
            print(f"Error: Profile '{target}' not found at {profile_path}", file=sys.stderr)
            print("", file=sys.stderr)
            print("Create it first:", file=sys.stderr)
            print(f"  mkdir -p {self.base_dir / 'profiles'}", file=sys.stderr)
            print(f"  cat > {profile_path} << 'EOF'", file=sys.stderr)
            print("  JENKINS_URL=http://your-jenkins-server:8080/", file=sys.stderr)
            print("  JENKINS_USER_ID=your_email@example.com", file=sys.stderr)
            print("  JENKINS_API_TOKEN=your_api_token", file=sys.stderr)
            print("  EOF", file=sys.stderr)
            return 1

        self.base_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = current_profile_path.with_suffix(".tmp")
        tmp_path.write_text(f"{target}\n")
        os.replace(tmp_path, current_profile_path)
        print(f"✓ Switched to profile '{target}'")
        print(f"  Using: {profile_path}")
        return 0

    def _current(self) -> int:
        """Show which profile is currently active"""
        config = JenkinsConfig(base_dir=self.base_dir)  # exits with a clear error if broken

        if config.profile_name:
            source_label = {
                "env-override": "JENKEE_PROFILE / --profile",
                "persistent": "jenkee profile use",
            }.get(config.profile_source, config.profile_source)
            print(f"Profile: {config.profile_name}")
            print(f"Source: {source_label}")
            print(f"Config file: {config.profiles_dir / f'{config.profile_name}.env'}")
        else:
            print("Profile: default")
            print("Source: default (no override active)")
            print(f"Config file: {config.env_path}")

        print(f"Jenkins URL: {config.jenkins_url or '(not configured)'}")
        return 0

    def _active_name_hint(self) -> Optional[str]:
        """
        Best-effort lookup of the active profile name without validating that
        its file still exists. `list` must keep working even when the current
        selection is broken -- that's the whole point of `list` as a recovery tool.
        """
        env_override = os.getenv("JENKEE_PROFILE", "").strip()
        if env_override:
            return env_override

        current_profile_path = self.base_dir / "current_profile"
        if current_profile_path.exists():
            try:
                stored = current_profile_path.read_text().strip()
            except (OSError, UnicodeDecodeError):
                return None
            if stored:
                return stored

        return None
