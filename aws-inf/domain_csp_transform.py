#!/usr/bin/env python

import sys

if __name__ == "__main__":
    domains = sys.argv[1]
    print(' '.join([ f"*.{domain.strip()}" for domain in domains.split(',')]))
    