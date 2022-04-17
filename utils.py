from pathlib import Path


def str_to_path(path: str) -> Path:
    return Path(path.replace(" ", "\\ ")).resolve()


def path_to_str(path: Path) -> str:
    return str(Path(path).resolve())


def format_str_path(path: str) -> str:
    return path_to_str(str_to_path(path))
