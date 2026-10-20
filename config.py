from pathlib import Path
import platform
import json
from dataclasses import dataclass, asdict

SYSTEM = platform.system()

CONFIG_PATH = {
    "Linux" : Path("~/.config/gädda/config.json").expanduser(),
    "Windows" : Path("%APPDATA%\\gädda\\config.json")
}

SEARCH_PATH = {
    "Linux" : Path("~/.local/share/Steam/steamapps/compatdata").expanduser(),
    "Windows" : Path("C:\\Program Files (x86)\\World of Warcraft")
}

FOREVER_PATH_PARENT_NAME = "_forever_"

def find_wow_install_path() -> Path | None:
    matches = [
        path
        for path in SEARCH_PATH[SYSTEM].rglob("Wow.exe")
        if path.parent.name.casefold() == FOREVER_PATH_PARENT_NAME
    ]

    if len(matches) == 1:
        return matches[0].parent
    return None


@dataclass
class Config:
    """Dataclass representing a persistent config object."""
    wow_path: Path = None
    server_address: str = None
    server_key: str = None

    @classmethod
    def load(cls):
        """Loads from config file.
        
        If the config file does not exist, create and try to populate.
        """
        config_file_path = CONFIG_PATH[SYSTEM]
        if not config_file_path.is_file():
            cls.create_default_config(config_file_path)
        data = json.loads(config_file_path.read_text())

        if not data["wow_path"]:
            path = find_wow_install_path()
            if not path:
                raise FileNotFoundError("Failed to find wow_path")
            data["wow_path"] = path

        data["wow_path"] = Path(data["wow_path"])
        if not data["wow_path"].exists():
            raise ValueError(f"Invalid wow_path: {data['wow_path']}")

        return cls(**data)

    @classmethod
    def create_default_config(cls, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)

        config = cls(
            wow_path=find_wow_install_path(),
            server_address="https://wow.klungo.dev",
            server_key="test"
        )

        data = asdict(config)
        data["wow_path"] = str(config.wow_path) if config.wow_path else None

        path.write_text(json.dumps(data, indent=2))
