from dataclasses import dataclass, field

from pathlib import Path
import tomllib


@dataclass
class Config:
    project_base: Path = Path(".")
    paths_to_visit: list[str] = field(default_factory=lambda: [])
    attribute_renames: dict[str, str] = field(default_factory=lambda: {})
    # XXX maybe rename this one
    codegen_import_path: str = "MISSING_IMPORT_PATH"
    codegen_generators_path: str = "MISSING"

    def __post_init__(self):
        # this IS_ASYNC rename is present even when we explicitly don't include
        # it. I have not come up with a good situation to not do this.
        self.attribute_renames.setdefault("IS_ASYNC", "False")


    @classmethod
    def from_project_path(cls, path) -> "Config":
        return load_config_from_project_path(path)

def load_config_from_project_path(project_path: str) -> Config:
    project_base = Path(project_path)
    pyproject_location = project_base / "pyproject.toml"
    with pyproject_location.open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    # XXX error handling
    paths_to_visit_config = pyproject["tool"]["django_unasyncify"]["paths_to_visit"]
    paths_to_visit = [str(project_base / path) for path in paths_to_visit_config]
    return Config(
        project_base=project_base, paths_to_visit=paths_to_visit, attribute_renames={}
    )
