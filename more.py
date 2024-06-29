"""
To test the functionality, we can generate two text files and see how the tool handles it.
1. wide.txt: Has a single line that is arbitrarily large to force a word wrap.
2. long.txt: Has lines that are single character long, we might end up reading all of the characters in one shot. This file helps check how we are handling the buffers.

```
import itertools
REPEAT = 100

with open("wide.txt", "w") as f:
    text = "abcdefghijklmnopqrstuvwxyz" * REPEAT
    f.write(text)

with open("long.txt", "w") as f:
    for ch in itertools.chain.from_iterable(itertools.repeat('abcdefghijklmnopqrstuvwxyz', REPEAT)):
        f.write(ch + '\n')
```
"""

import curses
import math
import argparse
import io
import os
import collections

def read_from_file(ptr: io.TextIOWrapper, buffer: collections.deque[str], n_lines: int, n_cols: int) -> tuple[int, int, str]:
    count = 0
    lines: list[str] = []
    line: list[str] = []
    while buffer and n_lines > 0:
        curr_line = buffer.popleft()
        curr_line_length = len(curr_line)
        if curr_line_length == n_cols or curr_line[-1] in ("\n", "\r"):
            lines.append(curr_line)
            count += curr_line_length
            n_lines -= 1
        else:
            line = list(curr_line)

    if n_lines > 0:
        for ch in ptr.read(n_cols * n_lines):
            line.append(ch)

            if line[-1] in ('\n', '\r'):
                if n_lines > 0:
                    lines.append(''.join(line))
                    count += len(lines[-1])
                    n_lines -= 1
                else:
                    buffer.append(''.join(line))
                line.clear()

            elif len(line) == n_cols:
                prev = line.pop()
                line.append("\n")
                if n_lines > 0:
                    lines.append(''.join(line))
                    count += len(lines[-1]) - 1
                    n_lines -= 1
                else:
                    buffer.append(''.join(line))
                line = [prev]

        # We reached end of buffer but line doesn't have an end (\n) or the required width
        if line:
            if n_lines > 0:
                lines.append(''.join(line))
                count += len(lines[-1])
                n_lines -= 1
            else:
                buffer.append(''.join(line))

    return count, len(lines), ''.join(lines)

def main(stdscr: curses.window, args) -> None:
    if not stdscr:
        stdscr = curses.initscr()

    ROWS, COLS = stdscr.getmaxyx()
    FILE_SIZE, PADDING = os.path.getsize(args.fname), 4
    TEXTBOX_ROWS, TEXTBOX_COLS = ROWS - PADDING, COLS - PADDING

    text_pointer: io.TextIOWrapper = open(args.fname, "r")

    stdscr.clear()
    stdscr.refresh()

    textbox = curses.newwin(TEXTBOX_ROWS, TEXTBOX_COLS, PADDING // 2, PADDING // 2)
    infobox = curses.newwin(1, 10, ROWS - 1, TEXTBOX_COLS - 10)
    infobox.addstr("Exit: 'q'")
    infobox.refresh()

    read_count = 0
    ch = ord(' ')
    buffer: collections.deque[str] = collections.deque([])
    while True:

        if ch in (ord(' '), curses.KEY_DOWN, curses.KEY_ENTER, ord('\n'), ord('\r')) and (read_count < FILE_SIZE or len(buffer) > 0):
            characters_read, lines_read, display_text = read_from_file(text_pointer, buffer, TEXTBOX_ROWS - 1, TEXTBOX_COLS)
            read_count += characters_read

            # When we are at buffer end
            if read_count >= FILE_SIZE:
                textbox.clear()

            percentage_completion = (read_count / FILE_SIZE) * 100
            textbox.addstr(0, 0, display_text)
            stdscr.addstr(ROWS - 1, 0, f"--MORE-- {percentage_completion:.2f}%", curses.A_REVERSE)
            textbox.refresh()

        elif ch == ord('q'):
            break

        ch = stdscr.getch()

# =============================== MAIN FUNCTION =============================== #

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='An imperfect clone of the `more` command line utility.')
    parser.add_argument("--fname", type=str, help='Path of the file to read.', required=True)
    args = parser.parse_args()
    if os.path.exists(args.fname):
        curses.wrapper(main, args)
    else:
        print("Specified doesn't exist. Please enter a valid file path.")
