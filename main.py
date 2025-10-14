from utils import Folder
from colors import Colors, all_colors

from os.path import dirname, join, exists
from time import sleep
from random import choice
from sys import exit as sysexit

PATH = dirname(__file__)
PATH_TO_RULES = join(PATH, "rules.txt")

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
    string = ""

    for path, backup_path in zip(paths, backup_paths):
        string += f"{choice(all_colors)}{path}{Colors.RESET} -> {choice(all_colors)}{backup_path}{Colors.RESET}\n"
    
    return string

def split_backup_key(line: str) -> list[str, str]:
    src, dst = map(str.strip, line.split("->"))

    return [src, dst]

def get_rules() -> tuple[list[str], list[str]]:
    paths, backup_paths = [], []

    for line in get_rules_content():
        src, dst = split_backup_key(line)

        paths.append(src)
        backup_paths.append(dst)

    return paths, backup_paths

def copy_files(paths: list[str], backup_paths: list[str]) -> None:
    count = 0

    try:
        error_buf = open("errors.txt", "w")
    except OSError:
        error_buf = None

    while count < len(paths):
        path = paths[count]
        backup_path = backup_paths[count]

        try:
            folder = Folder(path)
            copied_files, _ = folder.copy_to(backup_path)
        except (OSError, ValueError) as e:
            print(f"{Colors.BRIGHT_RED}An error occurred while copying.{Colors.RESET}\n{e}")

            if error_buf:
                error_buf.write(f"Error occurred at iteration {count}\n{e}\n")
            
            continue
        finally:
            count += 1

        print(f"Copied {choice(all_colors)}{len(copied_files)} files{Colors.RESET} from {choice(all_colors)}{folder.path}{Colors.RESET} to {choice(all_colors)}{backup_path}{Colors.RESET}.")

    if error_buf:
        error_buf.close()

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

if __name__ == "__main__":
    main()
