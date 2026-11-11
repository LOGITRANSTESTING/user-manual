#!/usr/bin/env python3
"""Add the Dr.Explain index (keywords) to an ILISCyber .gui.  Never edits SRC.

  python scripts/add_keywords.py SRC.gui DST.gui [--mapping]

Same as `python tools/ilis.py gui keywords SRC DST [--mapping]` (house rules in tools/ilis_gui.py: add_keywords).
"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import ilis_gui as U


def main():
    try: sys.stdout.reconfigure(errors='replace')
    except Exception: pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--mapping', action='store_true', help='mapping document: every page gets a keyword (except Tabs / Functionalities)')
    a = ap.parse_args()
    print(U.keywords_report(a.src, a.dst, a.mapping))


if __name__ == '__main__':
    main()
