#!/usr/bin/env python3
"""Print the real schema of a data source. Never guesses.

Usage: inspect-schema.py <logical-name>
Resolves the name through the project's profile.yaml (access mode) and the env var
DS_<NAME>_URL (or DATABASE_URL for the app database). Prints tables, columns, keys,
and the inspection time. Exits 3 if unreachable.
"""
import datetime as dt
import os
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    name = sys.argv[1]
    url = os.environ.get("DATABASE_URL") if name == "app" else os.environ.get(f"DS_{name.upper().replace('-', '_')}_URL")
    if not url:
        print(f"unreachable: no connection configured for '{name}' (set DS_{name.upper()}_URL)")
        return 3
    try:
        from sqlalchemy import create_engine, inspect
    except ImportError:
        print("unreachable: sqlalchemy not installed in this environment")
        return 3
    try:
        eng = create_engine(url)
        insp = inspect(eng)
        print(f"# schema of {name}  inspected {dt.datetime.now().isoformat(timespec='seconds')}")
        for t in insp.get_table_names():
            pk = insp.get_pk_constraint(t).get("constrained_columns", [])
            print(f"\n{t}  pk={pk}")
            for c in insp.get_columns(t):
                print(f"  {c['name']}  {c['type']}  {'NULL' if c['nullable'] else 'NOT NULL'}")
            for fk in insp.get_foreign_keys(t):
                print(f"  fk {fk['constrained_columns']} -> {fk['referred_table']}{fk['referred_columns']}")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"unreachable: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
