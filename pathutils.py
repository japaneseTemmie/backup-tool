from os.path import join, isfile, isdir, exists, basename, islink, getsize, getmtime, getatime, getctime, ismount
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
     
    bool(file) -> returns True if file exists
    iter(file) -> returns a generator object for each line 
    
    An empty `path` will create the file in the CWD. """

    def __init__(self, path: str="", ensure_exists: bool=False) -> None:
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        
        if not path:
            path = join(getcwd(), "UntitledFile")

        if not exists(path):

            if ensure_exists:
                open(path, "w").close()
            else:
                raise ValueError(f"File {path} does not exist")
        elif not isfile(path):
            raise ValueError("path argument must be a file, not folder")

        self.path = path
        self.name = basename(self.path)

        self.is_symlink = islink(self.path)

        self.last_access_time = getatime(self.path)
        self.last_modified_time = getmtime(self.path)
        self.last_metadata_modified_time = getctime(self.path)

        self.size = getsize(self.path)

    def __bool__(self) -> bool:
        return self.path is not None and isfile(self.path)

    def __iter__(self) -> Generator[str, None, None]:
        if self.path is None or not isfile(self.path):
            raise ValueError("File path must point to a valid location")

        with open(self.path) as f:
            for line in f:
                yield line

    def read_bytes(self, bufsize: int=-1) -> bytes:
        """ Read file contents.
         
        Return file contents as bytes.

        `bufsize` must be either -1 (read whole file) or an integer counting the number of bytes to read.

        Raises standard OS exceptions and additional TypeError or ValueError. """

        if self.path is None or not isfile(self.path):
            raise TypeError("File path must point to a valid location")
        elif not isinstance(bufsize, int):
            raise ValueError(f"Expected type int for argument bufsize, not {bufsize.__class__.__name__}")
        
        with open(self.path, "rb") as f:
            return f.read(bufsize)

    def read_text(self, bufsize: int=-1, encoding: str="utf-8") -> str | bytes:
        """ Read file contents.
         
        Return file contents as string.
        
        `bufsize` must be either -1 (read whole file) or an integer counting the number of characters to read.

        `encoding` must be a valid encoding string.

        Raises standard OS exceptions and additional TypeError or ValueError. """

        if self.path is None or not isfile(self.path):
            raise TypeError("File path must point to a valid location")
        elif not isinstance(bufsize, int):
            raise ValueError(f"Expected type int for argument bufsize, not {bufsize.__class__.__name__}")
        elif not isinstance(encoding, str):
            raise ValueError(f"Expected type str for argument encoding, not {encoding.__class__.__name__}")

        with open(self.path, "r", bufsize, encoding) as f:
            return f.read(bufsize)

    def write_bytes(self, content: bytes) -> int:
        """ Write `content` to file as bytes, if it exists.

        Returns number of bytes written. 
        
        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(content, bytes):
            raise ValueError(f"Expected type bytes for argument content, not {content.__class__}")
        elif self.path is None:
            raise TypeError("File path must point to a valid location")

        with open(self.path, "wb") as f:
            return f.write(content)
        
    def write_text(self, content: str, encoding: str="utf-8") -> int:
        """ Write `content` to file as text, if it exists.

        Returns number of characters written. 
        
        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(content, str):
            raise ValueError(f"Expected type str for argument content, not {content.__class__}")
        elif not isinstance(encoding, str):
            raise ValueError(f"Expected type str for argument encoding, not {encoding.__class__.__name__}")
        elif self.path is None:
            raise TypeError("File path must point to a valid location")

        with open(self.path, "w", encoding=encoding) as f:
            return f.write(content)

    def find(self, item: str | Pattern) -> list[str]:
        """ Find first occurrence of item in each line in the file.
         
        `item` can either be a string to compare a line to, or a `re.Pattern` object to match to a line.

        Return a list of string matches.
         
        Raises standard OS and regex exceptions and additional ValueError. """
        
        matches = []
        is_regex = isinstance(item, Pattern)
        
        for line in self:
            if not is_regex:
                if line == item:
                    matches.append(line)
            else:
                if item.match(line):
                    matches.append(line)
        
        return matches

    def delete(self) -> None:
        """ Delete the file if it exists.

        After this operation, this file's attributes become `None`, effectively rendering the object useless.
         
        Raises standard OS exceptions and additional TypeError. """

        if self.path is None or not isfile(self.path):
            raise TypeError("File path must point to a valid location")

        remove(self.path)
        self.__refresh(None)

    def copy_to(self, path: str) -> tuple["File", "File"]:
        """ Copy the file to a new location.
         
        Returns source file and new file.

        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif self.path is None or not isfile(self.path):
            raise TypeError("File path must point to a valid location")
        
        new_path = copy2(self.path, path)

        return self, File(new_path)

    def move_to(self, path: str) -> None:
        """ Move file to a new location.

        After this operation, this file's path is refreshed to the new path.
         
        Raises standard OS exceptions and additional ValueError and TypeError. """
        
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif self.path is None or not isfile(self.path):
            raise TypeError("File path must point to a valid location")

        new_path = move(self.path, path)
        self.__refresh(new_path)

    def hash(self, hash_type: str="sha256") -> str:
        """ Return a hash of the file.

        `hash_type` must be `sha1`, `sha224`, `sha256`, `sha384` or `sha512`. Defaults to `sha256`
        
        Raises standard OS, Hashlib exceptions and additional ValueError and TypeError. """

        valid_hash_types = {
            "sha1": sha1,
            "sha224": sha224,
            "sha256": sha256,
            "sha384": sha384,
            "sha512": sha512
        }

        if self.path is None or not isfile(self.path):
            raise TypeError("File path must point to a valid location")
        elif hash_type not in valid_hash_types:
            raise ValueError(f"Invalid hash type.")

        buf_size = 8192
        file_hash = valid_hash_types[hash_type]()

        with open(self.path, "rb") as f:
            while True:
                buf = f.read(buf_size)
                if not buf:
                    break

                file_hash.update(buf)

        return file_hash.hexdigest()

    def __refresh(self, path: str | None=None) -> None:
        if not isinstance(path, (str, NoneType)):
            raise ValueError(f"Expected type str or None for argument path, not {path.__class__.__name__}")

        if path is None:
            self.path = None
            self.name = None
            self.is_symlink = None
            self.last_access_time = None
            self.last_metadata_modified_time = None
            self.last_modified_time = None
            self.size = None
        else:
            if not isfile(path):
                raise ValueError(f"Expected file for argument path")
            
            self.path = path
            self.name = basename(self.path)

            self.is_symlink = islink(self.path)

            self.last_access_time = getatime(self.path)
            self.last_modified_time = getmtime(self.path)
            self.last_metadata_modified_time = getctime(self.path)

            self.size = getsize(self.path)

