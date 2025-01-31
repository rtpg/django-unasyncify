from dataclasses import dataclass

from pathlib import Path
import tomllib


@dataclass
class Config:
    project_base: Path
    paths_to_visit: list[str]


def load_config(project_path: str):
    project_base = Path(project_path)
    pyproject_location = project_base / "pyproject.toml"
    with pyproject_location.open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    # XXX error handling
    paths_to_visit_config = pyproject["tool"]["django_unasyncify"]["paths_to_visit"]
    paths_to_visit = [str(project_base / path) for path in paths_to_visit_config]
    return Config(project_base=project_base, paths_to_visit=paths_to_visit)
