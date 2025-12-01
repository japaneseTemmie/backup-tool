from os.path import join, isfile, isdir, exists, basename
from os import remove, rmdir, listdir, makedirs, getcwd
from shutil import copy2, move
from hashlib import sha1, sha224, sha256, sha384, sha512
from re import Pattern
from typing import Generator, Union, Optional
from types import NoneType

class File:
    """ File object.
    
    An object representing a file in the filesystem.
     
    Supports the following standard Python operations:
     
    bool(file) -> returns True if file exists """
    
    def __init__(self, path: str, ensure_exists: bool=False) -> None:
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        
        if not exists(path):

            if ensure_exists:
                open(path, "w").close()
            else:
                raise ValueError(f"File {path} does not exist")
        elif not isfile(path):
            raise ValueError("path argument must be a file, not folder")

        self.path = path
        self.name = basename(self.path)

    def __bool__(self) -> bool:
        return self.path is not None and isfile(self.path)

    def read(self, mode: str="r") -> str | bytes:
        """ Read file contents.
         
        Return file contents as string or bytes.
        
        `mode` must be either 'r' or 'rb'.

        Raises standard OS exceptions. """

        if not exists(self.path) or self.path is None:
            raise TypeError("File path must point to a valid location")
        elif mode not in {"r", "rb"}:
            raise ValueError(f"Unsupported mode: {mode}")

        with open(self.path, mode) as f:
            return f.read()

    def write(self, content: str | bytes) -> int:
        """ Write `content` to file as string or bytes, if it exists.
         
        Returns number of characters or bytes written. 
        
        Raises standard OS exceptions. """
        
        if not isinstance(content, (str, bytes)):
            raise ValueError(f"Expected type str for argument content, not {content.__class__}")
        elif self.path is None:
            raise TypeError("File path must point to a valid location")
        
        mode = "wb" if isinstance(content, bytes) else "w"

        with open(self.path, mode) as f:
            return f.write(content)

    def delete(self) -> None:
        """ Delete the file if it exists.
         
        Raises standard OS exceptions. """

        if not exists(self.path) or self.path is None:
            raise TypeError("File path must point to a valid location")

        remove(self.path)
        self._refresh(None)

    def copy_to(self, path: str) -> tuple["File", "File"]:
        """ Copy the file to a new location.
         
        Returns source file and new file.

        Raises standard OS exceptions. """
        
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif not exists(self.path) or self.path is None:
            raise TypeError("File path must point to a valid location")
        
        new_path = copy2(self.path, path)

        return self, File(new_path)

    def move_to(self, path: str) -> None:
        """ Move file to a new location.
         
        Raises standard OS exceptions. """
        
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif not exists(self.path) or self.path is None:
            raise TypeError("File path must point to a valid location")

        new_path = move(self.path, path)
        self._refresh(new_path)

    def hash(self, hash_type: str="sha256") -> str:
        """ Return a hash of the file.

        `hash_type` must be `sha1`, `sha224`, `sha256`, `sha384` or `sha512`. Defaults to `sha256`
        
        Raises standard OS / Hashlib exceptions. """

        valid_hash_types = {
            "sha1": sha1,
            "sha224": sha224,
            "sha256": sha256,
            "sha384": sha384,
            "sha512": sha512
        }

        if self.path is None or not exists(self.path):
            raise TypeError("File path must point to a valid location")
        elif hash_type not in valid_hash_types:
            raise ValueError(f"Invalid hash type.")

        buf_size = 8192
        file_hash = valid_hash_types.get(hash_type, sha256)()

        with open(self.path, "rb") as f:
            while True:
                buf = f.read(buf_size)
                if not buf:
                    break

                file_hash.update(buf)

        return file_hash.hexdigest()

    def _refresh(self, path: str | None=None) -> None:
        if not isinstance(path, (str, NoneType)):
            raise ValueError(f"Expected type str or None for argument path, not {path.__class__.__name__}")

        self.path = path
        self.name = basename(self.path) if self.path is not None else None

