from error import Error
from rulesparser import Rule
from colors import Colors, all_colors

from typing import Generator
from hashlib import sha256
from fnmatch import fnmatch
from os import scandir
from os.path import isdir, exists, relpath, join
from shutil import copy2, copytree, ignore_patterns, Error as shutilError
from random import choice

def _copy_impl(src: str, dst: str) -> str:
    print(f"Copying {choice(all_colors)}{src}{Colors.RESET} to {choice(all_colors)}{dst}{Colors.RESET}")

    return copy2(src, dst)

class BackupManager:
    """ Backup manager object to handle core functions. """

    def __init__(self, dry_run: bool, rules: list[Rule]) -> None:
        self.dry_run = dry_run
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
            print(f"{choice(all_colors)}[DRY RUN] Skipped copy of {rule.source} to {rule.destination} as per dry run flag{Colors.RESET}")

            return rule.destination

        try:
            return copytree(
                rule.source,
                rule.destination,
                ignore=ignore_patterns(*rule.ignore) if rule.ignore else None,
                copy_function=_copy_impl,
                dirs_exist_ok=True
            )
        except shutilError as exc:
            error_msg = f"{Colors.BRIGHT_RED}Error(s) occurred while copying files.{Colors.RESET}\n"
            for src, dst, msg in exc.args[0]:
                error_msg += f"{Colors.BRIGHT_RED}Failed to copy {src} to {dst}. Err: {msg}{Colors.RESET}\n"
            
            return Error(error_msg)
        except OSError as exc: # handles copytree()'s makedirs() function call exceptions
            return Error(f"{Colors.BRIGHT_RED}An OS error occurred while copying {rule.source} to {rule.destination}. Err: {exc}{Colors.RESET}")

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
        """ Recurse into the given path and build a list of file paths. 
        
        Additionally, exclusions can be specified with the ignore argument. """
        
        if not isdir(path):
            return Error(f"{Colors.BRIGHT_RED}Path {path} is not a directory{Colors.RESET}")
        
        files = []

        with scandir(path) as iterator:
            if sort:
                entries = list(iterator)
                entries.sort(key=lambda e: e.name)
            else:
                entries = iterator

            for entry in entries:
                if ignore is not None and any(fnmatch(entry.name, pattern) for pattern in ignore):
                    continue
                
                if entry.is_file():
                    files.append(entry.path)
                elif entry.is_dir():
                    other = self._recurse_directory(entry.path, ignore, sort)
                    if isinstance(other, Error):
                        return other
                    
                    files.extend(other)

        return files

    def _read_file_buffers(self, file_path: str) -> Generator[bytes, None, None]:
        """ Yield 8KB chunks of file content for given file path. """
        
        buf_size = 8192
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
            for src_buf in self._read_file_buffers(src):
                src_hash.update(src_buf)
            for dst_buf in self._read_file_buffers(dst):
                dst_hash.update(dst_buf)

            print(f"Verified hash of {choice(all_colors)}{src}{Colors.RESET} with {choice(all_colors)}{dst}{Colors.RESET}")

            return src_hash.hexdigest() == dst_hash.hexdigest()
        except OSError as exc:
            return Error(f"{Colors.BRIGHT_RED}An error occurred while reading file buffers: {exc}{Colors.RESET}")

    def _do_hash_verification(self) -> bool | Error:
        """ Compute and compare source and destination file SHA-256 hashes of all provided rules. """
        
        for rule in self.rules:
            try:
                src_files = self._recurse_directory(rule.source, rule.ignore)
                if isinstance(src_files, Error): return src_files

                for src_file in src_files:
                    relative = relpath(src_file, rule.source)
                    dst_file = join(rule.destination, relative)

                    if not exists(dst_file):
                        return Error(f"{Colors.BRIGHT_RED}File {dst_file} not found at expected location.{Colors.RESET}")

                    ret = self._compare_file_hashes(src_file, dst_file)
                    if isinstance(ret, Error):
                        return ret
                    elif not ret:
                        print(f"{Colors.BRIGHT_RED}Hash verification failed for file {src_file} with {dst_file}.{Colors.RESET}")
                        return False
            except OSError as exc:
                return Error(f"{Colors.BRIGHT_RED}An error occurred while verifiying hashes: {exc}{Colors.RESET}")

        return True

    def verify_hashes(self) -> bool | Error:
        return self._do_hash_verification()
