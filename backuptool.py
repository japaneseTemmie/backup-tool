from error import Error
from rulesparser import RulesParser
from colors import Colors, all_colors
from pathutils import File, Folder

from sys import exit as sysexit
from random import choice

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

    def verify_hashes(self, original: list[File], copied: list[File]) -> bool | Error:
        """ Compare each file's hash in `original` with the hash of each file in `copied`. """
        
        matches = []
        for orig_file, copied_file in zip(original, copied):
            try:
                matches.append(orig_file.hash() == copied_file.hash())

                print(f"Verified hash of {choice(all_colors)}{orig_file.path}{Colors.RESET} with {choice(all_colors)}{copied_file.path}{Colors.RESET}")
            except (ValueError, OSError) as e:
                return Error(f"An error occured while verifying hash of file {choice(all_colors)}{orig_file.name}{Colors.RESET} with {choice(all_colors)}{copied_file.name}{Colors.RESET}:\n{Colors.BRIGHT_RED}{e}{Colors.RESET}")

        return all(matches)

    def copy_files(self) -> tuple[list[File], list[File]] | Error:
        """ Copy all files from source to destination as defined in rules.json 
        
        Return original and copied files. """

        original, copied = [], []

        for rule in self.rules:
            try:
                source_folder = Folder(rule.source)
                dest, orig = source_folder.copy_to(rule.destination, rule.exclude_files, rule.exclude_directories)

                original.extend(orig)
                copied.extend(dest)

                print(f"Copied {choice(all_colors)}{len(orig)}{Colors.RESET} files to {choice(all_colors)}{rule.destination}{Colors.RESET}")
            except (OSError, ValueError) as e:
                return Error(f"An error occured while copying source {choice(all_colors)}{rule.source}{Colors.RESET} to destination {choice(all_colors)}{rule.destination}{Colors.RESET}:\n{choice(all_colors)}{e}{Colors.RESET}")
            
        return original, copied
