"""
Monte Carlo: how backtest selection inflates the Sharpe ratio.

Simulate N strategies with ZERO true edge (iid mean-zero returns) over T
trading days, compute each strategy's annualised in-sample Sharpe, and look at
the *maximum* — what you'd report if you cherry-picked the best backtest.

The max of N iid standard normals grows like sqrt(2 ln N), so the best spurious
annualised Sharpe scales as ~ sqrt(2 ln N) * sqrt(A / T).
"""
import numpy as np
import matplotlib.pyplot as plt

RNG = np.random.default_rng(42)
A, T = 252, 1260                     # 252 trading days/yr; 5 years of daily data
OUT = __file__.rsplit("/", 2)[0] + "/research/backtest-overfitting"

def ann_sharpe(returns):             # returns shape (T, N) -> (N,)
    mu = returns.mean(axis=0)
    sd = returns.std(axis=0, ddof=1)
    return np.sqrt(A) * mu / sd

def theoretical_max(n):
    a = np.sqrt(2 * np.log(n))
    e = a - (np.log(np.log(n)) + np.log(4 * np.pi)) / (2 * a)   # standard EVT approx
    return e * np.sqrt(A / T)

# ---- Figure 1: distribution of in-sample Sharpe for N=1000 zero-edge strategies
N = 1000
sr = ann_sharpe(RNG.standard_normal((T, N)))
best = sr.max()
print(f"[N={N}, T={T}] best spurious annualised Sharpe = {best:.2f}")
print(f"                mean across strategies          = {sr.mean():.3f}")
print(f"                theoretical E[max]              = {theoretical_max(N):.2f}")

plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(7, 4.3), dpi=130)
ax.hist(sr, bins=40, color="#7c9cbf", edgecolor="white", alpha=0.9)
ax.axvline(best, color="#c0392b", lw=2)
ax.text(best, ax.get_ylim()[1]*0.9, f" best = {best:.2f}", color="#c0392b", va="top")
ax.axvline(0, color="#333", lw=1, ls="--")
ax.set_xlabel("Annualised in-sample Sharpe"); ax.set_ylabel("Count")
ax.set_title(f"{N} strategies, zero true edge, {T//A} years of daily data")
fig.tight_layout(); fig.savefig(f"{OUT}/fig-sharpe-distribution.png"); plt.close(fig)

# ---- Figure 2: expected best spurious Sharpe vs number of trials
Ns = np.unique(np.round(np.logspace(0, 3.3, 16)).astype(int))
reps = 80
emp = np.array([[ann_sharpe(RNG.standard_normal((T, n))).max() for _ in range(reps)]
                for n in Ns]).mean(axis=1)
theo = theoretical_max(np.maximum(Ns, 2))
for n in [10, 100, 1000, 10000]:
    print(f"  N={n:>6}: expected best spurious annualised Sharpe ~ {theoretical_max(n):.2f}")

fig, ax = plt.subplots(figsize=(7, 4.3), dpi=130)
ax.plot(Ns, emp, "o-", color="#7c9cbf", label="Monte Carlo (mean best)")
ax.plot(Ns, theo, "--", color="#c0392b", label=r"$\sqrt{2\ln N}\,\sqrt{A/T}$ (approx.)")
ax.set_xscale("log")
ax.set_xlabel("Number of strategies tested, N (log scale)")
ax.set_ylabel("Best annualised Sharpe")
ax.set_title("A bigger search finds a better strategy — from pure noise")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{OUT}/fig-max-sharpe-vs-trials.png"); plt.close(fig)
print("figures written to", OUT)
