from constants import RULES_JSON_PATH
from error import Error
from colors import Colors

from os.path import exists, isdir
from json import load, JSONDecodeError
from re import Pattern, compile

class Rule:
    def __init__(self, source: str, destination: str, exclude_files: list[str | Pattern] | None, exclude_directories: list[str | Pattern]):
        self.source = source
        self.destination = destination
        self.exclude_files = exclude_files
        self.exclude_directories = exclude_directories

class RulesParser:
    def get_file_contents(self) -> dict | Error:
        """ Try to open the rules.json file. 
        
        Return file contents on success, otherwise Error. """
        
        if not exists(RULES_JSON_PATH):
            return Error(f"{Colors.BRIGHT_RED}The file rules.json does not exist!{Colors.RESET}")
        
        try:
            with open(RULES_JSON_PATH) as f:
                return load(f)
        except OSError as e:
            return Error(f"{Colors.BRIGHT_RED}Unable to open file due to error:\n{e}{Colors.RESET}")
        except JSONDecodeError as e:
            return Error(f"{Colors.BRIGHT_RED}Unable to parse JSON file due to error:\n{e}{Colors.RESET}")
    
    def check_destination(self, destination: str, iteration_count: int) -> str | Error:
        """ Run several authenticity checks on `destination`. 
        
        Return `destination` or `Error`. """

        if not destination:
            return Error(f"{Colors.BRIGHT_RED}Destination is not defined at iteration {iteration_count}{Colors.RESET}")
        elif not isinstance(destination, str):
            return Error(f"{Colors.BRIGHT_RED}Destination is defined as {type(destination)} at iteration {iteration_count}, expected string{Colors.RESET}")
        
        return destination

    def check_source(self, source: str, iteration_count: int) -> str | Error:
        """ Run several authenticity checks on `source`. 
        
        Return `source` or `Error`. """
        
        if not source:
            return Error(f"{Colors.BRIGHT_RED}Source is not defined at iteration {iteration_count}{Colors.RESET}")
        elif not isinstance(source, str):
            return Error(f"{Colors.BRIGHT_RED}Source is defined as {type(source)} at iteration {iteration_count}, expected string{Colors.RESET}")
        elif not exists(source):
            return Error(f"{Colors.BRIGHT_RED}Source defined at iteration {iteration_count} does not exist in the filesystem{Colors.RESET}")
        elif not isdir(source):
            return Error(f"{Colors.BRIGHT_RED}Source defined at iteration {iteration_count} is not a directory")

        return source

    def check_source_and_destination(self, source: str, destination: str, iteration_count: int) -> tuple[str, str] | Error:
        """ Run several authenticity checks on `source` and `destination`.
        
        Return `source` and `destination` or `Error`. """
        
        source = self.check_source(source, iteration_count)
        if isinstance(source, Error):
            return source
        
        destination = self.check_destination(destination, iteration_count)
        if isinstance(destination, Error):
            return destination
        
        return source, destination
    
    def check_exclude_list(self, exclude_list: list[str] | None, regex: bool, iteration_count: int) -> list[str | Pattern] | list | Error:
        """ Run authenticity checks on `exclude_list` """
        
        if exclude_list is None:
            return []
        
        if exclude_list is not None and (not isinstance(exclude_list, list) or not all(isinstance(item, str) for item in exclude_list)):
            return Error(f"{Colors.BRIGHT_RED}Exclude files is defined as {type(exclude_list)} at iteration {iteration_count}, expected list of strings.{Colors.RESET}")
        
        if regex:
            try:
                exclude_list = [compile(exclude_rule) for exclude_rule in exclude_list]
            except Exception as e:
                return Error(f"{Colors.BRIGHT_RED}An error occured while compiling a regular expression at iteration {iteration_count}\nErr: {e}")
    
        return exclude_list

    def check_exclude(self, exclude: dict, iteration_count: int) -> tuple[list[str | Pattern] | list, list[str | Pattern] | list] | Error:
        """ Run authenticity checks on `exclude`
        
        Return `exclude_files` and `exclude_directories` or `Error` """

        exclude_files, exclude_directories = [], []

        if exclude is not None:
            if "files" not in exclude and "directories" not in exclude:
                return Error(f"{Colors.BRIGHT_RED}Exclude is defined but with no content at iteration {iteration_count}{Colors.RESET}")
            elif not isinstance(exclude, dict):
                return Error(f"{Colors.BRIGHT_RED}Exclude is defined as {type(exclude)} at iteration {iteration_count}, expected dictionary{Colors.RESET}")
        
            regex = exclude.get("use_regex", False)
            if not isinstance(regex, bool):
                return Error(f"{Colors.BRIGHT_RED}Regex usage defined as {type(regex)} at iteration {iteration_count}, expected boolean")

            exclude_files = exclude.get("files", [])
            if exclude_files is not None:
                exclude_files = self.check_exclude_list(exclude_files, regex, iteration_count)
                if isinstance(exclude_files, Error):
                    return exclude_files
            
            exclude_directories = exclude.get("directories", [])
            if exclude_directories is not None:
                exclude_directories = self.check_exclude_list(exclude_directories, regex, iteration_count)
                if isinstance(exclude_directories, Error):
                    return exclude_directories

        return exclude_files, exclude_directories

    def parse_rules(self, content: dict[str, list[dict[str, str]]]) -> list[Rule] | Error:
        """ Parse rules.json's content and return Rule objects """
        
        rules = content.get("rules")
        rule_objs = []
        
        if not content or rules is None:
            return Error("No rules found.")
        
        for i, rule in enumerate(rules):
            source = rule.get("source")
            destination = rule.get("destination")
            exclude = rule.get("exclude")
            exclude_files = []
            exclude_directories = []

            result = self.check_source_and_destination(source, destination, i)
            if isinstance(result, Error):
                return result
            
            source, destination = result

            result = self.check_exclude(exclude, i)
            if isinstance(result, Error):
                return result
            
            exclude_files, exclude_directories = result
                
            rule_objs.append(Rule(source, destination, exclude_files, exclude_directories))

        return rule_objs