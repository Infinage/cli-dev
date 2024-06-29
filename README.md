# cli-dev

## Overview
**cli-dev** is a project aimed at exploring and replicating existing command-line interface (CLI) tools and games using Python.

### Current Scripts
- **more.py**: A Python script replicating the functionality of the `more` command line utility in Linux. It reads from a file in batches, displaying content as needed. The script uses the `curses` library to manage terminal input and output.

## more.py

### Features
- Reads file content in batches, displaying as much as the screen can fit.
- Uses `curses` for terminal handling.
- Displays progress percentage while reading the file.
- Provides an option to quit the application by pressing 'q'.

### Installation
To run the script, ensure you have Python installed on your system. Additionally, you'll need the `curses` library, which is included with Python on Unix-based systems. For Windows, you can install `windows-curses` via pip:

```sh
pip install windows-curses
```

### Usage

To use `more.py`, simply run the script with the file you wish to read as an argument:

```sh
python more.py --fname yourfile.txt
```

### Limitations
- Currently throws an error if the screen size is too small to fit the initial content.
