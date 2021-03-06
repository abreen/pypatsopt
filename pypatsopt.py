#!/usr/bin/env python3.3

# a Python wrapper around patsopt that is friendlier

import sys
import subprocess
import io
import re

VERSION = 0.1
MAX_EXCERPT_LINES = 10

RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
CYAN = '\033[36m'
INVERTED = '\033[7m'
UNDERLINE = '\033[4m'
RESET = '\033[0m'

ERROR_EFFECT = INVERTED

def _line_reference(match):
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
                elif ch == ' ':
                    lines.append(' ')
                else:
                    lines.append(last_line + ERROR_EFFECT + ch)

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


def _constraint(before, match):
    from parsetree import prettify
    return before + prettify(match.group(1))

subs = [
    # remove needless prefix
    ('^patsopt: ', ''),

    ('^patsopt\((.+)\): ', YELLOW + "\\1\t" + RESET),

    # remove odd prefixes to errors/exceptions
    ('_2home_2hwxi_2research_2Postiats.*__(.+)', r'\1'),

    # brackets
    (r'( +)\[(.+?)\]', BLUE + r'\1\2' + RESET),

    # warning() lines
    (r'^warn?ing\((.+?)\): ', YELLOW + "\\1\t" + RESET),

    # exit() lines
    (r'^(exit|error)\((.+?)\): ', RED + "\\1\t" + RESET),

    # error lines
    (r'^(.+\.[ds]ats): (\d+)\(line=(\d+), offs=(\d+)\) ' + \
     r'-- (\d+)\(line=(\d+), offs=(\d+)\): (error|warning)\((.+)\): (.+)',
     _line_reference)
    ]

if '--pretty' in sys.argv:
    subs.insert(0, (r'cannot be assigned the type (.+)',
                 lambda m: _constraint("expression cannot be assigned: ", m)))
    subs.append((r'unsolved constraint: (.+)',
                 lambda m: _constraint("unsolved constraint: ", m)))
    subs.append((r'The actual term is: (.+)',
                 lambda m: _constraint("actual term: ", m)))
    subs.append((r'The needed term is: (.+)',
                 lambda m: _constraint("needed: ", m)))
    sys.argv.remove('--pretty')

if '-h' in sys.argv or '--help' in sys.argv:
    subprocess.call(['patsopt'] + sys.argv[1:])
    print("pypatsopt wrapper version {}".format(VERSION))
    print("  --pretty (for better constraint solver expressions)")
    sys.exit(0)

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