class Folder:
    """ Folder object.
     
    An object representing a directory in the filesystem.
     
    Supports the following standard Python operations:
     
    bool(Folder) -> returns True if the folder exists in the filesystem.
    iter(Folder) -> returns an iterator of the folder's files and directories.
    
    An empty `path` will create the folder in the CWD. """

    def __init__(self, path: str="", ensure_exists: bool=False) -> None:
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        
        if not path:
            path = join(getcwd(), "UntitledFolder")
        
        if not exists(path):

            if ensure_exists:
                makedirs(path, exist_ok=True)
            else:
                raise ValueError(f"Directory {path} does not exist")
        elif not isdir(path):
            raise ValueError(f"Path must be a directory, not a file")

        self.path = path
        self.name = basename(self.path)

        self.is_mountpoint = ismount(self.path)

    def __bool__(self) -> bool:
        return self.path is not None and isdir(self.path)

    def __iter__(self) -> Generator[Union[File, "Folder"], None, None]:
        if self.path is None or not isdir(self.path):
            raise ValueError("Folder path must point to a valid location")

        entries = sorted(listdir(self.path))
        for item in entries:
            full_fp = join(self.path, item)
            
            if isfile(full_fp):
                yield File(full_fp)
            elif isdir(full_fp):
                yield Folder(full_fp)

    def __refresh(self, path: str | None=None) -> None:
        if not isinstance(path, (str, NoneType)):
            raise ValueError(f"Expected type str or None for argument path, not {path.__class__.__name__}")

        if path is None:
            self.path = None
            self.name = None
            self.is_mountpoint = None
        else:
            if not isdir(path):
                raise ValueError(f"Expected directory for argument path")
            
            self.path = path
            self.name = basename(self.path)

            self.is_mountpoint = ismount(self.path)

    def files(self) -> Generator[File, None, None]:
        """ Return a generator of file objects present in the directory. """
        if self.path is None or not isdir(self.path):
            raise ValueError("Folder path must point to a valid location")
        
        entries = sorted(listdir(self.path))
        for file in entries:
            full_fp = join(self.path, file)
            
            if isfile(full_fp):
                yield File(full_fp)

    def subfolders(self) -> Generator["Folder", None, None]:
        """ Return a generator object with subfolders present in the folder. """
        if self.path is None or not isdir(self.path):
            raise ValueError("Folder path must point to a valid location")
        
        entries = sorted(listdir(self.path))
        for dir in entries:
            full_fp = join(self.path, dir)
            
            if isdir(full_fp):
                yield Folder(full_fp)

    def add_file(self, name: str) -> File:
        """ Add a file to the folder.

        `name` must be a file name only, not path.

        Return new/existing file.
        
        Raises standard OS exceptions and additional ValueError and TypeError. """

        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a file name, not path")
        elif self.path is None or not isdir(self.path):
            raise TypeError("Folder path must point to a valid location")
        
        file_path = join(self.path, name)
        new_file = File(file_path, True)

        return new_file
        
    def delete_file(self, name: str) -> None:
        """ Delete a file from the folder.
         
        `name` must be a file name only.
        
        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a file name, not path")
        elif self.path is None or not isdir(self.path):
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
         
        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a directory name, not path")
        elif self.path is None or not isdir(self.path):
            raise TypeError("Folder path must point to a valid location")

        directory_path = join(self.path, name)

        return Folder(directory_path, True)

    def delete_subfolder(self, name: str) -> None:
        """ Delete a subfolder from the folder.
         
        `name` must be a folder name. 
        
        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a directory name, not path")
        elif self.path is None or not isdir(self.path):
            raise TypeError("Folder path must point to a valid location")

        dir_path = join(self.path, name)
        if isfile(dir_path):
            raise ValueError("name argument must point to a directory, not file")

        folder = Folder(dir_path)
        folder.delete()

    def delete(self) -> None:
        """ Recursively delete the folder.

        After this operation, this folder's attributes become `None`. Effectively rendering the object useless.

        Raises standard OS exceptions and additional TypeError. """

        if self.path is None or not isdir(self.path):
            raise TypeError("Folder path must point to a valid location")
        
        for file in self.files():
            file.delete()

        for subfolder in self.subfolders():
            subfolder.delete()

        if not listdir(self.path):
            rmdir(self.path)

        self.__refresh(None)

    def copy_to(self, path: str) -> list[tuple[File, File]]:
        """ Copy the folder to a new location. 
        
        Return a list of tuples with original file and destination file.

        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif self.path is None or not isdir(self.path):
            raise TypeError("Folder path must point to a valid location")

        pairs = []

        makedirs(path, exist_ok=True)

        for file in self.files():
            source_file, new_file = file.copy_to(join(path, file.name))
            pairs.append((source_file, new_file))

        for subfolder in self.subfolders():
            other_pairs = subfolder.copy_to(join(path, subfolder.name))
            pairs.extend(other_pairs)

        return pairs

    def move_to(self, path: str) -> list[File]:
        """ Move the folder to a new location. 
        
        Return moved files.

        Raises standard OS exceptions and additional ValueError or TypeError. """

        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif self.path is None or not isdir(self.path):
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

        self.__refresh(path)

        return moved_files

    def find(self, item: str | Pattern) -> list[Optional[Union[File, "Folder"]]]:
        """ Find first occurrence of file or subfolder in the folder.
         
        `item` can either be a string to compare a file name to, or a `re.Pattern` object to match to a file name.

        Return a list of `File` or `Folder` objects.
         
        Raises standard OS and regex exceptions and additional ValueError or TypeError. """

        if not isinstance(item, (str, Pattern)):
            raise ValueError(f"Expected type str or re.Pattern for argument item, not {item.__class__.__name__}")
        elif self.path is None or not isdir(self.path):
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
