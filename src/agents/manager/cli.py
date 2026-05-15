from __future__ import annotations

import argparse
from pathlib import Path

from .manager import TeamAgentManager
from .models import AgentManagerConfig


def main() -> None:
    p = argparse.ArgumentParser(description="Manager runtime helpers")
    p.add_argument("team", nargs="?", default="BLUE", help="team name")
    p.add_argument("--ledger-dir", dest="ledger_dir", help="ledger base path")
    p.add_argument("--verbose", action="store_true", help="verbose output")
    args = p.parse_args()

    cfg = AgentManagerConfig(ledger_base_path=Path(args.ledger_dir) if args.ledger_dir else None)
    mgr = TeamAgentManager(args.team, config=cfg)
    print(mgr.print_ledger_info(verbose=args.verbose))


if __name__ == "__main__":
    main()
