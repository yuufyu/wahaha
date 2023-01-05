"""
shuf.py

Shuffle input file.

"""

import random
from argparse import ArgumentParser

parser = ArgumentParser(description='Shuffle input file')
parser.add_argument('file', type=str)
parser.add_argument('-n', '--head-count', type=int, default = -1, help = 'Output at most count lines. By default, all input lines are output.')
args = parser.parse_args()

filename = args.file
head_count = args.head_count

f = open(filename, "r")
lines = f.readlines()
random.shuffle(lines)

if head_count < 0 :
    output_lines = lines
else :
    output_lines = lines[:head_count]

print("".join(output_lines), end="")
