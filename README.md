# Backup tool

Command-line tool to make copies of folders to specified directories. Useful for backups.

# Usage

To use the tool, simply put your 'rules' in a `rules.txt` file.

```
/path/to/my/source -> /path/to/my/destination
/other/path/ -> /other/destination/
```

Source paths must exist and be a folder. Single-file backups are not supported.

Then `python3 main.py`. Add `sudo` for root-protected files.