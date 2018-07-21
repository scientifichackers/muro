"""
A worker that runs on a Micropython board.

The data within "{{" & "}}" is populated by a Jinja2 template engine.
"""

import uos as os
import uhashlib as hashlib


def get_parent_path(path: str) -> str:
    return "/".join(path.split("/")[:-1])


def did_it_change(file_to_check: str, file_hash: bytes) -> int:
    try:
        with open(file_to_check, "rb") as fp:
            file_data = fp.read()
    except OSError:
        return 1
    else:
        return int(hashlib.sha1(file_data).digest() != file_hash)


def mkdir_p(dir: str) -> None:
    if dir:
        mkdir_p(get_parent_path(dir))
        try:
            os.mkdir(dir)
        except OSError:
            pass
    else:
        return


def rm_r(dir: str) -> None:
    os.chdir(dir)
    for f in os.listdir():
        try:
            os.remove(f)
        except OSError:
            pass
    for f in os.listdir():
        rm_r(f)
    os.chdir("..")
    os.rmdir(dir)


def rmdir_if_not_required(dir: str) -> None:
    for req in required_dirs:
        if req.startswith(dir):
            return
    try:
        rm_r(dir)
    except OSError:
        pass


def rm_if_not_required(file: str) -> None:
    if file not in required_files:
        try:
            os.remove(file)
        except OSError:
            pass


def remove_unwanted(dir_or_file: str):
    # remove the leading slashes, since the whole system works on relative paths.
    if dir_or_file.startswith("/"):
        dir_or_file = dir_or_file[1:]
    try:
        # if its a directory, then it should provide some children.
        children = os.listdir(dir_or_file)
    except OSError:
        # probably a file, remove if not required.
        rm_if_not_required(dir_or_file)
    else:
        # probably a directory, remove if not required.
        rmdir_if_not_required(dir_or_file)

        # queue the children to be inspected in next iteration (with correct path).
        for child in children:
            remove_unwanted(dir_or_file + "/" + child)  # pass the full path.


# gather required files / dirs.
required_files = {{required_files}}
required_files.add("boot.py")  # avoid fucking up the boot.py.
required_dirs = {{required_dirs}}


# Remove unwanted files / dirs.
remove_unwanted(os.getcwd())

# create necessary dirs.
for dir in required_dirs:
    mkdir_p(dir)

# inform everyone which files have changed.
for file_and_hash in {{files_to_check_for_change_with_hash}}:
    print(did_it_change(*file_and_hash), end=" ")
