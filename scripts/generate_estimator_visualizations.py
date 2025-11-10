#!/usr/bin/env python3
"""
Generate additional visualizations for estimator sections
Smaller size than main visualizations (400px width)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from pathlib import Path
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Create output directory
output_dir = Path("visualizations/estimators")
output_dir.mkdir(parents=True, exist_ok=True)

print("Generating estimator visualizations...")

# ============================================================================
# 1. PSM Balance Plot
# ============================================================================
print("[1/6] Generating PSM balance plot...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))

# Before matching
np.random.seed(42)
treated = np.random.normal(0.6, 0.2, 100)
control = np.random.normal(0.4, 0.25, 100)

ax1.hist(treated, bins=20, alpha=0.6, label='Treated', color='#E63946')
ax1.hist(control, bins=20, alpha=0.6, label='Control', color='#2E86AB')
ax1.set_xlabel('Propensity Score')
ax1.set_ylabel('Count')
ax1.set_title('Before Matching\nSMD = 0.45')
ax1.legend()

# After matching
treated_matched = np.random.normal(0.5, 0.15, 80)
control_matched = np.random.normal(0.48, 0.16, 80)

ax2.hist(treated_matched, bins=20, alpha=0.6, label='Treated', color='#E63946')
ax2.hist(control_matched, bins=20, alpha=0.6, label='Control', color='#2E86AB')
ax2.set_xlabel('Propensity Score')
ax2.set_ylabel('Count')
ax2.set_title('After Matching\nSMD = 0.08')
ax2.legend()

plt.tight_layout()
plt.savefig(output_dir / 'psm_balance.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ psm_balance.png")

# ============================================================================
# 2. DiD Event Study
# ============================================================================
print("[2/6] Generating DiD event study...")

fig, ax = plt.subplots(figsize=(8, 5))

np.random.seed(42)
time = np.arange(-10, 11)
effects = np.concatenate([
    np.random.normal(0, 0.3, 10),  # Pre-treatment
    [0],  # Treatment time
    np.cumsum(np.random.normal(0.2, 0.1, 10))  # Post-treatment
])
ci_lower = effects - 0.5
ci_upper = effects + 0.5

ax.plot(time, effects, 'o-', color='#2E86AB', linewidth=2, markersize=6)
ax.fill_between(time, ci_lower, ci_upper, alpha=0.3, color='#2E86AB')
ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Treatment')
ax.set_xlabel('Time Relative to Treatment')
ax.set_ylabel('Treatment Effect')
ax.set_title('Difference-in-Differences Event Study')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'did_event_study.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ did_event_study.png")

# ============================================================================
# 3. RD Discontinuity Plot
# ============================================================================
print("[3/6] Generating RD discontinuity plot...")

fig, ax = plt.subplots(figsize=(8, 5))

np.random.seed(42)
running_var = np.linspace(-50, 50, 200)
cutoff = 0

# Outcome with discontinuity
outcome = (
    10 + 0.05 * running_var +
    np.where(running_var >= cutoff, 2.5, 0) +
    np.random.normal(0, 1, len(running_var))
)

# Split by treatment
control_mask = running_var < cutoff
treated_mask = running_var >= cutoff

ax.scatter(running_var[control_mask], outcome[control_mask],
          alpha=0.4, s=20, color='#2E86AB', label='Control')
ax.scatter(running_var[treated_mask], outcome[treated_mask],
          alpha=0.4, s=20, color='#E63946', label='Treated')

# Local linear regression lines
from scipy.stats import linregress
slope_c, intercept_c, _, _, _ = linregress(running_var[control_mask], outcome[control_mask])
slope_t, intercept_t, _, _, _ = linregress(running_var[treated_mask], outcome[treated_mask])

ax.plot(running_var[control_mask],
       slope_c * running_var[control_mask] + intercept_c,
       color='#2E86AB', linewidth=2.5)
ax.plot(running_var[treated_mask],
       slope_t * running_var[treated_mask] + intercept_t,
       color='#E63946', linewidth=2.5)

ax.axvline(x=cutoff, color='gray', linestyle='--', alpha=0.7, label='Cutoff')
ax.set_xlabel('Running Variable (Credit Score)')
ax.set_ylabel('Outcome')
ax.set_title('Regression Discontinuity Design\nTreatment Effect = 2.5')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'rd_discontinuity.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ rd_discontinuity.png")

# ============================================================================
# 4. Causal Forest Feature Importance
# ============================================================================
print("[4/6] Generating Causal Forest feature importance...")

fig, ax = plt.subplots(figsize=(8, 5))

features = ['Age', 'Income', 'Education', 'Experience', 'Location']
importance = np.array([0.45, 0.32, 0.15, 0.06, 0.02])

colors = plt.cm.YlOrRd(np.linspace(0.4, 0.9, len(features)))
bars = ax.barh(features, importance, color=colors, edgecolor='black', linewidth=1.5)

# Add value labels
for i, (bar, val) in enumerate(zip(bars, importance)):
    ax.text(val + 0.01, i, f'{val:.2f}', va='center', fontweight='bold')

ax.set_xlabel('Importance Score')
ax.set_title('Causal Forest: Variable Importance for CATE')
ax.set_xlim(0, 0.5)
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'causal_forest_importance.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ causal_forest_importance.png")

# ============================================================================
# 5. Synthetic Control Plot
# ============================================================================
print("[5/6] Generating Synthetic Control plot...")

fig, ax = plt.subplots(figsize=(8, 5))

np.random.seed(42)
time = np.arange(1, 31)
treatment_time = 20

# Treated unit
treated = 100 + 2 * time + np.random.normal(0, 3, len(time))
treated[treatment_time:] += 15  # Treatment effect

# Synthetic control
synthetic = 100 + 2 * time + np.random.normal(0, 2, len(time))

ax.plot(time[:treatment_time], treated[:treatment_time],
       'o-', color='#E63946', linewidth=2, label='Treated Unit', markersize=5)
ax.plot(time[treatment_time-1:], treated[treatment_time-1:],
       'o--', color='#E63946', linewidth=2, markersize=5)
ax.plot(time, synthetic, 's-', color='#2E86AB', linewidth=2,
       label='Synthetic Control', markersize=5, alpha=0.7)

# Shaded treatment effect
ax.fill_between(time[treatment_time:],
               treated[treatment_time:],
               synthetic[treatment_time:],
               alpha=0.3, color='orange', label='Treatment Effect')

ax.axvline(x=treatment_time, color='gray', linestyle='--', alpha=0.7)
ax.text(treatment_time, ax.get_ylim()[1] * 0.95, 'Intervention',
       ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

ax.set_xlabel('Time Period')
ax.set_ylabel('Outcome')
ax.set_title('Synthetic Control Method')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'synthetic_control.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ synthetic_control.png")

# ============================================================================
# 6. Sensitivity Analysis (E-values)
# ============================================================================
print("[6/6] Generating Sensitivity Analysis plot...")

fig, ax = plt.subplots(figsize=(8, 5))

# E-value curve
rr = np.linspace(1.0, 5.0, 100)
e_values = rr + np.sqrt(rr * (rr - 1))

ax.plot(rr, e_values, linewidth=3, color='#2E86AB')
ax.fill_between(rr, e_values, alpha=0.2, color='#2E86AB')

# Mark observed effect
observed_rr = 2.5
observed_e = observed_rr + np.sqrt(observed_rr * (observed_rr - 1))
ax.plot([observed_rr], [observed_e], 'o', markersize=15, color='#E63946',
       markeredgecolor='black', markeredgewidth=2, label=f'Observed RR = {observed_rr}')

ax.axhline(y=observed_e, color='gray', linestyle='--', alpha=0.5)
ax.axvline(x=observed_rr, color='gray', linestyle='--', alpha=0.5)

ax.text(observed_rr + 0.2, observed_e + 0.3,
       f'E-value = {observed_e:.2f}',
       fontsize=12, fontweight='bold',
       bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

ax.set_xlabel('Risk Ratio (RR)')
ax.set_ylabel('E-value')
ax.set_title('Sensitivity Analysis: E-value Calculation\nUnmeasured confounder strength needed to explain away effect')
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xlim(1, 5)

plt.tight_layout()
plt.savefig(output_dir / 'sensitivity_evalue.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ sensitivity_evalue.png")

print("\n" + "="*70)
print("✅ All 6 estimator visualizations generated successfully!")
print(f"📁 Output directory: {output_dir.absolute()}")
print("="*70)
