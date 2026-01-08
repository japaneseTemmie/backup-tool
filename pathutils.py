from os.path import join, isfile, isdir, exists, basename, islink, getsize, getmtime, getatime, getctime, ismount
from os import remove, rmdir, listdir, makedirs, getcwd
from shutil import copy2, move
from hashlib import sha1, sha224, sha256, sha384, sha512

from re import Pattern

from typing import Generator, Union, Optional

class File:
    """ File object.
    
    An object representing a file in the filesystem.
     
    Supports the following standard Python operations:
     
    `bool(File)` -> returns True if file exists

    `iter(File)` -> returns a generator object for each line 
    
    An empty `path` will create a file named 'UntitledFile' in the CWD. 
    
    Raises ValueError and TypeError on invalid data. """

    def __init__(self, path: str="", ensure_exists: bool=False) -> None:
        if not isinstance(path, str):
            raise TypeError(f"Expected type str for argument path, not {path.__class__.__name__}")
        
        if not path:
            path = join(getcwd(), "UntitledFile")

        if not exists(path):

            if ensure_exists:
                open(path, "a").close() # do not use 'w' as this could wipe a file in a race condition
            else:
                raise ValueError(f"File {path} does not exist")
        elif not isfile(path):
            raise ValueError("path argument must be a file, not folder")

        self._path = path

    def __bool__(self) -> bool:
        return self._path is not None and isfile(self._path)

    def __iter__(self) -> Generator[str, None, None]:
        if self._path is None or not isfile(self._path):
            raise ValueError("path attribute must point to a file")

        with open(self._path) as f:
            for line in f:
                yield line

    @property
    def path(self) -> str | None:
        if self._path is None or not isfile(self._path):
            return None
        
        return self._path
    
    @property
    def name(self) -> str | None:
        if self._path is None or not isfile(self._path):
            return None
        
        return basename(self._path)
    
    @property
    def is_symlink(self) -> bool:
        if self._path is None or not isfile(self._path):
            return False
        
        return islink(self._path)
    
    @property
    def last_access_time(self) -> float | None:
        if self._path is None or not isfile(self._path):
            return None
        
        return getatime(self._path)
    
    @property
    def last_modified_time(self) -> float | None:
        if self._path is None or not isfile(self._path):
            return None
        
        return getmtime(self._path)
    
    @property
    def last_metadata_modified_time(self) -> float | None:
        if self._path is None or not isfile(self._path):
            return None
        
        return getctime(self._path)

    @property
    def size(self) -> int | None:
        if self._path is None or not isfile(self._path):
            return None
        
        return getsize(self._path)

    def read_bytes(self, bufsize: int=-1) -> bytes:
        """ Read file contents.
         
        Return file contents as bytes.

        `bufsize` must be either -1 (read whole file) or an integer counting the number of bytes to read.

        Raises standard OS exceptions and additional TypeError or ValueError. """

        if self._path is None or not isfile(self._path):
            raise ValueError("path attribute must point to a file")
        elif not isinstance(bufsize, int):
            raise TypeError(f"Expected type int for argument bufsize, not {bufsize.__class__.__name__}")
        
        with open(self._path, "rb") as f:
            return f.read(bufsize)

    def read_text(self, bufsize: int=-1, encoding: str="utf-8") -> str:
        """ Read file contents.
         
        Return file contents as string.
        
        `bufsize` must be either -1 (read whole file) or an integer counting the number of characters to read.

        `encoding` must be a valid encoding string.

        Raises standard OS exceptions and additional TypeError or ValueError. """

        if self._path is None or not isfile(self._path):
            raise ValueError("path attribute must point to a valid file")
        elif not isinstance(bufsize, int):
            raise TypeError(f"Expected type int for argument bufsize, not {bufsize.__class__.__name__}")
        elif not isinstance(encoding, str):
            raise TypeError(f"Expected type str for argument encoding, not {encoding.__class__.__name__}")

        with open(self._path, "r", encoding=encoding) as f:
            return f.read(bufsize)

    def write_bytes(self, content: bytes) -> int:
        """ Write `content` to file as bytes, if it exists.

        Returns number of bytes written. 
        
        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(content, bytes):
            raise TypeError(f"Expected type bytes for argument content, not {content.__class__}")
        elif self._path is None:
            raise ValueError("path attribute must point to a file")

        with open(self._path, "wb") as f:
            return f.write(content)
        
    def write_text(self, content: str, encoding: str="utf-8") -> int:
        """ Write `content` to file as text, if it exists.

        Returns number of characters written. 
        
        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(content, str):
            raise TypeError(f"Expected type str for argument content, not {content.__class__}")
        elif not isinstance(encoding, str):
            raise TypeError(f"Expected type str for argument encoding, not {encoding.__class__.__name__}")
        elif self._path is None:
            raise ValueError("path attribute must point to a file")

        with open(self._path, "w", encoding=encoding) as f:
            return f.write(content)

    def grep(self, item: str | Pattern) -> list[str]:
        """ Find occurrences of `item` in each line in the file.
         
        `item` can either be a string to compare a line to, or a `re.Pattern` object to match to a line.

        Both methods search the entire string.

        Return a list of string matches.
         
        Raises standard OS and regex exceptions and additional ValueError. """
        
        matches = []
        is_regex = isinstance(item, Pattern)
        
        for line in self:
            if not is_regex:
                if item in line:
                    matches.append(line)
            else:
                if item.search(line):
                    matches.append(line)
        
        return matches

    def delete(self) -> None:
        """ Delete the file if it exists.

        After this operation, this file's path becomes `None`, effectively rendering the object useless.
         
        Raises standard OS exceptions and additional ValueError. """

        if self._path is None or not isfile(self._path):
            raise ValueError("path attribute must point to a file")

        try:
            remove(self._path)
        except FileNotFoundError:
            pass

        self._path = None

    def copy_to(self, path: str) -> tuple["File", "File"]:
        """ Copy the file to a new location.
         
        Returns source file and new file.

        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(path, str):
            raise TypeError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif self._path is None or not isfile(self._path):
            raise ValueError("path attribute must point to a file")
        
        new_path = copy2(self._path, path)

        return self, File(new_path)

    def move_to(self, path: str) -> None:
        """ Move file to a new location.

        After this operation, this file's path is refreshed to the new path.
         
        Raises standard OS exceptions and additional ValueError and TypeError. """
        
        if not isinstance(path, str):
            raise TypeError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif self._path is None or not isfile(self._path):
            raise ValueError("path attribute must point to a file")

        new_path = move(self._path, path)
        self._path = new_path

    def hash(self, hash_type: str="sha256") -> str:
        """ Return a hash of the file.

        `hash_type` must be either `sha1`, `sha224`, `sha256`, `sha384` or `sha512`. Defaults to `sha256`
        
        Raises standard OS, Hashlib exceptions and additional ValueError. """

        valid_hash_types = {
            "sha1": sha1,
            "sha224": sha224,
            "sha256": sha256,
            "sha384": sha384,
            "sha512": sha512
        }

        if self._path is None or not isfile(self._path):
            raise ValueError("path must point to a valid file")
        elif hash_type not in valid_hash_types:
            raise ValueError(f"Invalid hash type.")

        buf_size = 8192
        file_hash = valid_hash_types[hash_type]()

        with open(self._path, "rb") as f:
            while True:
                buf = f.read(buf_size)
                if not buf:
                    break

                file_hash.update(buf)

        return file_hash.hexdigest()

class Folder:
    """ Folder object.
     
    An object representing a directory in the filesystem.
     
    Supports the following standard Python operations:
     
    `bool(Folder)` -> returns True if the folder exists in the filesystem.
    
    `iter(Folder)` -> returns an iterator of the folder's files and directories.
    
    An empty `path` will create a folder named 'UntitledFolder' in the CWD. 
    
    Raises ValueError or TypeError on invalid data. """

    def __init__(self, path: str="", ensure_exists: bool=False) -> None:
        if not isinstance(path, str):
            raise TypeError(f"Expected type str for argument path, not {path.__class__.__name__}")
        
        if not path:
            path = join(getcwd(), "UntitledFolder")
        
        if not exists(path):

            if ensure_exists:
                makedirs(path, exist_ok=True)
            else:
                raise ValueError(f"Directory {path} does not exist")
        elif not isdir(path):
            raise ValueError(f"Path must be a directory, not a file")

        self._path = path

    def __bool__(self) -> bool:
        return self._path is not None and isdir(self._path)

    def __iter__(self) -> Generator[Union[File, "Folder"], None, None]:
        if self._path is None or not isdir(self._path):
            raise ValueError("path attribute must point to a folder")

        entries = sorted(listdir(self._path)) # ensure this is sorted as listdir's return is arbitrary
        for item in entries:
            full_fp = join(self._path, item)
            
            if isfile(full_fp):
                yield File(full_fp)
            elif isdir(full_fp):
                yield Folder(full_fp)

    @property
    def path(self) -> str | None:
        if self._path is None or not isdir(self._path):
            return None
        
        return self._path
    
    @property
    def name(self) -> str | None:
        if self._path is None or not isdir(self._path):
            return None
        
        return basename(self._path)
    
    @property
    def is_mountpoint(self) -> bool:
        if self._path is None or not isdir(self._path):
            return False
        
        return ismount(self._path)

    @property
    def is_symlink(self) -> bool:
        if self._path is None or not isdir(self._path):
            return False
        
        return islink(self._path)

    def files(self) -> Generator[File, None, None]:
        """ Return a generator of file objects present in the directory. """
        if self._path is None or not isdir(self._path):
            raise ValueError("path attribute must point to a folder")
        
        entries = sorted(listdir(self._path))
        for file in entries:
            full_fp = join(self._path, file)
            
            if isfile(full_fp):
                yield File(full_fp)

    def subfolders(self) -> Generator["Folder", None, None]:
        """ Return a generator object with subfolders present in the folder. """
        if self._path is None or not isdir(self._path):
            raise ValueError("path attribute must point to a folder")
        
        entries = sorted(listdir(self._path))
        for dir in entries:
            full_fp = join(self._path, dir)
            
            if isdir(full_fp):
                yield Folder(full_fp)

    def add_file(self, name: str) -> File:
        """ Add a file to the folder, if it doesn't exist.

        `name` must be a file name only, not path.

        Return new/existing file.
        
        Raises standard OS exceptions and additional ValueError and TypeError. """

        if not isinstance(name, str):
            raise TypeError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a file name, not path")
        elif self._path is None or not isdir(self._path):
            raise ValueError("path attribute must point to a folder")
        
        file_path = join(self._path, name)
        new_file = File(file_path, True)

        return new_file
        
    def delete_file(self, name: str) -> None:
        """ Delete a file from the folder.
         
        `name` must be a file name only.
        
        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(name, str):
            raise TypeError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a file name, not path")
        elif self._path is None or not isdir(self._path):
            raise ValueError("path attribute must point to a folder")

        file_path = join(self._path, name)
        if isdir(file_path):
            raise ValueError("name argument must point to a file, not directory")

        file = File(file_path)
        file.delete()

    def make_subfolder(self, name: str) -> "Folder":
        """ Create a subfolder in the folder.
         
        `name` must be a folder name.
         
        Returns the created / existing folder.
         
        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(name, str):
            raise TypeError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a directory name, not path")
        elif self._path is None or not isdir(self._path):
            raise ValueError("path attribute must point to a folder")

        directory_path = join(self._path, name)

        return Folder(directory_path, True)

    def delete_subfolder(self, name: str) -> None:
        """ Delete a subfolder from the folder.
         
        `name` must be a folder name. 
        
        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(name, str):
            raise TypeError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a directory name, not path")
        elif self._path is None or not isdir(self._path):
            raise ValueError("path attribute must point to a folder")

        dir_path = join(self._path, name)
        if isfile(dir_path):
            raise ValueError("name argument must point to a directory, not file")

        folder = Folder(dir_path)
        folder.delete()

    def delete(self) -> None:
        """ Recursively delete the folder.

        After this operation, this folder's path becomes `None`, effectively rendering the object useless.

        Raises standard OS exceptions and additional ValueError. """

        if self._path is None or not isdir(self._path):
            raise ValueError("path attribute must point to a folder")
        elif self.is_symlink: # remove link itself, do not recurse into it
            remove(self._path)
            self._path = None

            return
        
        for file in self.files():
            try:
                file.delete()
            except FileNotFoundError:
                continue # deleted already, so just keep going

        for subfolder in self.subfolders():
            subfolder.delete()

        if not listdir(self._path):
            rmdir(self._path)

        self._path = None

    def copy_to(self, path: str) -> list[tuple[File, File]]:
        """ Copy the folder's contents to a new location. 
        
        Return a list of tuples with original file and destination file.

        Raises standard OS exceptions and additional ValueError or TypeError. """
        
        if not isinstance(path, str):
            raise TypeError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif self._path is None or not isdir(self._path):
            raise ValueError("path attribute must point to a folder")

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
        """ Move the folder's contents to a new location. 
        
        After this operation, the current object's path is refreshed to the new given path.

        Return moved files.

        Raises standard OS exceptions and additional ValueError or TypeError. """

        if not isinstance(path, str):
            raise TypeError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif self._path is None or not isdir(self._path):
            raise ValueError("path attribute must point to a folder")
        
        moved_files = []

        makedirs(path, exist_ok=True)
        
        for file in self.files():
            file.move_to(join(path, file.name))

            moved_files.append(file)

        for subfolder in self.subfolders():
            other_moved_files = subfolder.move_to(join(path, subfolder.name))

            moved_files.extend(other_moved_files)

        if not listdir(self._path):
            rmdir(self._path)

        self._path = path

        return moved_files

    def find(self, item: str | Pattern) -> list[Optional[Union[File, "Folder"]]]:
        """ Find files or subfolders in the folder.
         
        `item` can either be a string to compare a file name to, or a `re.Pattern` object to match to a file name.

        Both methods search the entire file names.

        Return a list of `File` or `Folder` objects.
         
        Raises standard OS and regex exceptions and additional ValueError or TypeError. """

        if not isinstance(item, (str, Pattern)):
            raise TypeError(f"Expected type str or re.Pattern for argument item, not {item.__class__.__name__}")
        elif self._path is None or not isdir(self._path):
            raise ValueError("path attribute must point to a folder")

        matches = []
        is_regex = isinstance(item, Pattern)

        for file in self.files():
            if not is_regex:
                if item in file.name:
                    matches.append(file)
            else:
                if item.search(file.name):
                    matches.append(file)
            
        for subfolder in self.subfolders():
            if not is_regex:
                if item in subfolder.name:
                    matches.append(subfolder)
            else:
                if item.search(subfolder.name):
                    matches.append(subfolder)
            
            other_matches = subfolder.find(item)
            if other_matches: matches.extend(other_matches)

        return matches
