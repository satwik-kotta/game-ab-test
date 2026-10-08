"""Cookie Cats gate-placement A/B test: full statistical readout.

Control = gate_30 (first gate at level 30), Treatment = gate_40.
Primary metric: D7 retention. Secondary: D1 retention. Guardrail: game rounds played.
Writes outputs/results.json (used by the dashboard and README).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize, proportions_ztest

ROOT = Path(__file__).resolve().parents[1]
rng = np.random.default_rng(42)

raw = pd.read_csv(ROOT / "data" / "cookie_cats.csv")
n_raw = len(raw)
df = raw[raw.sum_gamerounds < 10_000].copy()          # one player logged 49,854 rounds
for c in ("retention_1", "retention_7"):
    df[c] = df[c].astype(int)
ctrl, trt = df[df.version == "gate_30"], df[df.version == "gate_40"]
nc, nt = len(ctrl), len(trt)
R = {"n_raw": n_raw, "n": len(df), "n_control": nc, "n_treatment": nt}

# 1. Sample ratio mismatch (expected 50/50)
chi2, p_srm = stats.chisquare([nc, nt])
R["srm"] = {"chi2": chi2, "p": p_srm, "alarm_threshold": 0.001, "flag": bool(p_srm < 0.001)}

# 2. Power / minimum detectable effect at the realised sample size (alpha .05, power .8)
pw = NormalIndPower()
def mde(base):
    es = pw.solve_power(nobs1=nc, ratio=nt / nc, alpha=0.05, power=0.8)
    # invert Cohen's h back to an absolute difference
    p2 = np.sin(np.arcsin(np.sqrt(base)) - es / 2) ** 2
    return base - p2
R["power"] = {}
for m in ("retention_1", "retention_7"):
    base = ctrl[m].mean()
    d = mde(base)
    R["power"][m] = {"baseline": base, "mde_abs": d, "mde_rel": d / base}
# sample size per arm needed to detect a 2% relative drop in D7 (planning view)
b7 = ctrl.retention_7.mean()
R["power"]["n_per_arm_for_2pct_rel_d7"] = pw.solve_power(
    effect_size=abs(proportion_effectsize(b7, b7 * 0.98)), alpha=0.05, power=0.8)

# 3. Two-proportion z-tests + Wald 95% CI on the difference
tests = {}
for m in ("retention_7", "retention_1"):
    x = np.array([trt[m].sum(), ctrl[m].sum()]); n = np.array([nt, nc])
    z, p = proportions_ztest(x, n)
    pt, pc = x / n
    se = np.sqrt(pt * (1 - pt) / nt + pc * (1 - pc) / nc)
    diff = pt - pc
    tests[m] = {"control": pc, "treatment": pt, "diff": diff,
                "ci": [diff - 1.96 * se, diff + 1.96 * se],
                "rel_lift": diff / pc, "z": z, "p": p}

# 4. Guardrail: rounds played (heavy-tailed -> Mann-Whitney + bootstrap of the mean)
u, p_mw = stats.mannwhitneyu(trt.sum_gamerounds, ctrl.sum_gamerounds)
tests["sum_gamerounds"] = {"control_mean": ctrl.sum_gamerounds.mean(),
                           "treatment_mean": trt.sum_gamerounds.mean(),
                           "control_median": ctrl.sum_gamerounds.median(),
                           "treatment_median": trt.sum_gamerounds.median(),
                           "p": p_mw}

# Holm correction across the three metrics
names = list(tests)
_, p_adj, _, _ = multipletests([tests[k]["p"] for k in names], method="holm")
for k, pa in zip(names, p_adj):
    tests[k]["p_holm"] = pa
R["tests"] = tests

# 5. Bootstrap (10,000 resamples) of the relative lift in D1 and D7
B = 10_000
boot = {}
for m in ("retention_1", "retention_7"):
    c, t = ctrl[m].to_numpy(), trt[m].to_numpy()
    mc = rng.binomial(len(c), c.mean(), B) / len(c)   # parametric bootstrap of each arm's rate
    mt = rng.binomial(len(t), t.mean(), B) / len(t)
    lift = mt / mc - 1
    boot[m] = {"ci": list(np.percentile(lift, [2.5, 97.5])),
               "p_gate30_better": float((lift < 0).mean()),
               "hist": np.histogram(lift, bins=40)}
R["bootstrap"] = {m: {"ci": v["ci"], "p_gate30_better": v["p_gate30_better"],
                      "hist_counts": v["hist"][0].tolist(),
                      "hist_edges": v["hist"][1].tolist()} for m, v in boot.items()}

# 6. A/A test: split the control arm at random 1,000 times; false-positive rate should be ~5%
fp = 0
c7 = ctrl.retention_7.to_numpy()
for _ in range(1000):
    mask = rng.random(len(c7)) < 0.5
    a, b = c7[mask], c7[~mask]
    _, p = proportions_ztest([a.sum(), b.sum()], [len(a), len(b)])
    fp += p < 0.05
R["aa_false_positive_rate"] = fp / 1000

# 7. Engagement profile and descriptive segment cut (not causal: rounds is post-treatment)
bins = [-1, 0, 29, 39, 99, np.inf]
labels = ["0", "1-29", "30-39", "40-99", "100+"]
df["bucket"] = pd.cut(df.sum_gamerounds, bins=bins, labels=labels)
seg = (df.groupby(["bucket", "version"], observed=True)
         .agg(players=("userid", "size"), d1=("retention_1", "mean"), d7=("retention_7", "mean"))
         .reset_index())
R["segments"] = seg.to_dict(orient="records")
eng = df.groupby("bucket", observed=True).agg(players=("userid", "size"),
                                               d1=("retention_1", "mean"),
                                               d7=("retention_7", "mean")).reset_index()
eng["share"] = eng.players / len(df)
R["engagement"] = eng.to_dict(orient="records")
R["overall"] = {"d1": df.retention_1.mean(), "d7": df.retention_7.mean(),
                "median_rounds": float(df.sum_gamerounds.median()),
                "share_under_30": float((df.sum_gamerounds < 30).mean()),
                "share_zero": float((df.sum_gamerounds == 0).mean()),
                "d1_not_d7": float(((df.retention_1 == 1) & (df.retention_7 == 0)).mean())}

# 8. Business impact: D7 players lost per 100k installs if gate_40 shipped
R["impact_per_100k_installs"] = -tests["retention_7"]["diff"] * 100_000

# Decision rule set before reading results: ship gate_40 only if D7 is not significantly worse
t7 = tests["retention_7"]
R["decision"] = ("Keep gate at level 30" if t7["p_holm"] < 0.05 and t7["diff"] < 0
                 else "Gate 40 acceptable")

(ROOT / "outputs").mkdir(exist_ok=True)
(ROOT / "outputs" / "results.json").write_text(json.dumps(R, indent=2, default=float))

t1 = tests["retention_1"]
print(f"Players analysed: {len(df):,} (raw {n_raw:,})  control {nc:,} / treatment {nt:,}")
print(f"SRM chi2={chi2:.2f} p={p_srm:.4f}  flag={R['srm']['flag']}")
for m in ("retention_1", "retention_7"):
    P = R["power"][m]
    print(f"MDE {m}: {P['mde_abs']*100:.2f} pp abs ({P['mde_rel']*100:.1f}% rel) on base {P['baseline']*100:.2f}%")
print(f"n/arm for 2% rel D7 drop: {R['power']['n_per_arm_for_2pct_rel_d7']:,.0f}")
for m in ("retention_7", "retention_1"):
    t = tests[m]
    print(f"{m}: {t['control']*100:.2f}% -> {t['treatment']*100:.2f}%  diff {t['diff']*100:.2f}pp "
          f"CI [{t['ci'][0]*100:.2f}, {t['ci'][1]*100:.2f}]  rel {t['rel_lift']*100:.2f}%  "
          f"p={t['p']:.4f} holm={t['p_holm']:.4f}")
g = tests["sum_gamerounds"]
print(f"rounds mean {g['control_mean']:.1f} vs {g['treatment_mean']:.1f}, median {g['control_median']} vs "
      f"{g['treatment_median']}  MW p={g['p']:.4f} holm={g['p_holm']:.4f}")
for m in ("retention_1", "retention_7"):
    b = R["bootstrap"][m]
    print(f"bootstrap {m}: rel lift CI [{b['ci'][0]*100:.2f}%, {b['ci'][1]*100:.2f}%]  P(gate30 better)={b['p_gate30_better']:.3f}")
print(f"A/A false-positive rate: {R['aa_false_positive_rate']:.3f}")
print(f"D7 players lost per 100k installs with gate_40: {R['impact_per_100k_installs']:.0f}")
print("Overall:", {k: round(v, 4) for k, v in R["overall"].items()})
print("Decision:", R["decision"])
