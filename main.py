from pathutils import Folder, File
from colors import Colors, all_colors

from os.path import dirname, join, exists, isdir
from hashlib import sha256
from time import sleep
from random import choice
from sys import exit as sysexit

from typing import Generator, NoReturn
from io import TextIOWrapper

PATH = dirname(__file__)
PATH_TO_RULES = join(PATH, "rules.txt")
SPLIT_KEY = "->"

if not exists(PATH_TO_RULES):
    print(f"Create a rules.txt file in {PATH} before usage.")
    sysexit(1)

def get_rules_content(error_buf: TextIOWrapper) -> Generator[str, None, None] | NoReturn:
    try:
        with open(PATH_TO_RULES) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    yield line
    except OSError as e:
        print(f"Failed to open rules file.\nErr: {e}")

        if error_buf:
            error_buf.write(f"An error occurred while reading rules file.\n{e}\n")

        sysexit(1)

def get_src_dst_string(paths: list[str], backup_paths: list[str]) -> str:
    string = str()

    for path, backup_path in zip(paths, backup_paths):
        string += f"{choice(all_colors)}{path}{Colors.RESET} -> {choice(all_colors)}{backup_path}{Colors.RESET}\n"
    
    return string

def split_backup_key(line: str) -> list[str, str] | None:
    if SPLIT_KEY not in line:
        return None

    src, dst = map(str.strip, line.split(SPLIT_KEY, 1))

    if not isdir(src):
        return None

    return [src, dst]

def get_rules(error_buf: TextIOWrapper) -> tuple[list[str], list[str]]:
    paths, backup_paths = [], []

    for line in get_rules_content(error_buf):
        result = split_backup_key(line)

        if result is None:
            print(f"Ignoring invalid line {Colors.BRIGHT_RED}'{line}'{Colors.RESET}")
            continue
        
        src, dst = result
        
        if not exists(src):
            print(f"Skipping line {Colors.BRIGHT_RED}'{line}'{Colors.RESET} as source does not exist")
            continue
        
        paths.append(src)
        backup_paths.append(dst)

    return paths, backup_paths

def verify_hash(original: list[File], other: list[File], error_buf: TextIOWrapper) -> bool:
    if len(original) != len(other):
        print("Backup copy does not match item count")
        return False
    
    matches = []
    
    for file, other_file in zip(original, other):
        print(f"Verifying hash of {choice(all_colors)}{file.path}{Colors.RESET} with {choice(all_colors)}{other_file.path}{Colors.RESET}")
        try:
            file_hash = sha256(file.read("rb")).hexdigest()
            other_file_hash = sha256(other_file.read("rb")).hexdigest()

            matches.append(file_hash == other_file_hash)
        except OSError as e:
            print(f"{Colors.BRIGHT_RED}Failed to verify hash of {file.path} with {other_file.path}\nErr: {e}{Colors.RESET}")

            if error_buf:
                error_buf.write(f"An error occurred during hash verification.\n{e}\n")

    return all(matches)

def copy_files(paths: list[str], backup_paths: list[str], error_buf: TextIOWrapper) -> list[tuple[list[File], list[File]]]:
    count = 0
    original_files, destination_files = [], []

    while count < len(paths):
        path = paths[count]
        backup_path = backup_paths[count]

        try:
            orig_folder = Folder(path)
            dst, src = orig_folder.copy_to(backup_path)

            original_files.extend(src)
            destination_files.extend(dst)

            print(f"Copied {choice(all_colors)}{len(dst)} files{Colors.RESET} from {choice(all_colors)}{orig_folder.path}{Colors.RESET} to {choice(all_colors)}{backup_path}{Colors.RESET}.")
        except (OSError, ValueError) as e:
            print(f"{Colors.BRIGHT_RED}An error occurred while copying.{Colors.RESET}\n{e}")

            if error_buf:
                error_buf.write(f"Error occurred while copying file {path} to {backup_path} at iteration {count}\n{e}\n")
        finally:
            count += 1

    return destination_files, original_files

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
    try:
        output = input(prompt)
    except KeyboardInterrupt:
        sysexit(0)
    
    check_input(output)

def main() -> None:
    try:
        error_buf = open("errors.txt", "w")
    except OSError as e:
        print(f"{Colors.BRIGHT_RED}Can't open error buffer due to error.\n{e}")
        error_buf = None
    
    paths, backup_paths = get_rules(error_buf)
    print(f"Will copy and verify hash:\n{get_src_dst_string(paths, backup_paths)}")
    ask("Proceed? (y/N): ")

    destination_files, original_files = copy_files(paths, backup_paths, error_buf)
    print("Verifying hashes...")
    sleep(0.5)

    hashes_match = verify_hash(original_files, destination_files, error_buf)
    if hashes_match:
        print("Hashes match!")
    
if __name__ == "__main__":
    main()
