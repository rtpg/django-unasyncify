from dataclasses import dataclass, field

from pathlib import Path
from textwrap import dedent
import tomllib


@dataclass
class Config:
    project_base: Path = Path(".")
    paths_to_visit: list[str] = field(default_factory=lambda: [])
    attribute_renames: dict[str, str] = field(default_factory=lambda: {})
    # XXX maybe rename this one
    unasync_helpers_import_path: str = "MISSING_IMPORT_PATH"
    # XXX rename this one as well, and not include the defaults here
    unasync_helpers_path: str = "MISSING"

    def __post_init__(self):
        # this IS_ASYNC rename is present even when we explicitly don't include
        # it. I have not come up with a good situation to not do this.
        self.attribute_renames.setdefault("IS_ASYNC", "False")

    @classmethod
    def from_project_path(cls, path) -> "Config":
        return load_config_from_project_path(path)

    def codegen_template_path(self) -> Path:
        return self.project_base / self.unasync_helpers_path


def load_config_from_project_path(project_path: str) -> Config:
    project_base = Path(project_path)
    pyproject_location = project_base / "pyproject.toml"
    try:
        with pyproject_location.open("rb") as pyproject_file:
            pyproject = tomllib.load(pyproject_file)
    except FileNotFoundError:
        raise IOError(
            f"Could not find a pyproject.toml file for the project (at {project_path})"
        )

    try:
        unasyncify_config = pyproject["tool"]["django_unasyncify"]
    except KeyError:
        raise ValueError(
            dedent(
                """
        Could not find the [tool.django_unasyncify] config section
        inside the pyproject.toml file of your project. Is it missing?
        """
            )
        )

    paths_to_visit_config = unasyncify_config.get("paths_to_visit", ["."])
    paths_to_visit = [str(project_base / path) for path in paths_to_visit_config]

    return Config(
        project_base=project_base,
        paths_to_visit=paths_to_visit,
        attribute_renames=unasyncify_config.get("attribute_renames", {}),
        unasync_helpers_path=unasyncify_config["unasync_helpers_path"],
        unasync_helpers_import_path=unasyncify_config["unasync_helpers_import_path"],
    )
