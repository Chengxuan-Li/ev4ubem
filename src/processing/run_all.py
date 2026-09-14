"""Run all processing steps (requires acquisition outputs in data/raw/)."""
from __future__ import annotations

from src.processing import (acs_features, dmv_ev_stock, dmv_statewide_ev, drive_clean, evaluateny, geography,
                            infrastructure)


def main() -> None:
    evaluateny.main()
    geography.main()
    acs_features.main()
    infrastructure.main()
    drive_clean.main()
    dmv_ev_stock.main()
    dmv_statewide_ev.main()


if __name__ == "__main__":
    main()
