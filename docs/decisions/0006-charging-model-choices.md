# 0006 — Charging model design choices driven by validation (2026-09-14)

**Status:** accepted

## Context
The event-based charging library (`src/model/charging_library.py`) was iterated against independent evidence
(`src/analysis/charging_validation.py`). Each change below was made because a check failed or a behaviour was
physically implausible; checks used for calibration are flagged so they are not reported as independent validation.

## Decisions
1. **Workplace charging use rate.** Workplace-access users plug in on 40 % of attended workdays and only with a deficit
   > 8 kWh. First runs let users charge every workday (1.6–3.7 MWh/yr at work per user), inconsistent with NYSERDA
   22-03 session energy (≈ 9.7 kWh) and Drive Clean's "≈⅔ of those with access use it".
2. **Public top-up probability** is derived per vehicle from its expected annual plug energy, so the share parameter
   is honoured (first runs gave ~40–130 kWh/yr instead of ~300).
3. **Forced home charging and en-route DCFC.** BEVs are forced to plug in at home when the deficit exceeds 60 % of
   usable capacity and take en-route DCFC above 95 %; PHEVs are never forced (they switch to gasoline) and never use
   DCFC. Frequency types are tied to mileage (daily 1.15×, few/week 1.0×, weekly 0.8×, rare 0.6×).
4. **Frequency categories.** Survey categories are mapped to simulated sessions per week as daily ≥ 4.5, few/week
   1.5–4.5, weekly 0.6–1.5, rare < 0.6. PHEV frequency agreement is largely by construction (types are inputs and
   PHEVs are not forced); the BEV check (TVD ≈ 0.19) is informative: physical energy needs push self-reported weekly
   chargers into more frequent charging.
5. **Managed charging** starts at 23:00 + U[0, 2] h. A synchronized 23:00 start created a rebound peak
   (2050 trend home peak 60 MW vs 39 MW unmanaged); staggering reflects typical managed-charging programs, and the
   synchronized case is reported as a sensitivity in the report.
6. **Fleet depot profile** uses return times spread uniformly over 16:00–20:00 (expected profile); a single 18:00 start
   produced an artificial ~2 MW coincident block.
7. **Workplace timing** uses NYSERDA 22-03 Fig. 18 (NY) rather than the open Midwest workplace dataset (weekday peak
   12:00 vs NY 9–10 am, r = 0.47).
8. **Location energy shares are model outputs**, replacing the earlier fixed 80/7/8/5 assumption (event model 2026:
   home 66 %, work 5 %, public L2 10 %, DCFC 20 % including en-route and no-home-access BEVs).

## Consequences
The 2026 model reproduces NY weekday shapes (r ≈ 0.89–0.97), public L2 utilisation within the observed Ithaca
ChargePoint range, survey-based kWh per EV (±5 %), cold-climate seasonality (r ≈ 0.8) and residential diversity
between Norway's empirical 3.6 kW and 7.2 kW curves. Home charging timing in upstate NY single-family homes,
Level 1 behaviour, and DCFC shares remain unvalidated.
