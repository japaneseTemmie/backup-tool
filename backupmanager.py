from constants import FILE_BUF_SIZE
from error import Error
from rulesparser import Rule
from colors import Colors, all_colors
from logutils import log

from typing import Generator
from hashlib import sha256
from fnmatch import fnmatch
from os import scandir
from os.path import relpath, basename, join
from shutil import copy2, copytree, ignore_patterns, Error as shutilError
from random import choice

def _copy_impl(src: str, dst: str, quiet: bool) -> str:
    log(f"Copying {choice(all_colors)}{src}{Colors.RESET} to {choice(all_colors)}{dst}{Colors.RESET}", quiet)

    return copy2(src, dst)

class BackupManager:
    """ Backup manager object to handle core functions. """

    def __init__(self, dry_run: bool, no_follow_symlinks: bool, quiet: bool, rules: list[Rule]) -> None:
        self.dry_run = dry_run
        self.no_follow_symlinks = no_follow_symlinks
        self.quiet = quiet
        self.rules = rules

    def get_changes(self) -> str:
        """ Return a string containing all the rules' changes and their exclusions. """
        
        string = str()

        string += f"Will copy and verify hash:\n"
        for rule in self.rules:
            string += f"{choice(all_colors)}{rule.source} {Colors.RESET}"
            string += "-> "
            string += f"{choice(all_colors)}{rule.destination} {Colors.RESET}"
            if rule.ignore:
                string += f"{choice(all_colors)}(excluding {', '.join([excluded for excluded in rule.ignore])} files/folders){Colors.RESET}"
            string += "\n"

        return string

    def _do_copy_op(self, rule: Rule) -> str | Error:
        """ Copy source to destination as specified by the rule argument. 
        
        On success, return a string of the copied directory, otherwise `Error` object. """

        if self.dry_run:
            log(f"{choice(all_colors)}[DRY RUN] Skipped copy of {rule.source} to {rule.destination} as per dry run flag{Colors.RESET}", self.quiet)

            return rule.destination

        try:
            return copytree(
                rule.source,
                rule.destination,
                symlinks=self.no_follow_symlinks, # 'symlinks' argument is basically the same as 'follow_symlinks'
                ignore=ignore_patterns(*rule.ignore) if rule.ignore else None,
                copy_function=lambda src, dst: _copy_impl(src, dst, self.quiet),
                dirs_exist_ok=True
            )
        except shutilError as exc:
            error_msg = f"{Colors.BRIGHT_RED}Error(s) occurred while copying files.{Colors.RESET}\n"
            for src, dst, msg in exc.args[0]:
                error_msg += f"{Colors.BRIGHT_RED}Failed to copy {src} to {dst}. Err: {msg}{Colors.RESET}\n"
            
            return Error(error_msg)
        except OSError as exc: # handles copytree()'s makedirs() function call exceptions
            return Error(f"{Colors.BRIGHT_RED}An error occurred while copying {rule.source} to {rule.destination}. Err: {exc}{Colors.RESET}")

    def copy_files(self) -> tuple[list[str], list[str]] | Error:
        """ Copy all files from source to destination as defined in rules.json 
        
        Return a tuple with two lists containing source and copied directories' paths respectively. """

        source, copied = [], []

        for rule in self.rules:
            ret = self._do_copy_op(rule)

            if isinstance(ret, Error):
                return ret
            
            copied.append(ret)
            source.append(rule.source)

        return source, copied
    
    def _recurse_directory(self, path: str, ignore: list[str] | None=None, sort: bool=False) -> list[str] | Error:
        """ Recurse into the given directory path and build a list of paths for all inner files. 
        
        Additionally, exclusions can be specified as glob patterns with the ignore argument. 

        Return a list of string file paths, or an Error object on failure. """
        
        def _traverse_dir(current_path: str) -> list[str] | Error:
            """ Traverse into the directory and collect all file paths inside of it. This is recursive. """
            
            files = []
        
            try:
                with scandir(current_path) as iterator:
                    for entry in iterator:
                        if ignore is not None and any(fnmatch(entry.name, pattern) for pattern in ignore):
                            continue
                        
                        if entry.is_file():
                            files.append(entry.path)
                        elif entry.is_dir():
                            other = _traverse_dir(entry.path)
                            if isinstance(other, Error):
                                return other
                            
                            files.extend(other)
            except FileNotFoundError:
                return Error(f"{Colors.BRIGHT_RED}Path {current_path} does not exist!{Colors.RESET}")
            except NotADirectoryError:
                return Error(f"{Colors.BRIGHT_RED}Path {current_path} is not a directory!{Colors.RESET}")
            except PermissionError:
                return Error(f"{Colors.BRIGHT_RED}Unable to open directory {current_path} due to permission error.{Colors.RESET}")
            except OSError as exc:
                return Error(f"{Colors.BRIGHT_RED}An error occurred while recursing directory at {current_path}.\nErr: {exc}{Colors.RESET}")

            return files

        ret = _traverse_dir(path)
        if isinstance(ret, Error):
            return ret
        
        return ret if not sort else sorted(ret, key=basename)

    def _read_file_buffers(self, file_path: str, buf_size: int) -> Generator[bytes, None, None]:
        """ Yield chunks of arbitrary size of file content for the given file path. """

        with open(file_path, "rb") as f:
            while True:
                buf = f.read(buf_size)
                if not buf:
                    return

                yield buf

    def _compare_file_hashes(self, src: str, dst: str) -> bool | Error:
        """ Build and compare source and destination files' hashes. """
        
        src_hash = sha256()
        dst_hash = sha256()

        try:
            log(f"Verifying hash of {choice(all_colors)}{src}{Colors.RESET} with {choice(all_colors)}{dst}{Colors.RESET}", self.quiet)

            for src_buf in self._read_file_buffers(src, FILE_BUF_SIZE):
                src_hash.update(src_buf)
            for dst_buf in self._read_file_buffers(dst, FILE_BUF_SIZE):
                dst_hash.update(dst_buf)

            return src_hash.hexdigest() == dst_hash.hexdigest()
        except FileNotFoundError:
            return Error(f"{Colors.BRIGHT_RED}Required files were not found during hash verification of file {src} with {dst}{Colors.RESET}")
        except PermissionError:
            return Error(f"{Colors.BRIGHT_RED}Unable to open required files for hash verification of file {src} with {dst}{Colors.RESET}")
        except OSError as exc:
            return Error(f"{Colors.BRIGHT_RED}An error occurred while reading file buffers: {exc}{Colors.RESET}")

    def _do_hash_verification(self) -> bool | Error:
        """ Compute and compare source and destination file SHA-256 hashes of all provided rules. """
        
        for rule in self.rules:
            try:
                dst_files, src_files = self._recurse_directory(rule.destination, rule.ignore), self._recurse_directory(rule.source, rule.ignore)
                if isinstance(src_files, Error):
                    return src_files
                elif isinstance(dst_files, Error):
                    return dst_files

                src_files = set(src_files)
                for dst_file in dst_files:
                    relative = relpath(dst_file, rule.destination)
                    src_file = join(rule.source, relative)

                    if src_file not in src_files:
                        continue # we did not copy this file

                    ret = self._compare_file_hashes(src_file, dst_file)
                    if isinstance(ret, Error):
                        return ret
                    elif not ret:
                        log(f"{Colors.BRIGHT_RED}Hash verification failed for file {src_file} with {dst_file}.{Colors.RESET}")
                        return False
            except OSError as exc:
                return Error(f"{Colors.BRIGHT_RED}An error occurred while verifiying hashes: {exc}{Colors.RESET}")

        return True

    def verify_hashes(self) -> bool | Error:
        return self._do_hash_verification()
