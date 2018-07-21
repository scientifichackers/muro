"""A bunch of command-line utils to help you do the chores."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from jinja2 import Template

import click
import mpy_cross
import hashlib
from typing import List

COMPILE_DIR = Path.cwd() / ".compiled"
AUTO_START_PATH = Path.home() / ".config" / "autostart" / "muro.desktop"
THIS_DIR = Path(__file__).parent
MPY_DIR = THIS_DIR / "micropython"
CLI_WORKER_TEMPLATE = THIS_DIR / "cli_worker.py"
COMMON_DIR = THIS_DIR / "common"
PROJECT_FILES = [*MPY_DIR.rglob("*.py"), *COMMON_DIR.rglob("*.py")]

AUTO_START_FILE = f"""\
#!/usr/bin/env xdg-open
[Desktop Entry]
Type=Application
Name=muro
Description=My short description for my project.
Exec={subprocess.check_output(["which", "python"], encoding="utf-8").strip()} -m muro.cli run\
"""


def clean_compiled():
    shutil.rmtree(COMPILE_DIR, ignore_errors=True)


clean_compiled()


def run_ampy_cmd(port: str, cmd: list) -> str:
    return subprocess.check_output(
        ["/usr/bin/env", "ampy", "-p", port] + cmd, encoding="utf-8"
    )


def run_code_on_board(port: str, code_as_str: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        fp.write(code_as_str)
        fp.flush()
        return run_ampy_cmd(port, ["run", fp.name])


def save_code_on_board(port: str, code_as_str: str, file_name_on_board: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        fp.write(code_as_str)
        fp.flush()
        return run_ampy_cmd(port, ["put", fp.name, file_name_on_board])


def cross_compile(input_path: Path) -> Path:
    output_path = COMPILE_DIR / (".".join(input_path.name.split(".")[:-1]) + ".mpy")
    mpy_cross_process = mpy_cross.run(input_path, "-o", output_path)

    if mpy_cross_process.wait() == 0:
        return output_path
    else:
        exit("Something bad happened!")


class File:
    def __init__(self, file_path: Path):
        self.path = file_path
        self.path_compiled = cross_compile(file_path)

        with open(self.path_compiled, "rb") as fp:
            self.hash = hashlib.sha1(fp.read()).digest()

        self.path_on_board = str(
            file_path.relative_to(THIS_DIR.parent).with_suffix(
                self.path_compiled.suffix
            )
        )
        self.dir_path_on_board = str(file_path.parent.relative_to(THIS_DIR.parent))

    def __repr__(self):
        return f"<File path: {self.path}>"


def create_mpy_code(project_files: List[File]) -> str:
    with open(CLI_WORKER_TEMPLATE, "r") as fp:
        return Template(fp.read()).render(
            required_dirs={file.dir_path_on_board for file in project_files},
            required_files={file.path_on_board for file in project_files},
            files_to_check_for_change_with_hash=[
                (file.path_on_board, file.hash) for file in project_files
            ],
        )


@click.group()
def cli():
    pass


@click.command(short_help="Install muro")
@click.option(
    "--port", default="/dev/ttyUSB0", help="USB serial port for connected board"
)
@click.option(
    "--force", is_flag=True, help="Transfer files whether they have changed or not."
)
def install(port, force):
    """
    Puts the required code for muro to function
    on the MicroPython chip, using "ampy".

    By default, it uses /dev/ttyUSB0 as the port.

    It also uses the `mpy-cross` utility to cross compile the files,
    which helps when the files are big.

    It also configures the application to be run at boot,
    using the `muro run` command.

    Note:
        By default, it only transfers the files that have changed.

    Warning:
        Removes the files on the board, that are not needed.
        (except "boot.py")
    """

    try:
        COMPILE_DIR.mkdir()

        project_files = [File(file_path) for file_path in PROJECT_FILES]
        mpy_code = create_mpy_code(project_files)

        print(f'Preparing board @ "{port}"...')
        code_output = run_code_on_board(port, mpy_code)
        code_output = map(int, code_output.strip().split())

        for file, did_change in zip(project_files, code_output):
            if int(did_change) or force:
                print(f"Transferring {file.path}...")
                run_ampy_cmd(port, ["put", file.path_compiled, file.path_on_board])
    finally:
        clean_compiled()

    print('Configuring "main.py"...')
    save_code_on_board(
        port, "from muro.micropython.muro import mainloop\nmainloop()", "main.py"
    )

    if click.confirm("Add `muro run` to auto-start?", default=False):
        print(f"Adding to auto-start... ({AUTO_START_PATH})")

        if not AUTO_START_PATH.parent.exists():
            AUTO_START_PATH.parent.mkdir(parents=True)

        with open(AUTO_START_PATH, "w") as f:
            f.write(AUTO_START_FILE)

    print("Done!")


@click.command()
def run():
    """Run muro"""

    from muro.muro import mainloop

    mainloop()


###########################################
# Add your own command-line utils here.   #
# For more information on how to do that, #
# check out the Click documentation :     #
#   http://click.pocoo.org                #
###########################################


cli.add_command(install)
cli.add_command(run)

if __name__ == "__main__":
    cli()
