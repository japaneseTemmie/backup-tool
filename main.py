from os.path import join, dirname, relpath, isdir, exists
from os import makedirs, listdir
from shutil import copy2
from time import sleep
from sys import exit as sysexit
from re import compile

PATH = dirname(__file__)
PATH_TO_RULES = join(PATH, "rules.txt")
EXTENSION_PATTERN = compile(r"\[(\..+)?\]")

def get_rules_content():
    with open(PATH_TO_RULES) as f:
        lines = f.readlines()

    for line in lines:
        yield line

def split_backup_key(line: str) -> list[str, str, str | None]:
    ext_match = EXTENSION_PATTERN.search(line.strip())
    ext = ext_match.group(1) if ext_match else None

    line = EXTENSION_PATTERN.sub("", line)

    src, dst = map(str.strip, line.split("->"))

    return [src, dst, ext]

def get_rules() -> tuple[list[str], list[str], list[str | None]]:
    paths, backup_paths, extensions = [], [], []

    for line in get_rules_content():
        src, dst, ext = split_backup_key(line)

        paths.append(src)
        backup_paths.append(dst)
        extensions.append(ext)

    return paths, backup_paths, extensions

def get_files(path: str, extension: str | None) -> list[str] | list:
    stack = []
    
    if exists(path):
        all_files = listdir(path)
    else:
        print(f"Directory {path} does not exist.")
        return stack

    for file in all_files:
        full_fp = join(path, file)

        if not isdir(full_fp):
            
            if extension is None or full_fp.endswith(extension):
                stack.append(full_fp)
        else:
            other_files = get_files(full_fp, extension)
            if other_files:
                stack.extend(other_files)

    return stack

def copy_files(paths: list[str], backup_paths: list[str], extensions: list[str | None]) -> None:
    count = 0
    while count < len(paths):
        path = paths[count]
        backup_path = backup_paths[count]
        extension = extensions[count]

        all_files = get_files(path, extension)

        for file in all_files:
            relative_path = relpath(file, path)
            dest = join(backup_path, relative_path)
            folders = dirname(dest)

            try:
                if not exists(folders):
                    makedirs(folders, exist_ok=True)
                    print(f"Made directory {folders}")

                copy2(file, dest)
                print(f"Copied file from {file} to {dest}")
            except OSError as e:
                print(f"An error occured while copying file {file} to {dest}.\n{e}")
                sysexit(0)
        count += 1

def check_input(string: str) -> None:
    match string.lower():
        case "y":
            print("Proceeding..")
            sleep(1)
        case "n":
            sysexit(0)
        case _:
            sysexit(0)

def ask(prompt: str) -> None:
    output = input(prompt)
    check_input(output)

def main() -> None:
    paths, backup_paths, extensions = get_rules()
    print(f"Will copy contents from {"\n".join(paths)} to {"\n".join(backup_paths)}")
    ask("Proceed? (y/N): ")

    copy_files(paths, backup_paths, extensions)

if __name__ == "__main__":
    main()