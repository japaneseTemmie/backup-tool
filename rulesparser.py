from constants import RULES_JSON_PATH
from error import Error
from colors import Colors

from os.path import isfile, isdir, isabs
from json import load, JSONDecodeError

class Rule:
    """ Generic rule object to cache properties for each transfer. """
    
    def __init__(self, source: str, destination: str, ignore: list[str]):
        self.source = source
        self.destination = destination
        self.ignore = ignore

class RulesParser:
    def get_file_contents(self) -> dict | Error:
        """ Try to open the rules.json file. 
        
        Return file contents on success, otherwise an `Error` object. """
        
        if not isfile(RULES_JSON_PATH):
            return Error(f"{Colors.BRIGHT_RED}The file rules.json does not exist!{Colors.RESET}")
        
        try:
            with open(RULES_JSON_PATH) as f:
                return load(f)
        except OSError as e:
            return Error(f"{Colors.BRIGHT_RED}Unable to open file due to error:\n{e}{Colors.RESET}")
        except JSONDecodeError as e:
            return Error(f"{Colors.BRIGHT_RED}Unable to parse JSON file due to error:\n{e}{Colors.RESET}")
    
    def _check_destination(self, destination: str, iteration_count: int) -> str | Error:
        """ Check if destination is valid. 
        
        Return destination if checks are passed, otherwise an `Error` object. """

        if not destination:
            return Error(f"{Colors.BRIGHT_RED}Destination is not defined at iteration {iteration_count}{Colors.RESET}")
        elif not isinstance(destination, str):
            return Error(f"{Colors.BRIGHT_RED}Destination is defined as {destination.__class__.__name__} at iteration {iteration_count}, expected string{Colors.RESET}")
        elif not isabs(destination):
            return Error(f"{Colors.BRIGHT_RED}Destination path must be an absolute path. (begins from root to destination){Colors.RESET}")
        
        return destination

    def _check_source(self, source: str, iteration_count: int) -> str | Error:
        """ Check if source is valid.
        
        Return source if checks are passed, otherwise `Error` object. """
        
        if not isinstance(source, str):
            return Error(f"{Colors.BRIGHT_RED}Source is defined as {source.__class__.__name__} at iteration {iteration_count}, expected string{Colors.RESET}")
        elif not source:
            return Error(f"{Colors.BRIGHT_RED}Source is not defined at iteration {iteration_count}{Colors.RESET}")
        elif not isabs(source):
            return Error(f"{Colors.BRIGHT_RED}Source path must be an absolute path at iteration {iteration_count}. (begins from root to source directory){Colors.RESET}")
        elif not isdir(source):
            return Error(f"{Colors.BRIGHT_RED}Source defined at iteration {iteration_count} is not a directory{Colors.RESET}")

        return source

    def _check_source_and_destination(self, source: str, destination: str, iteration_count: int) -> tuple[str, str] | Error:
        """ Check both source and destination. 
        
        Return a tuple with source and destination if checks are passed, otherwise an `Error` object. """
        
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
            return Error(f"{Colors.BRIGHT_RED}Ignore attribute is defined as a list, but atleast one item in it is not a string representing a glob pattern at iteration {iteration_count}{Colors.RESET}.")

        return ignore_list

    def parse_rules(self, content: dict[str, list[dict]]) -> list[Rule] | Error:
        """ Parse rules.json's content and return `Rule` objects. """
        
        rules = content.get("rules")
        rule_objs = []
        
        if not content or rules is None:
            return Error("No rules found.")
        
        for i, rule in enumerate(rules):
            source = rule.get("source")
            destination = rule.get("destination")
            ignore = rule.get("ignore")

            result = self._check_source_and_destination(source, destination, i)
            if isinstance(result, Error):
                return result
            
            source, destination = result

            result = self._check_ignore_list(ignore, i)
            if isinstance(result, Error):
                return result
            
            ignore_files = result
                
            rule_objs.append(Rule(source, destination, ignore_files))

        return rule_objs