# Backup tool

Command-line tool used to make copies of folders.

# Usage

To use the tool, simply put your 'rules' in a `rules.txt` file.

```
/path/to/my/source -> /path/to/my/destination
/other/path/ -> /other/destination/ # add other rules
```

Then `python3 main.py`. Remember to add `sudo` for root-protected files.