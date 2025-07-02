# Backup Tool
Command line tool to copy all contents from a source directory to a destination directory using simple rulesets defined in a `rules.txt` (works on UNIX-like systems only).

# Defining rules
In a `rules.txt` file:

Define a source destination (folder only):

`/path/to/my/source`

Use `->` to point to a new directory

`/path/to/my/source -> /path/to/my/destination`

Optionally, define new rules under others:

`/path/to/my/source -> /path/to/my/destination`

`/path/to/my/source2 -> /path/to/my/destination2`

then:

`python3 main.py`

## The developer of this project is not responsible for data loss as a result of use or misuse of this program.
