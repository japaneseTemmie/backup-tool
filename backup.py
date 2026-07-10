from constants import RULES_JSON_PATH
from backupmanager import BackupManager
from rulesparser import RulesParser, Rule
from error import Error
from colors import Colors, all_colors
from logutils import log

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
        answer = input(prompt).lower().strip()

        if answer in {"y", "yes"}:
            log(f"{choice(all_colors)}Proceeding...{Colors.RESET}")
            sleep(1)

            return True
        elif answer in {"n", "no"}:
            log(f"{Colors.BRIGHT_RED}Abort.{Colors.RESET}")
            return False

def _show_changes(backup_manager: BackupManager) -> bool:
    """ Print the changes that will be applied to the user and wait for input. """

    log(backup_manager.get_changes())
    return _ask(f"{choice(all_colors)}Continue? (y/n){Colors.RESET}: ")

def _do_copy(backup_manager: BackupManager, dry_run: bool, quiet: bool) -> bool:
    """ Do the copy process. """

    log(f"{choice(all_colors)}Now copying files..{Colors.RESET}", quiet)

    ret = backup_manager.copy_files()
    if isinstance(ret, Error):
        log(ret.msg)
        return False

    _, copied = ret

    log(f"{'[DRY RUN] Would have ' if dry_run else ''}{'s' if dry_run else 'S'}uccessfully copied {choice(all_colors)}{len(copied)}{Colors.RESET} directories.", quiet)
    sleep(1)

    return True

def _do_sync(no_fs_sync: bool, dry_run: bool, quiet: bool) -> bool:
    """ Do filesystem sync (POSIX only). """
    
    if no_fs_sync:
        log(f"{choice(all_colors)}Skipped filesystem sync as per command line switch{Colors.RESET}", quiet)
        return True
    elif dry_run:
        log(f"{choice(all_colors)}[DRY RUN] Skipped filesystem sync as per dry run flag{Colors.RESET}", quiet)
        return True
    
    log(f"{choice(all_colors)}Syncing filesystem..{Colors.RESET}", quiet)
    
    if _SUPPORTS_FS_SYNC:
        try:
            sync() # Important to let all buffers get written before using them to compute the hashes
        except Exception as e:
            log(f"Syncing filesystem failed. Cannot proceed with hash verification. Your copy may not be fully written.\nErr: {e}")
            return False
    else:
        log(f"Unable to sync filesystem. OS might not provide support for it, and hash verification might fail due to unwritten buffers.", quiet)

    return True

def _do_hash_verification(backup_manager: BackupManager, no_hash_verification: bool, dry_run: bool, quiet: bool) -> bool:
    """ Do hash verification on the fresh copy of the files. """
    
    if no_hash_verification:
        log(f"{choice(all_colors)}Skipped hash verification as per command line switch{Colors.RESET}", quiet)
        return True
    elif dry_run:
        log(f"{choice(all_colors)}[DRY RUN] Skipped hash verification as per dry run flag{Colors.RESET}", quiet)
        return True
    
    log(f"{choice(all_colors)}Verifying hashes..{Colors.RESET}", quiet)
    sleep(2)
    
    ret = backup_manager.verify_hashes()

    if isinstance(ret, Error):
        log(ret.msg)
        return False
    elif ret:
        log(f"{Colors.BRIGHT_GREEN}Hashes match!{Colors.RESET}", quiet)
        return True
    else:
        log(f"{Colors.BRIGHT_RED}Hashes don't match!{Colors.RESET}", quiet)
        return False

def _get_rules(rules_file_path: str | None=None) -> list[Rule] | None:
    """ Get a list of rules provided by the `RulesParser` object. """

    parser = RulesParser(rules_file_path or RULES_JSON_PATH)
    content = parser.get_file_contents()

    if isinstance(content, Error):
        log(content.msg)
        return None
    
    rules = parser.parse_rules(content)

    if isinstance(rules, Error):
        log(rules.msg)
        return None

    return rules

def main(args: Namespace) -> None:
    if args.dry_run:
        log(f"{choice(all_colors)}===DRY RUN==={Colors.RESET}")

    rules = _get_rules(args.rules_file)
    if rules is None:
        sysexit(1)

    backup_manager = BackupManager(args.dry_run, args.no_follow_symlinks, args.quiet, rules)

    if not _show_changes(backup_manager):
        sysexit(0)
    elif not _do_copy(backup_manager, args.dry_run, args.quiet):
        sysexit(1)
    elif not _do_sync(args.no_fs_sync, args.dry_run, args.quiet):
        sysexit(1)
    elif not _do_hash_verification(backup_manager, args.no_hash_verification, args.dry_run, args.quiet):
        sysexit(1)

    log("done")

if __name__ == "__main__":
    argparser = ArgumentParser(
        prog="backup-tool",
        description="A tool to make copies of specified directories, useful for backups.",
        usage="""
        Usage options for backup-tool:

        --no-hash-verification Disables the post-copy hash verification between source and destination files.
        --no-fs-sync Disables filesystem sync after copying files.
        --dry-run Runs the program without making any changes. Useful to test configurations.
        --no-follow-symlinks Copies symlinks as symlinks to the destination. This is not recommended for backups to external disks.
        --quiet Hides noisy output.
        --rules-file Specifies which file to use as the 'rules file'. The chosen file must be a JSON file following the example structure.
        """,
        allow_abbrev=False
    )
    argparser.add_argument("--no-hash-verification", action="store_true")
    argparser.add_argument("--no-fs-sync", action="store_true")
    argparser.add_argument("--dry-run", action="store_true")
    argparser.add_argument("--no-follow-symlinks", action="store_true")
    argparser.add_argument("--quiet", action="store_true")
    argparser.add_argument("--rules-file")
    args = argparser.parse_args()

    main(args)
