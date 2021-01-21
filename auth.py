import re

def read_tokens():
    with open('tokens.txt', 'r') as f:
        lines = f.read().strip().splitlines()
        tokens = [re.split(r'\s+', line)[0] for line in lines]
    return set(tokens)