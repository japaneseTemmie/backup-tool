# Backup tool

Command-line tool to make copies of folders to specified directories. Useful for backups.

Simply copies specified files to another destination and verifies their hash.

Does not modify original data in any way.

# Usage

To use the tool, simply put your 'rules' in a `rules.json` file. Which must follow the JSON structure.

Example `rules.json`:

```json
{
    "rules": [
        {
            "source": "/my/source/directory/",
            "destination": "/my/destination/directory/",
            "exclude": {
                "files": ["badfile1", "badfile2"],
                "directories": ["badfolder1"]
            }
        },
        {
            "source": "/my/other/source/directory/",
            "destination": "/my/other/destination/directory/",
            "exclude": {
                "files": [".*\\.log"],
                "use_regex": true
            }
        }
    ]
}
```

The `source` is the directory to recurse through. Single files are not supported.

The `destination` is the directory to copy data to. **Will overwrite existing files with the same name at destination**.

These two properties **must** exist in every rule.

The `exclude` property defines what parts of the `source` directory to not copy to `destination`. It can contain either one or two other core properties:

  - `files` is a list of file names to exclude from the backup.

  - `directories` is a list of directory names to exclude from the backup.

  - `use_regex` [Optional] is a boolean telling the script whether or not to treat the strings in `files` and `directories` as regular expressions. Each expression is matched against the full file/directory name.

  Additionally, these are **global**, **name-based** exclusions, and will be accounted for at every copy iteration.

Then, run `python3 backup.py`. Prefix the command with `sudo` for root-protected files.

# CLI options
You can modify program behaviour with these options:

```
--no-hash-verification     Disables hash verification.
--no-fs-sync               Disables filesystem sync after copy.
--dry-run                  Runs the script but without actually copying files.
```

# Notes

- If copying to an external drive, ensure the connection to the drive is stable.

- Symlinked files are handled by _only copying the file contents and metadata_ to the destination. 