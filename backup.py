from backuptool import BackupTool
from error import Error
from colors import Colors, all_colors

from argparse import ArgumentParser, Namespace
from sys import exit as sysexit

try:
    from os import sync
    _SUPPORTS_FS_SYNC = True
except ImportError:
    _SUPPORTS_FS_SYNC = False

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
    backup = BackupTool(args.dry_run)

    if args.dry_run:
        print(f"{choice(all_colors)}===DRY RUN==={Colors.RESET}")

    print(backup.get_src_dst_string())
    if not ask(f"{choice(all_colors)}Continue? (y/n){Colors.RESET}: "):
        sysexit(0)
    
    copied = backup.copy_files()
    if isinstance(copied, Error):
        print(copied.msg)
        sysexit(1)

    print(f"{'Would have' if args.dry_run else ''} {'s' if args.dry_run else 'S'}uccessfully copied {choice(all_colors)}{len(copied)}{Colors.RESET} entries.")
    sleep(1)

    if not args.no_fs_sync and not args.dry_run:
        print(f"{choice(all_colors)}Syncing filesystem..{Colors.RESET}")
        
        if _SUPPORTS_FS_SYNC:
            try:
                sync()
            except Exception as e:
                print(f"Syncing filesystem failed. Cannot proceed with hash verification. Your copy may not be fully written.\nErr: {e}")
                sysexit(1)
        else:
            print(f"Unable to sync filesystem. OS might not provide support for it, and hash verification might fail due to unwritten buffers.")

    if not args.no_hash_verification and not args.dry_run:
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
    argparser.add_argument("--dry-run", action="store_true")
    args = argparser.parse_args()

    main(args)