#!/usr/bin/env python3
"""Build _MoltenContactSheet.png for the Molten theme. Thin wrapper over the
shared contact-sheet engine (../_themegen/contact_sheet.py); dev-only."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_themegen"))
import contact_sheet

if __name__ == "__main__":
    contact_sheet.build(os.path.dirname(os.path.abspath(__file__)))
