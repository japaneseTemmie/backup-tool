# Backup tool

Command-line tool to make copies of folders to specified directories. Useful for backups.

Simply copies specified files to another destination and verifies their hash.

Does not modify original data in any way.

# Key features
- Post-copy filesystem sync (POSIX only).
- SHA-256 based hash verification after copy.
- Simple exclusion system.
- Easy-to-read JSON-based configuration file.

# Usage

To use the tool, ensure you have atleast Python 3.10. Then, simply put your 'rules' in a `rules.json` file. Which must follow the JSON structure.

Example `rules.json`:

```json
{
    "rules": [
        {
            "source": "/my/source/directory/",
            "destination": "/my/destination/directory/",
            "ignore": ["badfile1", "badfile2", "badfolder"]
        },
        {
            "source": "/my/other/source/directory/",
            "destination": "/my/other/destination/directory/",
            "ignore": ["*.log"]
        }
    ]
}
```

The `source` is the directory to recurse through. Single files are not supported.

The `destination` is the directory to copy data to. **Any existing files with the same name at destination will be overwritten**.

These two properties **must** exist in every rule.

The `ignore` optional property defines what parts of the `source` directory to not copy to `destination`. It is defined as a list of strings and supports glob patterns.

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