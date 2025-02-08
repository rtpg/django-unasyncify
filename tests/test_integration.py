import pytest

from pathlib import Path
import shutil
import tempfile

from django_unasyncify.cmd import main as cli_main
from django_unasyncify.config import Config


original_sample_project = Path(__file__).parent / "proj"


@pytest.fixture
def sample_project():
    """
    A copy of the sample project, in
    a temporary directory

    yields the Path of the project
    """
    with tempfile.TemporaryDirectory() as dirpath:
        projpath = dirpath + "/proj"
        shutil.copytree(src=original_sample_project, dst=projpath)
        yield Path(projpath)


def assert_matching_file_contents(left: Path, right: Path):
    try:
        with left.open("r") as f:
            left_contents = f.read()
    except FileNotFoundError:
        raise ValueError("left file not found")
    try:
        with right.open("r") as f:
            right_contents = f.read()
    except FileNotFoundError:
        raise ValueError("right file not found")
    assert left_contents == right_contents


def test_command_run_itself(sample_project):
    """
    This is a huge integration test that tries
    to capture everything around the edges.

    Note[Raphael]: Once I figure out what the right
    patterns are here I'll try to make more of these.
    """

    # let's run django-unasyncify on the project
    cli_main(Config.from_project_path(sample_project))

    # let's confirm that our CLI did what we expect
    # first, we should have our codegen output
    assert_matching_file_contents(
        sample_project / "unasync_utils.py",
        Path(__file__).parent / ".." / "src" / "django_unasyncify" / "_codegen.py",
    )

    # then, we should also have transformed our files into
    # what we expect
    assert_matching_file_contents(
        sample_project / "one.py", sample_project / "one.py.expected"
    )


def test_sample_project_config_loading():
    config = Config.from_project_path(original_sample_project)
    assert config == Config(
        project_base=(original_sample_project),
        paths_to_visit=[str(original_sample_project)],
        unasync_helpers_path="unasync_utils.py",
        unasync_helpers_import_path="unasync_utils",
    )

    assert (
        config.codegen_template_path()
        == Path(__file__).parent / "proj" / "unasync_utils.py"
    )
