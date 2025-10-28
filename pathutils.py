from os.path import join, isfile, isdir, exists, basename, dirname
from os import remove, rmdir, listdir, makedirs, getcwd
from shutil import copy2, move

from re import compile, match

from typing import Generator, Union
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
         
        Returns file contents or None if file doesn't exist.
        
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
         
        Returns number of characters written. 
        
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

    def move_to(self, path: str) -> "File":
        """ Move file to a new location.

        Return moved file.
         
        Raises standard OS exceptions. """
        
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif not exists(self.path) or self.path is None:
            raise TypeError("File path must point to a valid location")

        new_path = move(self.path, path)
        self._refresh(new_path)

        return self

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
    
    An empty `path` will create the folder object using the script's directory. Or CWD if __file__ is missing. """

    def __init__(self, path: str="", ensure_exists: bool=False) -> None:
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        
        if not path:
            path = dirname(__file__) if "__file__" in globals() else getcwd()
        
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

    def __iter__(self) -> Generator[File, None, None]:
        return self.files()

    def files(self) -> Generator[File, None, None]:
        """ Return a generator of file objects present in the directory. """
        
        for file in listdir(self.path):
            full_fp = join(self.path, file)
            
            if isfile(full_fp):
                yield File(full_fp)

    def subfolders(self) -> Generator["Folder", None, None]:
        """ Return a generator object with subfolders present in the folder. """
        
        for dir in listdir(self.path):
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

    def delete_subfolder(self, name: str) -> list[File]:
        """ Delete a subfolder from the folder.
         
        `name` must be a folder name. 
        
        Returns deleted files. 
        
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

        return folder.delete()

    def delete(self) -> list[File]:
        """ Recursively delete the folder. 
        
        Returns successfully deleted files.

        Raises standard OS exceptions. """

        if not exists(self.path) or self.path is None:
            raise TypeError("Folder path must point to a valid location")
        
        deleted_files = []
    
        for file in self.files():
            file.delete()

            deleted_files.append(file)

        for subfolder in self.subfolders():
            other_files = subfolder.delete()

            deleted_files.extend(other_files)

        if not listdir(self.path):
            rmdir(self.path)

        return deleted_files

    def copy_to(self, path: str) -> tuple[list[File], list[File]]:
        """ Copy the folder to a new location. 
        
        Return a tuple with destination files and original files.

        Raises standard OS exceptions. """
        
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif not exists(self.path) or self.path is None:
            raise TypeError("Folder path must point to a valid location")

        destination_files, original_files = [], []

        makedirs(path, exist_ok=True)

        for file in self.files():
            source_file, new_file = file.copy_to(join(path, file.name))

            original_files.append(source_file)
            destination_files.append(new_file)

        for subfolder in self.subfolders():
            other_destination_files, other_original_files = subfolder.copy_to(join(path, subfolder.name))
        
            destination_files.extend(other_destination_files)
            original_files.extend(other_original_files)

        return destination_files, original_files

    def move_to(self, path: str) -> tuple[list[File], list[File]]:
        """ Move the folder to a new location. 
        
        Return a tuple with moved files and original files.

        Raises standard OS exceptions. """

        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        elif not exists(self.path) or self.path is None:
            raise TypeError("Folder path must point to a valid location")
        
        moved_files, original_files = [], []

        makedirs(path, exist_ok=True)
        
        for file in self.files():
            moved_file = file.move_to(join(path, file.name))

            moved_files.append(moved_file)
            original_files.append(file)

        for subfolder in self.subfolders():
            other_moved_files, other_original_files = subfolder.move_to(join(path, subfolder.name))

            moved_files.extend(other_moved_files)
            original_files.extend(other_original_files)

        if not listdir(self.path):
            rmdir(self.path)

        return moved_files, original_files

    def find(self, item: str, use_regex: bool=False) -> Union[File, "Folder"] | None:
        """ Find first occurrence of file or subfolder in the folder.
         
        Treat `item` as a regex pattern if `use_regex` is true.

        Returns a File or Folder object or None for no matches.
         
        Raises standard OS or regex exceptions. """

        if not isinstance(item, str):
            raise ValueError(f"Expected type str for argument item, not {item.__class__.__name__}")
        elif not exists(self.path) or self.path is None:
            raise TypeError("Folder path must point to a valid location")
        
        pattern = compile(item) if use_regex else None

        for file in self.files():
            if file.name == item if not pattern else match(pattern, file.name):
                return file
            
        for subfolder in self.subfolders():
            if subfolder.name == item if not pattern else match(pattern, subfolder.name):
                return subfolder
            
            obj = subfolder.find(item, use_regex)
            if obj: return obj
