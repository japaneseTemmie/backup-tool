from utils import Folder
from colors import Colors, all_colors

from os.path import dirname, join, exists
from time import sleep
from random import choice
from sys import exit as sysexit

PATH = dirname(__file__)
PATH_TO_RULES = join(PATH, "rules.txt")
SPLIT_KEY = "->"
try:
    ERROR_BUF = open("errors.txt", "w")
except OSError:
    ERROR_BUF = None

if not exists(PATH_TO_RULES):
    print(f"Create a rules.txt file in {PATH} before usage.")
    sysexit(1)

def get_rules_content():
    with open(PATH_TO_RULES) as f:
        lines = f.readlines()

    for line in lines:
        if line.strip() and not line.startswith("#"):
            yield line

def get_src_dst_string(paths: list[str], backup_paths: list[str]) -> str:
    string = str()

    for path, backup_path in zip(paths, backup_paths):
        string += f"{choice(all_colors)}{path}{Colors.RESET} -> {choice(all_colors)}{backup_path}{Colors.RESET}\n"
    
    return string

def split_backup_key(line: str) -> list[str | None, str | None]:
    if SPLIT_KEY not in line:
        return [None, None]

    src, dst = map(str.strip, line.split(SPLIT_KEY, 1))

    return [src, dst]

def get_rules() -> tuple[list[str], list[str]]:
    paths, backup_paths = [], []

    for line in get_rules_content():
        src, dst = split_backup_key(line)

        if src is not None and dst is not None:
            paths.append(src)
            backup_paths.append(dst)
        else:
            print(f"Ignoring invalid line {Colors.BRIGHT_RED}'{line}'{Colors.RESET}")

    return paths, backup_paths

def copy_files(paths: list[str], backup_paths: list[str]) -> list[str]:
    count = 0

    while count < len(paths):
        path = paths[count]
        backup_path = backup_paths[count]

        try:
            orig_folder = Folder(path)
            copied_files, _ = orig_folder.copy_to(backup_path)

            print(f"Copied {choice(all_colors)}{len(copied_files)} files{Colors.RESET} from {choice(all_colors)}{orig_folder.path}{Colors.RESET} to {choice(all_colors)}{backup_path}{Colors.RESET}.")
        except (OSError, ValueError) as e:
            print(f"{Colors.BRIGHT_RED}An error occurred while copying.{Colors.RESET}\n{e}")

            if ERROR_BUF:
                ERROR_BUF.write(f"Error occurred while copying file {path} to {backup_path} at iteration {count}\n{e}\n")
            
            continue
        finally:
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
    paths, backup_paths = get_rules()
    print(f"Will copy:\n{get_src_dst_string(paths, backup_paths)}")
    ask("Proceed? (y/N): ")

    copy_files(paths, backup_paths)

    if ERROR_BUF:
        ERROR_BUF.close()

if __name__ == "__main__":
    main()
