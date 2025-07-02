from os.path import join, dirname, relpath, isdir, exists
from os import makedirs, listdir
from shutil import copy2
from time import sleep
from sys import exit as sysexit

PATH = dirname(__file__)
PATH_TO_RULES = join(PATH, "rules.txt")

PATH_TO_BACKUP_KEY = "->"

def get_rules_content():
    with open(PATH_TO_RULES) as f:
        lines = f.readlines()

    for line in lines:
        yield line

def remove_spaces_from_paths(iterable: list[str]):
    new_iterable = []
    for path in iterable:
        new_iterable.append(path.strip())

    return new_iterable

def split_backup_key(line: str):
    return remove_spaces_from_paths(line.strip().split(PATH_TO_BACKUP_KEY))

def add_paths_to_lists(paths: list[str], path_list: list, backup_paths: list):
    if paths:
        path = paths.pop(0)
        backup_path = paths.pop(0)

        path_list.append(path)
        backup_paths.append(backup_path)

def get_rules():
    paths, backup_paths = [], []

    for line in get_rules_content():
        split = split_backup_key(line)

        if len(split) == 2:
            add_paths_to_lists(split, paths, backup_paths)

    return paths, backup_paths

def get_files(path: str):
    if exists(path):
        all_files = listdir(path)
    else:
        print(f"Directory {path} does not exist.")
        return

    stack = []

    for file in all_files:
        full_fp = join(path, file)

        if not isdir(full_fp):
            stack.append(full_fp)
        else:
            other_files = get_files(full_fp)
            if other_files:
                stack.extend(other_files)

    return stack

def copy_files(paths: list, backup_paths: list):
    for path, backup_path in zip(paths, backup_paths):
        all_files = get_files(path)

        for file in all_files:
            relative_path = relpath(file, path)
            dest = join(backup_path, relative_path)
            folders = dirname(dest)

            try:
                makedirs(folders, exist_ok=True)
                print(f"Made directory at {folders}")

                copy2(file, dest)
                print(f"Copied file from {file} to {dest}")
            except OSError as e:
                print(f"An error occured while copying file {file} to {dest}.\n{e}")
                sysexit(0)

def check_input(string: str):
    match string.lower():
        case "y":
            print("Proceeding..")
            sleep(1)
        case "n":
            sysexit(0)
        case _:
            sysexit(0)

def ask(prompt: str):
    output = input(prompt)
    check_input(output)

def main() -> None:
    paths, backup_paths = get_rules()
    print(f"Will copy contents from {"\n".join(paths)} to {"\n".join(backup_paths)}")
    ask("Proceed? (y/N): ")

    copy_files(paths, backup_paths)

if __name__ == "__main__":
    main()