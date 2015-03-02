#!/usr/bin/env python3.3

# a Python wrapper around patsopt that is friendlier

import sys
import subprocess
import io
import re

MAX_EXCERPT_LINES = 10

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
INVERTED = '\033[7m'
RESET = '\033[0m'

def line_reference(match):
    filename = match.group(1)
    start_byte = int(match.group(2))
    start_line = int(match.group(3))
    start_offset = int(match.group(4))
    end_byte = int(match.group(5))
    end_line = int(match.group(6))
    end_offset = int(match.group(7))
    type = match.group(8)
    id = match.group(9)
    desc = match.group(10)

    if desc[-1] in [':', '.']:
        desc = desc[:-1]

    spans_lines = start_line != end_line
    if spans_lines:
        token_highlight = ''
    else:
        token_highlight = INVERTED

    out = ''
    if type == 'warning':
        out += YELLOW + "warning\t" + RESET
    elif type == 'error':
        out += RED + "error\t" + RESET
    else:
        out += type + "\t"

    out += desc

    if id not in '0123456789':
        out += ' ({})'.format(id)

    out += "\n"

    out += "in {}, ".format(CYAN + filename + RESET)
    if spans_lines:
        out += "from lines {} to {}:".format(start_line, end_line)
    else:
        out += "on line {}:".format(start_line)

    with open(filename, 'r') as f:
        lines = []
        i = 0
        last_line = ''

        while True:
            i += 1
            ch = f.read(1)

            if i < start_byte:
                if ch == '\n':
                    last_line = ''
                else:
                    last_line += ch

            elif i == start_byte:
                if ch == '\n':
                    lines.append('')
                else:
                    lines.append(last_line + token_highlight + ch)

                if i == end_byte:
                    lines[-1] = lines[-1] + RESET
                    break

            else:   # i > start_byte
                if i == end_byte:
                    if ch == '\n':
                        lines[-1] = lines[-1] + RESET
                    else:
                        lines[-1] = lines[-1] + RESET + ch
                    break

                elif ch == '\n':
                    lines.append('')

                else:
                    lines[-1] = lines[-1] + ch

        if ch not in ['\n', '']:
            while True:
                ch = f.read(1)
                if ch in ['\n', '']:
                    break
                lines[-1] = lines[-1] + ch

    if len(lines) > MAX_EXCERPT_LINES:
        lines = lines[:MAX_EXCERPT_LINES] + [RESET + '...']

    out += '\n' + '\n'.join(lines)
    return out

subs = [
    # remove needless prefix
    ('^patsopt: ', ''),

    ('^patsopt\((.+)\): ', YELLOW + "\\1\t" + RESET),

    # remove odd prefixes to errors/exceptions
    ('_2home_2hwxi_2research_2Postiats.*__(.+)', r'\1'),

    # brackets
    (r'( +)\[(.+)\]', BLUE + r'\1\2' + RESET),

    # warning() lines
    (r'^warn?ing\((.+?)\): ', YELLOW + "\\1\t" + RESET),

    # exit() lines
    (r'^(exit|error)\((.+?)\): ', RED + "\\1\t" + RESET),

    # error lines
    (r'^(.+\.[ds]ats): (\d+)\(line=(\d+), offs=(\d+)\) ' + \
     r'-- (\d+)\(line=(\d+), offs=(\d+)\): (error|warning)\((.+)\): (.+)',
     line_reference)
    ]

args = ['patsopt'] + sys.argv[1:]
patsopt_err = False

try:
    from_patsopt = subprocess.check_output(args, stderr=subprocess.STDOUT,
                                           universal_newlines=True)
except subprocess.CalledProcessError as err:
    from_patsopt = err.output
    patsopt_err = True

for line in from_patsopt.split('\n'):
    if len(line) == 0:
        continue

    for search, repl in subs:
        if re.search(search, line):
            line = re.sub(search, repl, line)

    print(line)

if patsopt_err:
    sys.exit(1)
else:
    sys.exit(0)
