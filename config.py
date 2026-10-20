from pathlib import Path
import json
import logging
from dataclasses import dataclass, asdict
import os

from globals import SYSTEM, FOREVER_DIR, SERVER_ADDRESS, DATA_FILE_NAME

logger = logging.getLogger(__name__)

def is_wow_install(path: Path) -> bool:
    return path.is_dir() and (
        (path / "Wow.exe").is_file()
        or (path / "WowB.exe").is_file()
    )

def find_wow_install_path() -> Path | None:
    candidates = []

    if SYSTEM == "Windows":
        for base in (
            os.environ.get("ProgramFiles(x86)"),
            os.environ.get("ProgramFiles"),
        ):
            if base:
                candidates.append(
                    Path(base) / "World of Warcraft" / FOREVER_DIR
                )

    elif SYSTEM == "Linux":
        home = Path.home()

        steam_roots = [
            home / ".local/share/Steam/steamapps/compatdata",
            home / ".steam/steam/steamapps/compatdata",
        ]

        for steam_root in steam_roots:
            candidates.extend(
                Path(p) for p in steam_root.glob(
                    "*/pfx/drive_c/Program Files (x86)"
                    f"/World of Warcraft/{FOREVER_DIR}"
                )
            )

    matches = sorted({
        path.resolve()
        for path in candidates
        if is_wow_install(path)
    })

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple WoW installations found: {matches}. "
            "Set wow_path manually in config.json."
        )

    return matches[0] if matches else None

def get_config_path() -> Path:
    if SYSTEM == "Windows":
        base = Path(os.environ["APPDATA"])
    elif SYSTEM == "Linux":
        base = Path(
            os.environ.get("XDG_CONFIG_HOME", "~/.config")
        ).expanduser()
    else:
        raise OSError(f"Unsupported platform: {SYSTEM}")

    return base / "gädda" / "config.json"

@dataclass
class Config:
    """Dataclass representing a persistent config object."""
    wow_path: Path | None = None
    server_address: str = SERVER_ADDRESS
    server_key: str | None = None

    @classmethod
    def load(cls):
        """Load the config, creating it and detecting the WoW path if needed."""
        path = get_config_path()
        logger.info("Loading configuration from %s", path)
        if not path.is_file():
            cls.create_default_config(path)
        data = json.loads(path.read_text())

        configured_path = data.get("wow_path")
        if configured_path:
            wow_path = Path(configured_path)
        else:
            wow_path = find_wow_install_path()
            if wow_path is None:
                raise FileNotFoundError(
                    "Unable to find WoW installation. "
                    f"Set wow_path in {path}"
                )
            data["wow_path"] = str(wow_path)
            path.write_text(json.dumps(data, indent=2))

        if not is_wow_install(wow_path):
            raise ValueError(f"Invalid WoW path: {wow_path}")

        data["wow_path"] = wow_path
        config = cls(**data)
        logger.info("Configuration loaded successfully")
        return config

    @classmethod
    def create_default_config(cls, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)

        config = cls()
        path.write_text(json.dumps(asdict(config),indent=2))
        logger.info("Created default configuration at %s", path)

    @property
    def account_dir(self) -> Path:
        if self.wow_path is None:
            raise ValueError("WoW path not configured")

        return self.wow_path / "WTF" / "Account"

    @property
    def data_files(self) -> list[Path]:
        return list(
            self.account_dir.glob(
                f"*/SavedVariables/{DATA_FILE_NAME}"
            )
        )
