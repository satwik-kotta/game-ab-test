# Mobile Game Retention & A/B Testing — Cookie Cats Gate Placement

**Question:** Cookie Cats makes players wait (or pay) at "gates" to progress. Should the first gate move from level 30 to level 40?
**Answer:** No. Moving it lowers 7-day retention by **4.3% relative** (19.02% → 18.20%, Holm-adjusted p = 0.005). That's about **818 fewer players still active on day 7 for every 100,000 installs**.

**Live dashboard:** `dashboard/index.html` (enable GitHub Pages on this repo, then open `/dashboard/`)

## Workflow
Raw player data → SQL quality checks and engagement metrics → behavioral finding → hypothesis → power analysis → randomized A/B readout → robustness checks → launch decision → dashboard

## Data
Public experiment data from the mobile puzzle game *Cookie Cats* (Tactile Entertainment; distributed via DataCamp/Kaggle). 90,189 players who installed during the test were randomized at the player level to `gate_30` (control) or `gate_40` (treatment).

| Column | Meaning |
|---|---|
| `userid` | player id |
| `version` | `gate_30` or `gate_40` |
| `sum_gamerounds` | game rounds played in the first 14 days |
| `retention_1` / `retention_7` | played again 1 / 7 days after install |

## 1. Player behavior (SQL, `sql/02`–`03`)
- One player logged 49,854 rounds (the next highest is 2,961). They were removed as an outlier, leaving **90,188 players**.
- **63% of players stop before round 30**, so most players never see the first gate. 4.4% never play a single round.
- Overall D1 retention is 44.5% and D7 is 18.6%. **30% of players return on day 1 but are gone by day 7**, which makes D7 the metric where gate design matters most.
- Retention rises steeply with engagement: D7 is 4% for players with 1–29 rounds and 71% for players with 100+ rounds.

## 2. Experiment design
- **Hypothesis:** a later first gate gives players more uninterrupted play and improves retention. The opposing view is that an earlier break makes players come back for more.
- **Primary metric:** D7 retention. **Secondary:** D1 retention. **Guardrail:** rounds played.
- **Decision rule, set before the readout:** keep the gate at 30 if gate 40 is significantly worse on D7 after Holm correction.
- **Power:** at 80% power and α = 0.05, the test can detect a **0.73 pp change in D7 (3.8% relative)** and a 0.93 pp change in D1. Detecting a 2% relative drop in D7 would need about 166K players per arm.

## 3. Results (`analysis/ab_test.py`)
| Metric | Gate 30 | Gate 40 | Difference (95% CI) | p | Holm p |
|---|---|---|---|---|---|
| D7 retention (primary) | 19.02% | 18.20% | −0.82 pp [−1.33, −0.31] | 0.0016 | **0.0048** |
| D1 retention | 44.82% | 44.23% | −0.59 pp [−1.24, 0.06] | 0.074 | 0.102 |
| Rounds played (guardrail) | median 17 | median 16 | mean 51.3 vs 51.3 | 0.051 | 0.102 |

- **Bootstrap (10,000 resamples):** the relative lift in D7 is −6.9% to −1.6%, and gate 30 is better in 99.9% of resamples.

## 4. Validity checks
- **Sample ratio:** 44,699 vs 45,489 players, chi-square p = 0.0085. That is above the 0.001 alarm threshold used in industry, so randomization holds. It is still worth watching.
- **A/A test:** splitting the control arm at random 1,000 times gives a 5.1% false-positive rate, in line with the nominal 5%. The test machinery is calibrated.
- **Multiple testing:** Holm correction across the three metrics. Only D7 stays significant.
- **Segment cuts:** retention by rounds-played bucket is shown as description only. Rounds played is itself affected by the gate, so conditioning on it is not causal.

## 5. Decision
**Keep the first gate at level 30.** D7 retention is significantly worse with gate 40. D1 shows no significant change, and rounds played do not improve enough to offset the D7 loss. A follow-up test could target the 63% of players who stop before round 30, for example with onboarding changes, because the gate never reaches them.

## Run it
```bash
pip install -r requirements.txt
createdb games && ./run_sql.sh games      # PostgreSQL metrics (run from repo root)
python analysis/ab_test.py                # stats -> outputs/results.json
python analysis/build_dashboard.py        # -> dashboard/index.html
```

## Repo layout
```
data/cookie_cats.csv        raw experiment data
sql/                        load, quality checks, engagement, experiment readout, segments
analysis/ab_test.py         SRM, power/MDE, z-tests, bootstrap, A/A, Holm, decision
analysis/build_dashboard.py injects results into the ECharts dashboard
dashboard/index.html        interactive dashboard (Apache ECharts)
outputs/                    results.json + printed SQL and test output
```
