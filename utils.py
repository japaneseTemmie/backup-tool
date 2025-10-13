from os.path import join, isfile, isdir, exists, basename
from os import remove, rmdir, listdir, makedirs
from shutil import copy2, move

from typing import Generator, Union
from types import NoneType

class File:
    """ File object.
    
    An object representing a file in the filesystem.
     
    Supports the following standard Python operations:
     
    bool(file) -> returns True if file exists """
    
    def __init__(self, path: str, ensure_exists: bool=False):
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

    def read(self) -> str | None:
        """ Read file contents.
         
        Returns file contents or None if file doesn't exist.
        
        Raises standard OS exceptions. """

        if self.path is not None:
            with open(self.path) as f:
                return f.read()

    def write(self, content: str) -> int:
        """ Write `content` to file.
         
        Returns number of characters written. 
        
        Raises standard OS exceptions. """
        
        if not isinstance(content, str):
            raise ValueError(f"Expected type str for argument content, not {content.__class__}")
        
        if self.path is not None:
            with open(self.path, "w") as f:
                return f.write(content)

        return 0

    def delete(self) -> None:
        """ Delete the file.
         
        Raises standard OS exceptions. """

        if self.path is not None:
            remove(self.path)

            self._refresh(None)

    def copy_to(self, path: str) -> None:
        """ Copy the file to a new location.
         
        Raises standard OS exceptions. """
        
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        
        if self.path is not None:
            copy2(self.path, path)

    def move_to(self, path: str) -> None:
        """ Move file to a new location.
         
        Raises standard OS exceptions. """
        
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        
        if self.path is not None:
            new_path = move(self.path, path)
            self._refresh(new_path)

    def _refresh(self, path: str | None=None) -> None:
        if not isinstance(path, (str, NoneType)):
            raise ValueError(f"Expected type str or None for argument path, not {path.__class__.__name__}")

        self.path = path
        self.name = basename(self.path) if self.path is not None else None

class Folder:
    """ Folder object.
     
    An object representing a directory in the filesystem.
     
    Supports the following standard Python operations:
     
    bool(folder) -> returns True if there are any files or subfolders
    iter(folder) -> returns an Iterator object that iterates over files in the folder. """

    def __init__(self, path: str, ensure_exists: bool=False):
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        
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
    
    def __len__(self) -> int:
        count = 0

        for _ in self:
            count += 1

        for subfolder in self.subfolders():
            count += len(subfolder)

        return count

    def __iter__(self) -> Generator[File, None, None]:
        for file in listdir(self.path):
            full_fp = join(self.path, file)
            
            if isfile(full_fp):
                yield File(full_fp)

    def subfolders(self) -> Generator["Folder", None, None]:
        for dir in listdir(self.path):
            full_fp = join(self.path, dir)
            
            if isdir(full_fp):
                yield Folder(full_fp)

    def add_file(self, name: str, content: str | None=None) -> str | None:
        """ Add a file to the folder.

        `name` must be a file name only, not path.
         
        Writes `content` to file if specified, too. 

        Returns new file's path or None.
        
        Raises standard OS exceptions. """

        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif not isinstance(name, (str, NoneType)):
            raise ValueError(f"Expected type str or NoneType for content argument, not {content.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a file name, not path")

        if self.path is not None:
            file_path = join(self.path, name)

            with open(file_path, "w") as f:
                if content is not None:
                    f.write(content)

            return file_path
        
    def delete_file(self, name: str) -> str | None:
        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a file name, not path")

        if self.path is not None:
            file_path = join(self.path, name)
            remove(file_path)

            return file_path

    def make_subfolder(self, name: str) -> str | None:
        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a directory name, not path")

        if self.path is not None:
            directory_path = join(self.path, name)
            makedirs(directory_path, exist_ok=True)

            return directory_path

    def delete_subfolder(self, name: str) -> str | None:
        if not isinstance(name, str):
            raise ValueError(f"Expected type str for name argument, not {name.__class__.__name__}")
        elif basename(name) != name:
            raise ValueError(f"name argument must be a directory name, not path")

        if self.path is not None:
            folder = Folder(join(self.path, name))

            return folder.delete()

    def delete(self) -> tuple[list[File], list["Folder"]]:
        """ Recursively delete the folder. 
        
        Returns successfully deleted files and folders.

        Raises standard OS exceptions. """

        if self.path is not None:
            deleted_files, deleted_subfolders = [], []
        
            for file in self:
                file.delete()

                deleted_files.append(file)

            for subfolder in self.subfolders():
                other_files, other_subfolders = subfolder.delete()

                deleted_files.extend(other_files)
                deleted_subfolders.extend(other_subfolders)

            if not listdir(self.path):
                rmdir(self.path)

            return deleted_files, deleted_subfolders

    def copy_to(self, path: str) -> tuple[list[File], list["Folder"]]:
        """ Copy the folder to a new location. 
        
        Returns successfully copied folders.

        Raises standard OS exceptions. """
        
        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")

        if self.path is not None:
            copied_files, copied_subfolders = [], []

            makedirs(path, exist_ok=True)

            for file in self:
                file.copy_to(join(path, file.name))

                copied_files.append(file)

            for subfolder in self.subfolders():
                other_files, other_subfolders = subfolder.copy_to(join(path, subfolder.name))
            
                copied_files.extend(other_files)
                copied_subfolders.extend(other_subfolders)

            return copied_files, copied_subfolders

    def move_to(self, path: str) -> tuple[list[File], list["Folder"]]:
        """ Move the folder to a new location. 
        
        Returns successfully moved folders.

        Raises standard OS exceptions. """

        if not isinstance(path, str):
            raise ValueError(f"Expected type str for argument path, not {path.__class__.__name__}")
        
        if self.path is not None:
            moved_files, moved_folders = [], []

            makedirs(path, exist_ok=True)
            
            for file in self:
                file.move_to(join(path, file.name))

                moved_files.append(file)

            for subfolder in self.subfolders():
                other_files, other_folders = subfolder.move_to(join(path, subfolder.name))

                moved_files.extend(other_files)
                moved_folders.extend(other_folders)

            if not listdir(self.path):
                rmdir(self.path)

            return moved_files, moved_folders

    def find(self, item: str) -> Union[File, "Folder"] | None:
        """ Find first occurrence of file or subfolder in the folder.
         
        Returns a File or Folder object or None for no matches. """

        if not isinstance(item, str):
            raise ValueError(f"Expected type str for argument item, not {item.__class__}")
        
        if self.path is not None:
            for file in self:
                if file.name == item:
                    return file
                
            for subfolder in self.subfolders():
                if subfolder.name == item:
                    return subfolder
                
                obj = subfolder.find(item)
                if obj: return obj
