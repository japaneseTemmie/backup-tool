from error import Error
from rulesparser import RulesParser
from colors import Colors, all_colors
from pathutils import File, Folder

from typing import Optional, Generator, Union
from os import makedirs, listdir
from os.path import exists, join, isfile, isdir, basename
from sys import exit as sysexit
from random import choice

class BackupFolder(Folder):
    def __init__(self, path = "", ensure_exists = False):
        super().__init__(path, ensure_exists)

    def __bool__(self) -> bool:
        return self.path is not None and exists(self.path)

    def __iter__(self) -> Generator[Union[File, "Folder"], None, None]:
        entries = sorted(listdir(self.path))
        for item in entries:
            full_fp = join(self.path, item)
            
            if isfile(full_fp):
                yield File(full_fp)
            elif isdir(full_fp):
                yield BackupFolder(full_fp)

    def subfolders(self) -> Generator["Folder", None, None]:
        """ Return a generator object with subfolders present in the folder. """
        
        entries = sorted(listdir(self.path))
        for dir in entries:
            full_fp = join(self.path, dir)
            
            if isdir(full_fp):
                yield BackupFolder(full_fp)

    def make_subfolder(self, name: str) -> "Folder":
        """ Create a subfolder in the folder.
         
        `name` must be a folder name.
         
        Returns the created folder.
         
        Raises standard OS exceptions. """
        
        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a directory name, not path")
        elif not exists(self.path) or self.path is None:
            raise TypeError("Folder path must point to a valid location")

        directory_path = join(self.path, name)

        return BackupFolder(directory_path, True)

    def delete_subfolder(self, name: str) -> None:
        """ Delete a subfolder from the folder.
         
        `name` must be a folder name. 
        
        Raises standard OS exceptions. """
        
        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a directory name, not path")
        elif not exists(self.path) or self.path is None:
            raise TypeError("Folder path must point to a valid location")

        dir_path = join(self.path, name)
        if isfile(dir_path):
            raise ValueError("name argument must point to a directory, not file")

        folder = BackupFolder(dir_path)
        folder.delete()

    def copy_to(self, path: str, exclude_files: list[Optional[str]]=None, exclude_directories: list[Optional[str]]=None) -> list[tuple[File, File]]:
        """ Copy the folder to a new location. 
        
        Additionally, pass a list of strings (file or directory names) to exclude from copy.

        Return a list of tuples with original file and destination file.

        Raises standard OS exceptions. """
        
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif not exists(self.path) or self.path is None:
            raise TypeError("Folder path must point to a valid location")

        pairs = []

        makedirs(path, exist_ok=True)

        for file in self.files():
            if isinstance(exclude_files, list) and file.name in exclude_files:
                continue

            source_file, new_file = file.copy_to(join(path, file.name))
            pairs.append((source_file, new_file))

        for subfolder in self.subfolders():
            if isinstance(exclude_directories, list) and subfolder.name in exclude_directories:
                continue
            
            other_pairs = subfolder.copy_to(join(path, subfolder.name), exclude_files, exclude_directories)
            pairs.extend(other_pairs)

        return pairs

class BackupTool:
    def __init__(self):
        self.rules_parser = RulesParser()

        self.rules_content = self.rules_parser.get_file_contents()
        if isinstance(self.rules_content, Error):
            print(self.rules_content.msg)
            sysexit(1)

        self.rules = self.rules_parser.parse_rules(self.rules_content)
        if isinstance(self.rules, Error):
            print(self.rules.msg)
            sysexit(1)

    def get_src_dst_string(self) -> str:
        string = str()

        string += "Will copy and verify hash:\n"
        for rule in self.rules:
            string += f"{choice(all_colors)}{rule.source} {Colors.RESET}"
            string += "-> "
            string += f"{choice(all_colors)}{rule.destination} {Colors.RESET}"
            if rule.exclude_files:
                string += f"{choice(all_colors)}(excluding {rule.exclude_files} files){Colors.RESET}"
            if rule.exclude_directories:
                string += f"{choice(all_colors)} (excluding {rule.exclude_directories} directories){Colors.RESET}"
            string += "\n\n"

        return string

    def verify_hashes(self, pairs: list[tuple[File, File]]) -> bool | Error:
        """ Verify each file's hash in `pairs`. """
        
        matches = []
        for orig_file, copied_file in pairs:
            try:
                matches.append(orig_file.hash() == copied_file.hash())

                print(f"Verified hash of {choice(all_colors)}{orig_file.path}{Colors.RESET} with {choice(all_colors)}{copied_file.path}{Colors.RESET}")
            except (ValueError, TypeError, OSError) as e:
                return Error(f"An error occured while verifying hash of file {choice(all_colors)}{orig_file.name}{Colors.RESET} with {choice(all_colors)}{copied_file.name}{Colors.RESET}:\n{Colors.BRIGHT_RED}{e}{Colors.RESET}")

        return all(matches)

    def copy_files(self) -> list[tuple[File, File]] | Error:
        """ Copy all files from source to destination as defined in rules.json 
        
        Return original and copied files. """

        pairs = []

        for rule in self.rules:
            try:
                source_folder = BackupFolder(rule.source)
                pair = source_folder.copy_to(rule.destination, rule.exclude_files, rule.exclude_directories)

                pairs.extend(pair)

                print(f"Copied {choice(all_colors)}{len(pair)}{Colors.RESET} entries to {choice(all_colors)}{rule.destination}{Colors.RESET}")
            except (OSError, TypeError, ValueError) as e:
                return Error(f"An error occured while copying source {choice(all_colors)}{rule.source}{Colors.RESET} to destination {choice(all_colors)}{rule.destination}{Colors.RESET}:\n{Colors.BRIGHT_RED}{e}{Colors.RESET}")
            
        return pairs