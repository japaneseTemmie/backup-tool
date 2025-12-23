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
            "destination": "/my/other/destination/directory/"
        }
    ]
}
```

The `source` is the directory to recurse through. Single files are not supported.

The `destination` is the directory to copy data to. **Will overwrite anything existing at destination**.

These two properties **must** exist in every rule.

The `exclude` property defines what parts of the `source` directory to not copy. It can contain either one or two other properties:

  - `files` is a list of file names to exclude from the backup.

  - `directories` is a list of directory names to exclude from the backup.

  Currently these properties does not support regular expressions. Additionally, these are **global** exclusions, and will be accounted for at every copy iteration.

Then, run `python3 backup.py`. Prefix the command with `sudo` for root-protected files.

# CLI options
You can modify program behaviour with these options:

```
--no-hash-verification          Disables hash verification.
--no-fs-sync          Disables filesystem sync after copy.
```

# Notes

If copying to an external drive, ensure the connection to the drive is stable.