from backuptool import BackupTool
from error import Error
from colors import Colors, all_colors

from argparse import ArgumentParser, Namespace
from sys import exit as sysexit
from os import sync
from time import sleep
from random import choice

def ask(prompt: str) -> bool:
    while True:
        answer = input(prompt)

        if answer in {"y", "yes"}:
            print(f"{choice(all_colors)}Proceeding...{Colors.RESET}")
            sleep(1)

            return True
        elif answer in {"n", "no"}:
            print(f"{Colors.BRIGHT_RED}Abort.{Colors.RESET}")
            return False

def main(args: Namespace) -> None:
    backup = BackupTool()

    print(backup.get_src_dst_string())
    if not ask(f"{choice(all_colors)}Continue? (y/N){Colors.RESET}: "):
        sysexit(0)
    
    copied = backup.copy_files()
    if isinstance(copied, Error):
        print(copied.msg)
        sysexit(1)

    print(f"Successfully copied {choice(all_colors)}{len(copied)}{Colors.RESET} files.")
    sleep(1)

    if not args.no_fs_sync:
        print(f"{choice(all_colors)}Syncing filesystem..{Colors.RESET}")
        try:
            sync()
        except Exception as e:
            print(f"Syncing filesystem failed. Cannot proceed with hash verification. Your copy may not be fully written.\nErr: {e}")
            sysexit(1)

    if not args.no_hash_verification:
        print(f"{choice(all_colors)}Verifying hashes..{Colors.RESET}")
        sleep(2)
        
        hashes_match = backup.verify_hashes(copied)
        if isinstance(hashes_match, Error):
            print(hashes_match.msg)
        elif hashes_match:
            print(f"{Colors.BRIGHT_GREEN}Hashes match!{Colors.RESET}")
        else:
            print(f"{Colors.BRIGHT_RED}Hashes don't match!{Colors.RESET}")

    print("done")

if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument("--no-hash-verification", action="store_true")
    argparser.add_argument("--no-fs-sync", action="store_true")
    args = argparser.parse_args()

    main(args)