class Folder:
    """ Folder object.
     
    An object representing a directory in the filesystem.
     
    Supports the following standard Python operations:
     
    bool(Folder) -> returns True if there are any files or subfolders
    iter(Folder) -> returns an iterator of the folder's files.
    
    An empty `path` will create the folder in the CWD. """

    def __init__(self, path: str="", ensure_exists: bool=False) -> None:
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        
        if not path:
            path = getcwd()
        
        if not exists(path):

            if ensure_exists:
                makedirs(path, exist_ok=True)
            else:
                raise ValueError(f"File {path} does not exist")
        elif not isdir(path):
            raise ValueError(f"path must be a directory, not a file")

        self.path = path
        self.name = basename(self.path)

    def __bool__(self) -> bool:
        return len(listdir(self.path)) > 0

    def __iter__(self) -> Generator[Union[File, "Folder"], None, None]:
        entries = sorted(listdir(self.path))
        for item in entries:
            full_fp = join(self.path, item)
            
            if isfile(full_fp):
                yield File(full_fp)
            elif isdir(full_fp):
                yield Folder(full_fp)

    def files(self) -> Generator[File, None, None]:
        """ Return a generator of file objects present in the directory. """
        
        entries = sorted(listdir(self.path))
        for file in entries:
            full_fp = join(self.path, file)
            
            if isfile(full_fp):
                yield File(full_fp)

    def subfolders(self) -> Generator["Folder", None, None]:
        """ Return a generator object with subfolders present in the folder. """
        
        entries = sorted(listdir(self.path))
        for dir in entries:
            full_fp = join(self.path, dir)
            
            if isdir(full_fp):
                yield Folder(full_fp)

    def add_file(self, name: str, content: str | None=None) -> File:
        """ Add a file to the folder.

        `name` must be a file name only, not path.
         
        Write `content` to file if specified, too. 

        If file already exists, return that file.

        Returns new file.
        
        Raises standard OS exceptions. """

        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif not isinstance(content, (str, NoneType)):
            raise ValueError(f"Expected type str or NoneType for content argument, not {content.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a file name, not path")
        elif not exists(self.path) or self.path is None:
            raise TypeError("Folder path must point to a valid location")
            
        file_path = join(self.path, name)

        new_file = File(file_path, True)
        if content is not None:
            new_file.write(content)

        return new_file
        
    def delete_file(self, name: str) -> None:
        """ Delete a file from the folder.
         
        `name` must be a file name only.
        
        Raises standard OS exceptions. """
        
        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a file name, not path")
        elif self.path is None or not exists(self.path):
            raise TypeError("Folder path must point to a valid location")

        file_path = join(self.path, name)
        if isdir(file_path):
            raise ValueError("name argument must point to a file, not directory")

        file = File(file_path)
        file.delete()

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

        return Folder(directory_path, True)

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

        folder = Folder(dir_path)
        folder.delete()

    def delete(self) -> None:
        """ Recursively delete the folder. 

        Raises standard OS exceptions. """

        if not exists(self.path) or self.path is None:
            raise TypeError("Folder path must point to a valid location")
    
        for file in self.files():
            file.delete()

        for subfolder in self.subfolders():
            subfolder.delete()

        if not listdir(self.path):
            rmdir(self.path)

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
            source_file, new_file = file.copy_to(join(path, file.name))
            pairs.append((source_file, new_file))

        for subfolder in self.subfolders():
            other_pairs = subfolder.copy_to(join(path, subfolder.name), exclude_files, exclude_directories)
            pairs.extend(other_pairs)

        return pairs

    def move_to(self, path: str) -> list[File]:
        """ Move the folder to a new location. 
        
        Return moved files.

        Raises standard OS exceptions. """

        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif not exists(self.path) or self.path is None:
            raise TypeError("Folder path must point to a valid location")
        
        moved_files = []

        makedirs(path, exist_ok=True)
        
        for file in self.files():
            file.move_to(join(path, file.name))

            moved_files.append(file)

        for subfolder in self.subfolders():
            other_moved_files = subfolder.move_to(join(path, subfolder.name))

            moved_files.extend(other_moved_files)

        if not listdir(self.path):
            rmdir(self.path)

        return moved_files

    def find(self, item: str | Pattern) -> list[Optional[Union[File, "Folder"]]]:
        """ Find first occurrence of file or subfolder in the folder.
         
        `item` can either be a string to compare a file name to, or a `re.Pattern` object to match to a file name.

        Return a list of `File` or `Folder` objects.
         
        Raises standard OS or regex exceptions. """

        if not isinstance(item, (str, Pattern)):
            raise ValueError(f"Expected type str or re.Pattern for argument item, not {item.__class__.__name__}")
        elif not exists(self.path) or self.path is None:
            raise TypeError("Folder path must point to a valid location")

        matches = []
        is_regex = isinstance(item, Pattern)

        for file in self.files():
            if not is_regex:
                if file.name == item:
                    matches.append(file)
            else:
                if item.match(file.name):
                    matches.append(file)
            
        for subfolder in self.subfolders():
            if not is_regex:
                if subfolder.name == item:
                    matches.append(subfolder)
            else:
                if item.match(subfolder.name):
                    matches.append(subfolder)
            
            other_matches = subfolder.find(item)
            if other_matches: matches.extend(other_matches)

        return matches
