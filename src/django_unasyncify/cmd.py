from argparse import ArgumentParser

from django_unasyncify.codemod import UnasyncifyMethodCommand
from django_unasyncify.scaffolding import ensure_codegen_template
from .config import Config

from libcst.codemod import (
    CodemodContext,
    parallel_exec_transform_with_prettyprint,
    gather_files,
)

parser = ArgumentParser(
    prog="django-unasyncify",
    description="Unasyncify some of your code",
)

parser.add_argument("-p", "--project", required=True)


def main(config: Config | None = None):
    """
    Run django-unasyncify

    If config is not provided, parse from the command line
    """
    if not config:
        args = parser.parse_args()
        config = Config.from_project_path(args.project)

    # place the codegen template
    ensure_codegen_template(config.codegen_template_path())
    codemod = UnasyncifyMethodCommand(config=config, context=CodemodContext())

    print("About to run transform...")
    files_to_visit = gather_files(config.paths_to_visit)
    parallel_exec_transform_with_prettyprint(
        codemod, files_to_visit, repo_root=str(config.project_base)
    )
    print("Done.")
