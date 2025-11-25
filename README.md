# Backup tool

Command-line tool to make copies of folders to specified directories. Useful for backups.

Simply copies specified files to another destination and verifies their hash.

Does not modify original data in any way.

# Usage

To use the tool, simply put your 'rules' in a `rules.txt` file.

```
/path/to/my/source -> /path/to/my/destination
/other/path/ -> /other/destination/
```

Source paths must exist and be a folder. Single-file backups are not supported.

If copying to an external drive, ensure the connection to the drive is stable.

Then `python3 main.py`. Prefix the command with `sudo` for root-protected files.