from pathlib import Path
from shutil import copyfile


def ensure_codegen_template(target_location):
    """
    Insert the codegen template to where it's needed
    """
    codegen_location = Path(__file__).parent / "_codegen.py"
    copyfile(src=codegen_location, dst=target_location)
