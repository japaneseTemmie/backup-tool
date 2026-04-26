from backupmanager import BackupManager, Rule
from rulesparser import RulesParser
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

def _ask(prompt: str) -> bool:
    while True:
        answer = input(prompt)

        if answer in {"y", "yes"}:
            print(f"{choice(all_colors)}Proceeding...{Colors.RESET}")
            sleep(1)

            return True
        elif answer in {"n", "no"}:
            print(f"{Colors.BRIGHT_RED}Abort.{Colors.RESET}")
            return False

def _show_changes(backup_manager: BackupManager) -> None:
    """ Print the changes that will be applied to the user and wait for input. """

    print(backup_manager.get_src_dst_string())
    if not _ask(f"{choice(all_colors)}Continue? (y/n){Colors.RESET}: "):
        sysexit(0)

def _do_copy(backup_manager: BackupManager) -> None:
    """ Do the copy process. """
    
    print(f"{choice(all_colors)}Now copying files..{Colors.RESET}")

    ret = backup_manager.copy_files()
    if isinstance(ret, Error):
        print(ret.msg)
        sysexit(1)

    _, copied = ret

    print(f"{'[DRY RUN] Would have ' if args.dry_run else ''}{'s' if args.dry_run else 'S'}uccessfully copied {choice(all_colors)}{len(copied)}{Colors.RESET} directories.")
    sleep(1)

def _do_sync(args: Namespace) -> None:
    """ Do filesystem sync (POSIX only). """
    
    if args.no_fs_sync:
        print(f"{choice(all_colors)}Skipped filesystem sync as per command line switch{Colors.RESET}")
        return
    elif args.dry_run:
        print(f"{choice(all_colors)}[DRY RUN] Skipped filesystem sync as per dry run flag{Colors.RESET}")
        return
    
    print(f"{choice(all_colors)}Syncing filesystem..{Colors.RESET}")
    
    if _SUPPORTS_FS_SYNC:
        try:
            sync() # Important to let all buffers get written before using them to compute the hashes
        except Exception as e:
            print(f"Syncing filesystem failed. Cannot proceed with hash verification. Your copy may not be fully written.\nErr: {e}")
            sysexit(1)
    else:
        print(f"Unable to sync filesystem. OS might not provide support for it, and hash verification might fail due to unwritten buffers.")

def _do_hash_verification(backup_manager: BackupManager) -> None:
    """ Do hash verification on the fresh copy of the files. """
    
    if args.no_hash_verification:
        print(f"{choice(all_colors)}Skipped hash verification as per command line switch{Colors.RESET}")
        return
    elif args.dry_run:
        print(f"{choice(all_colors)}[DRY RUN] Skipped hash verification as per dry run flag{Colors.RESET}")
        return
    
    print(f"{choice(all_colors)}Verifying hashes..{Colors.RESET}")
    sleep(2)
    
    ret = backup_manager.verify_hashes()

    if isinstance(ret, Error):
        print(ret.msg)
    elif ret:
        print(f"{Colors.BRIGHT_GREEN}Hashes match!{Colors.RESET}")
    else:
        print(f"{Colors.BRIGHT_RED}Hashes don't match!{Colors.RESET}")

def _get_rules() -> list[Rule] | Error:
    """ Get a list of rules provided by the `RulesParser` object. """

    parser = RulesParser()
    content = parser.get_file_contents()

    if isinstance(content, Error):
        print(content.msg)
        sysexit(1)
    
    rules = parser.parse_rules(content)

    if isinstance(rules, Error):
        print(rules.msg)
        sysexit(1)

    return rules

def main(args: Namespace) -> None:
    if args.dry_run:
        print(f"{choice(all_colors)}===DRY RUN==={Colors.RESET}")

    rules = _get_rules()

    backup_manager = BackupManager(args.dry_run, rules)

    _show_changes(backup_manager)
    _do_copy(backup_manager)
    _do_sync(args)
    _do_hash_verification(backup_manager)

    print("done")

if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument("--no-hash-verification", action="store_true")
    argparser.add_argument("--no-fs-sync", action="store_true")
    argparser.add_argument("--dry-run", action="store_true")
    args = argparser.parse_args()

    main(args)