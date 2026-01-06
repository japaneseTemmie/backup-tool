from error import Error
from rulesparser import RulesParser
from colors import Colors, all_colors
from pathutils import File, Folder

from typing import Generator, Union
from re import Pattern
from os import makedirs, listdir
from os.path import join, isfile, isdir, basename
from sys import exit as sysexit
from random import choice

class BackupFolder(Folder):
    def __init__(self, path = "", ensure_exists = False):
        super().__init__(path, ensure_exists)

        self.__path = self.path

    def __bool__(self) -> bool:
        return self.__path is not None and isdir(self.__path)

    def __iter__(self) -> Generator[Union[File, "Folder"], None, None]:
        if self.__path is None or not isdir(self.__path):
            raise ValueError("path attribute must point to a valid folder")

        entries = sorted(listdir(self.__path))
        for item in entries:
            full_fp = join(self.__path, item)
            
            if isfile(full_fp):
                yield File(full_fp)
            elif isdir(full_fp):
                yield BackupFolder(full_fp)

    def subfolders(self) -> Generator["Folder", None, None]:
        """ Return a generator object with subfolders present in the folder. """
        if self.__path is None or not isdir(self.__path):
            raise ValueError("path attribute must point to a valid folder")
        
        entries = sorted(listdir(self.__path))
        for dir in entries:
            full_fp = join(self.__path, dir)
            
            if isdir(full_fp):
                yield BackupFolder(full_fp)

    def make_subfolder(self, name: str) -> "Folder":
        """ Create a subfolder in the folder.
         
        `name` must be a folder name.
         
        Returns the created folder.
         
        Raises standard OS exceptions and additional ValueError and TypeError. """
        
        if not isinstance(name, str):
            raise TypeError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a directory name, not path")
        elif self.__path is None or not isdir(self.__path):
            raise ValueError("path attribute must point to a valid folder")

        directory_path = join(self.__path, name)

        return BackupFolder(directory_path, True)

    def delete_subfolder(self, name: str) -> None:
        """ Delete a subfolder from the folder.
         
        `name` must be a folder name. 
        
        Raises standard OS exceptions and additional ValueError and TypeError. """
        
        if not isinstance(name, str):
            raise TypeError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a directory name, not path")
        elif self.__path is None or not isdir(self.__path):
            raise ValueError("path attribute must point to a valid folder")

        dir_path = join(self.__path, name)
        if isfile(dir_path):
            raise ValueError("name argument must point to a directory, not file")

        folder = BackupFolder(dir_path)
        folder.delete()

    def copy_to(self, path: str, exclude_files: list[Pattern | str] | list, exclude_directories: list[Pattern | str] | list, dry_run: bool=False) -> list[tuple[File | None, File | None]]:
        """ Copy the folder to a new location. 
        
        Additionally, pass a list of strings (file or directory names) or re.Pattern objects to exclude from copy.

        Return a list of tuples with original file and destination file.

        Raises standard OS exceptions and additional ValueError and TypeError. """
        
        if not isinstance(path, str):
            raise TypeError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif self.__path is None or not isdir(self.__path):
            raise ValueError("Folder path must point to a valid location")

        pairs = []

        if not dry_run:
            makedirs(path, exist_ok=True)

        for file in self.files():
            if exclude_files and any((isinstance(exclude_rule, Pattern) and exclude_rule.match(file.name)) or (isinstance(exclude_rule, str) and file.name == exclude_rule) for exclude_rule in exclude_files):
                print(f"Skipped file {choice(all_colors)}{file.path}{Colors.RESET}")
                continue

            if not dry_run:
                source_file, new_file = file.copy_to(join(path, file.name))
            else:
                source_file, new_file = None, None
            pairs.append((source_file, new_file))

        for subfolder in self.subfolders():
            if exclude_directories and any((isinstance(exclude_rule, Pattern) and exclude_rule.match(subfolder.name)) or (isinstance(exclude_rule, str) and subfolder.name == exclude_rule) for exclude_rule in exclude_directories):
                print(f"Skipped directory {choice(all_colors)}{subfolder.path}{Colors.RESET}")
                continue
            
            other_pairs = subfolder.copy_to(join(path, subfolder.name), exclude_files, exclude_directories, dry_run)
            pairs.extend(other_pairs)

        return pairs

class BackupTool:
    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run
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

        string += f"{'Would' if self.dry_run else 'Will'} copy and verify hash:\n"
        for rule in self.rules:
            string += f"{choice(all_colors)}{rule.source} {Colors.RESET}"
            string += "-> "
            string += f"{choice(all_colors)}{rule.destination} {Colors.RESET}"
            if rule.exclude_files:
                string += f"{choice(all_colors)}(excluding {', '.join([exclude_rule.pattern if isinstance(exclude_rule, Pattern) else exclude_rule for exclude_rule in rule.exclude_files])} files){Colors.RESET}"
            if rule.exclude_directories:
                string += f"{choice(all_colors)} (excluding {', '.join([exclude_rule.pattern if isinstance(exclude_rule, Pattern) else exclude_rule for exclude_rule in rule.exclude_directories])} directories){Colors.RESET}"
            string += "\n"

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
                pair = source_folder.copy_to(rule.destination, rule.exclude_files, rule.exclude_directories, self.dry_run)

                pairs.extend(pair)

                message = f"Would have copied {choice(all_colors)}{len(pair)}{Colors.RESET} entries to {choice(all_colors)}{rule.destination}{Colors.RESET}" if self.dry_run else\
                f"Copied {choice(all_colors)}{len(pair)}{Colors.RESET} entries to {choice(all_colors)}{rule.destination}{Colors.RESET}"
                
                print(message)
            except (OSError, TypeError, ValueError) as e:
                return Error(f"An error occured while copying source {choice(all_colors)}{rule.source}{Colors.RESET} to destination {choice(all_colors)}{rule.destination}{Colors.RESET}:\n{Colors.BRIGHT_RED}{e}{Colors.RESET}")
            
        return pairs