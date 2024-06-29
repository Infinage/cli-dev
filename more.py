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

def read_from_file(ptr: io.TextIOWrapper, buffer: collections.deque[str], n_lines: int, n_cols: int) -> tuple[int, list[str]]:
    """
    Reads from the file pointer only as much as neccessary, based on n_lines, n_cols and existing text in the buffer.
    Buffer holds the data that was previously read but couldn't fit into the screen.
    Before reading any new text, we try exhaust text in the buffer.

    Why / when do we insert line breaks?
    - When the current line contains characters beyond what a line on screen can show
    - When a line break is encountered in the text being read (for formatting purposes, we leave it untouched)

    Buffer deque is modified in place.
    We return the count of line breaks we have inserted so far, along with the actual text to be displayed.
    """

    line_breaks_inserted = 0
    lines: list[str] = []
    line: list[str] = []
    while buffer and n_lines > 0:
        curr_line = buffer.popleft()
        curr_line_length = len(curr_line)

        # If the current line is of the right width or if it contains a
        # line break, we have inserted a single line to our screen
        if curr_line_length == n_cols or curr_line[-1] in ("\n", "\r"):
            lines.append(curr_line)
            n_lines -= 1

        # Only time this would be executed is when the buffer is exhausted,
        # we have some line that is shorter that our screen width.
        else:
            line = list(curr_line)

    # After exhausting buffer, if we still have more lines that the screen can fit
    if n_lines > 0:
        # Read as much as neccessary
        for ch in ptr.read(n_cols * n_lines):
            line.append(ch)

            # At each iteration we check if we have encountered a line break
            # If not, check if the accumulated characters would cover the width of the screen
            # In either of the cases, we are done for that particular line
            # Append that line and clear the accumulating variable for the next line

            # We have to be careful to only insert as much into our `lines` as it can hold
            # If we have read beyond it, we start accumulating the excess into our buffer

            if line[-1] in ('\n', '\r'):
                if n_lines > 0:
                    lines.append(''.join(line))
                    n_lines -= 1
                else:
                    buffer.append(''.join(line))
                line.clear()

            elif len(line) == n_cols:
                prev = line.pop()
                line.append("\n")
                line_breaks_inserted += 1
                if n_lines > 0:
                    lines.append(''.join(line))
                    n_lines -= 1
                else:
                    buffer.append(''.join(line))
                line = [prev]

        # We reached end of buffer but line doesn't have an end (\n) or the required width
        if line:
            if n_lines > 0:
                lines.append(''.join(line))
                n_lines -= 1
            else:
                buffer.append(''.join(line))

    return line_breaks_inserted, lines

def main(stdscr: curses.window, args) -> None:

    # There is no proper typing support in curses for mypy
    # This is added merely for type hint support and never gets executed
    if not stdscr:
        stdscr = curses.initscr()

    # Our screen would contain two windows: one to display text,
    # other to display % completion and help details
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

        # We read from file the first time and every subsequent time as long as
        # a 'space', 'newline', 'keydown' characters are hit. This can only
        # happen until we have data still left in our file *or* in our buffer.
        if ch in (ord(' '), curses.KEY_DOWN, curses.KEY_ENTER, ord('\n'), ord('\r')) and (read_count < FILE_SIZE or len(buffer) > 0):
            line_breaks_inserted, lines = read_from_file(text_pointer, buffer, TEXTBOX_ROWS - 1, TEXTBOX_COLS)
            display_text = ''.join(lines)

            # There was some confusion on how to handle extra line breaks inserted
            # to reflect proper percentage completion. We are resorting to incrementing
            # the file size by the amount of line breaks that we are inserting
            read_count, FILE_SIZE = read_count + len(display_text), FILE_SIZE + line_breaks_inserted
            percentage_completion = (read_count / FILE_SIZE) * 100

            # When we are at buffer end, we might have text that only partially
            # cover our screen. In these cases, we would need to clear the screen
            if read_count >= FILE_SIZE:
                textbox.clear()

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
