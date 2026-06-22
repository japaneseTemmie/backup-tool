from error import Error
from colors import Colors

from os.path import isdir, isabs, normpath, abspath
from json import load, JSONDecodeError
from typing import Any

class Rule:
    """ Generic rule object to cache properties for each transfer. """
    
    def __init__(self, source: str, destination: str, ignore: list[str]) -> None:
        self.source = source
        self.destination = destination
        self.ignore = ignore

class RulesParser:
    def __init__(self, rules_file_path: str) -> None:
        if not isabs(rules_file_path):
            self.rules_file_path = abspath(rules_file_path)
        else:
            self.rules_file_path = rules_file_path

    def get_file_contents(self) -> dict[str, list[dict[str, Any]]] | Error:
        """ Try to open the rules.json file. 
        
        Return file contents on success, otherwise an `Error` object. """
        
        try:
            with open(self.rules_file_path) as f:
                return load(f)
        except FileNotFoundError:
            return Error(f"{Colors.BRIGHT_RED}'{self.rules_file_path}' rules file does not exist!{Colors.RESET}")
        except OSError as e:
            return Error(f"{Colors.BRIGHT_RED}Unable to open '{self.rules_file_path}' rules file due to error:\n{e}{Colors.RESET}")
        except JSONDecodeError as e:
            return Error(f"{Colors.BRIGHT_RED}Unable to parse '{self.rules_file_path}' JSON rules file due to error:\n{e}{Colors.RESET}")
    
    def _check_destination(self, destination: str, iteration_count: int) -> str | Error:
        """ Check if destination is valid. 
        
        Return destination if checks are passed, otherwise an `Error` object. """

        if not isinstance(destination, str):
            return Error(f"{Colors.BRIGHT_RED}Destination is defined as {destination.__class__.__name__} at iteration {iteration_count}, expected string{Colors.RESET}")
        elif not destination:
            return Error(f"{Colors.BRIGHT_RED}Destination is not defined at iteration {iteration_count}{Colors.RESET}")
        elif not isabs(destination):
            return Error(f"{Colors.BRIGHT_RED}Destination path defined at iteration {iteration_count} must be an absolute path. (begins from root to destination){Colors.RESET}")
        elif isdir(destination):
            print(f"{Colors.BRIGHT_YELLOW}WARNING: Destination defined at iteration {iteration_count} '{destination}' already exists! Its contents matching file names from source directory will be overwritten!{Colors.RESET}")

        return destination

    def _check_source(self, source: str, iteration_count: int) -> str | Error:
        """ Check if source is valid.
        
        Return source if checks are passed, otherwise `Error` object. """
        
        if not isinstance(source, str):
            return Error(f"{Colors.BRIGHT_RED}Source is defined as {source.__class__.__name__} at iteration {iteration_count}, expected string{Colors.RESET}")
        elif not source:
            return Error(f"{Colors.BRIGHT_RED}Source is not defined at iteration {iteration_count}{Colors.RESET}")
        elif not isabs(source):
            return Error(f"{Colors.BRIGHT_RED}Source path defined at iteration {iteration_count} must be an absolute path. (begins from root to source directory){Colors.RESET}")
        elif not isdir(source):
            return Error(f"{Colors.BRIGHT_RED}Source defined at iteration {iteration_count} is not a directory{Colors.RESET}")

        return source

    def _check_source_and_destination(self, source: str, destination: str, iteration_count: int) -> tuple[str, str] | Error:
        """ Check both source and destination. This also normalizes the source and destination paths.
        
        Return a tuple with source and destination if checks are passed, otherwise an `Error` object. """
        
        source, destination = normpath(source), normpath(destination)

        if source == destination:
            return Error(f"{Colors.BRIGHT_RED}Source and destination defined at iteration {iteration_count} cannot be the same!{Colors.RESET}")

        source = self._check_source(source, iteration_count)
        if isinstance(source, Error):
            return source
        
        destination = self._check_destination(destination, iteration_count)
        if isinstance(destination, Error):
            return destination
        
        return source, destination
    
    def _check_ignore_list(self, ignore_list: list[str] | None, iteration_count: int) -> list[str] | Error:
        """ Check the ignore list. 
        
        Return the ignore list if checks are passed, otherwise an `Error` object. """
        
        if ignore_list is None:
            return []
        elif not isinstance(ignore_list, list):
            return Error(f"{Colors.BRIGHT_RED}Ignore attribute is defined as {ignore_list.__class__.__name__} at iteration {iteration_count}, expected list of strings.{Colors.RESET}")
        elif not all(isinstance(item, str) for item in ignore_list):
            return Error(f"{Colors.BRIGHT_RED}Ignore attribute is defined as a list at iteration {iteration_count}, but atleast one item in it is not a string representing a glob pattern.{Colors.RESET}")
        elif not all(item for item in ignore_list):
            return Error(f"{Colors.BRIGHT_RED}Ignore attribute is defined as a list at iteration {iteration_count}, but atleast one item in it is an empty string.{Colors.RESET}")

        return ignore_list

    def parse_rules(self, content: dict[str, list[dict[str, Any]]]) -> list[Rule] | Error:
        """ Parse rules.json's content and return `Rule` objects. """
        
        if not isinstance(content, dict):
            return Error(f"{Colors.BRIGHT_RED}The rules file does not contain a valid toplevel structure! Must be a JSON object.{Colors.RESET}")
        elif not content:
            return Error(f"{Colors.BRIGHT_RED}The rules file contains an empty toplevel object.{Colors.RESET}")

        rules = content.get("rules")
        rule_objs = []
        
        if not isinstance(rules, list):
            return Error(f"{Colors.BRIGHT_RED}The 'rules' field in the rules file toplevel object is not an array!{Colors.RESET}")
        elif not rules:
            return Error(f"{Colors.BRIGHT_RED}No rules found.{Colors.RESET}")
        
        for i, rule in enumerate(rules):
            source = rule.get("source")
            destination = rule.get("destination")
            ignore = rule.get("ignore")

            result = self._check_source_and_destination(source, destination, i+1)
            if isinstance(result, Error):
                return result
            
            source, destination = result

            result = self._check_ignore_list(ignore, i+1)
            if isinstance(result, Error):
                return result
            
            ignore_list = result
                
            rule_objs.append(Rule(source, destination, ignore_list))

        return rule_objs