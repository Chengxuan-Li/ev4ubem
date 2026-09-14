"""Run all analyses in dependency order (requires processing outputs; some steps read raw session data)."""
from __future__ import annotations

from src.analysis import (charging_sessions, chargepoint_local_use, diversity, drive_clean_parameters,
                          flows_reconciliation, home_event_library,
                          hourly_load_scenarios, nhts_ev_propensity, nhts_vehicle_days, ny_vs_open_shapes,
                          ownership_trends, subzip_allocation, zip_ev_penetration)


def main() -> None:
    ownership_trends.main()
    flows_reconciliation.main()
    zip_ev_penetration.main(2023)
    zip_ev_penetration.main(2026)
    nhts_vehicle_days.main()
    nhts_ev_propensity.main()
    subzip_allocation.main()
    charging_sessions.main()
    ny_vs_open_shapes.main()
    chargepoint_local_use.main()
    diversity.main()
    hourly_load_scenarios.main()
    home_event_library.main()
    drive_clean_parameters.main()


if __name__ == "__main__":
    main()
