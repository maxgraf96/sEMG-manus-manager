import os
from pathlib import Path


def _load_dotenv(dotenv_path):
    env_values = {}
    if not dotenv_path.exists():
        return env_values

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        env_values[key] = value

    return env_values


BASE_DIR = Path(__file__).resolve().parent
DOTENV_VALUES = _load_dotenv(BASE_DIR / ".env")


def _get_env(name, default):
    return os.environ.get(name) or DOTENV_VALUES.get(name) or default


def _expand_path(path_value):
    expanded = Path(path_value).expanduser()
    if expanded.is_absolute():
        return expanded
    return (BASE_DIR / expanded).resolve()


BG_COLOUR_LIGHT = "white"
FG_COLOUR_LIGHT = "black"
BG_COLOUR_DARK = "black"
FG_COLOUR_DARK = "white"

FONT = "Helvetica"

USER_DATA_DIR = _expand_path(_get_env("USER_DATA_DIR", "user_data"))
VISUALISER_PATH = str(
    _expand_path(
        _get_env("VISUALISER_PATH", "E:/Pycharm Projects 10/sEMG-manus-hand-renderer")
    )
)


def get_user_data_path(*parts):
    return str(USER_DATA_DIR.joinpath(*parts))


def user_data_dir_exists():
    return USER_DATA_DIR.exists()


def ensure_user_data_dir():
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return str(USER_DATA_DIR)
