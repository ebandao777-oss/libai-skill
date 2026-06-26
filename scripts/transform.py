#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command-line interface for AI text rewriting."""

import argparse
import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from cli_utils import add_common_args, read_input, validate_text
from rewrite import AIRewriter
from utils import write_file


def main():
    parser = argparse.ArgumentParser(
        description="Rewrite AI-generated text to sound more natural."
    )
    add_common_args(parser, with_aggressive=True)
    
    args = parser.parse_args()
    
    text, _ = read_input(args)
    validate_text(text)
    
    rewriter = AIRewriter(user_rules_path=args.rules)
    rewritten, changes = rewriter.rewrite(text, aggressive=args.aggressive)
    
    if not args.quiet and changes:
        print(f"Changes ({len(changes)}):", file=sys.stderr)
        for c in changes:
            print(f" • {c}", file=sys.stderr)
    
    if args.output:
        write_file(args.output, rewritten)
        if not args.quiet:
            print(f"→ Saved to {args.output}", file=sys.stderr)
    else:
        print(rewritten)


if __name__ == "__main__":
    main()
