from argparse import ArgumentParser

from django_unasyncify.codemod import UnasyncifyMethodCommand
from .config import load_config

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


def main():
    args = parser.parse_args()
    config = load_config(args.project)

    codemod = UnasyncifyMethodCommand(config=config, context=CodemodContext())

    print("About to run transform...")
    files_to_visit = gather_files(config.paths_to_visit)
    parallel_exec_transform_with_prettyprint(
        codemod, files_to_visit, repo_root=str(config.project_base)
    )
    print("Done.")
