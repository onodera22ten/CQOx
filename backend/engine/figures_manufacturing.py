"""
Manufacturing Domain Figures
Specialized visualizations for manufacturing and production analysis
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def generate_manufacturing_figures(df: pd.DataFrame, mapping: Dict[str, str], output_dir: Path) -> Dict[str, str]:
    """
    Generate Manufacturing domain figures (4 figures)

    Figures:
    1. Quality Control Chart (X-bar and R charts)
    2. Yield Optimization Analysis
    3. Downtime Analysis (Pareto chart)
    4. Supply Chain Lead Time Distribution
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {}

    logger.info(f"[Manufacturing] Generating figures for {len(df)} rows")

    # 1. Quality Control Chart
    try:
        y_col = mapping.get("y")
        treatment_col = mapping.get("treatment")

        if y_col and y_col in df.columns:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

            # X-bar chart (mean)
            if treatment_col and treatment_col in df.columns:
                groups = df.groupby(treatment_col)[y_col]
                means = groups.mean()
                stds = groups.std()

                x_positions = np.arange(len(means))
                ax1.plot(x_positions, means.values, 'o-', color='blue', linewidth=2, markersize=8)

                # Control limits (mean ± 3σ)
                grand_mean = df[y_col].mean()
                grand_std = df[y_col].std()
                ucl = grand_mean + 3 * grand_std
                lcl = grand_mean - 3 * grand_std

                ax1.axhline(y=grand_mean, color='green', linestyle='--', linewidth=2, label='Center Line')
                ax1.axhline(y=ucl, color='red', linestyle='--', linewidth=1.5, label='UCL (+3σ)')
                ax1.axhline(y=lcl, color='red', linestyle='--', linewidth=1.5, label='LCL (-3σ)')

                ax1.set_xlabel('Group', fontsize=12, fontweight='bold')
                ax1.set_ylabel('Mean Value', fontsize=12, fontweight='bold')
                ax1.set_title('X-bar Chart (Quality Control)', fontsize=14, fontweight='bold')
                ax1.set_xticks(x_positions)
                ax1.set_xticklabels(means.index, rotation=45, ha='right')
                ax1.legend()
                ax1.grid(True, alpha=0.3)

                # R chart (range)
                ranges = groups.apply(lambda x: x.max() - x.min())
                ax2.plot(x_positions, ranges.values, 's-', color='orange', linewidth=2, markersize=8)

                mean_range = ranges.mean()
                ax2.axhline(y=mean_range, color='green', linestyle='--', linewidth=2, label='R-bar')
                ax2.axhline(y=mean_range * 2.114, color='red', linestyle='--', linewidth=1.5, label='UCL (D4*R-bar)')

                ax2.set_xlabel('Group', fontsize=12, fontweight='bold')
                ax2.set_ylabel('Range', fontsize=12, fontweight='bold')
                ax2.set_title('R Chart (Variability Control)', fontsize=14, fontweight='bold')
                ax2.set_xticks(x_positions)
                ax2.set_xticklabels(ranges.index, rotation=45, ha='right')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
            else:
                # Simple control chart without groups
                values = df[y_col].values
                x = np.arange(len(values))

                ax1.plot(x, values, 'o-', color='blue', markersize=4, alpha=0.6)

                mean = values.mean()
                std = values.std()
                ax1.axhline(y=mean, color='green', linestyle='--', linewidth=2, label='Mean')
                ax1.axhline(y=mean + 3*std, color='red', linestyle='--', linewidth=1.5, label='UCL (+3σ)')
                ax1.axhline(y=mean - 3*std, color='red', linestyle='--', linewidth=1.5, label='LCL (-3σ)')

                ax1.set_xlabel('Sample', fontsize=12, fontweight='bold')
                ax1.set_ylabel('Value', fontsize=12, fontweight='bold')
                ax1.set_title('Quality Control Chart', fontsize=14, fontweight='bold')
                ax1.legend()
                ax1.grid(True, alpha=0.3)

                ax2.axis('off')

            path = output_dir / "mfg_quality_control.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["mfg_quality_control"] = str(path)
            logger.info(f"[Manufacturing] Generated quality control chart")
    except Exception as e:
        logger.error(f"[Manufacturing] Quality control chart failed: {e}")

    # 2. Yield Optimization Analysis
    try:
        # Look for yield column
        yield_col = None
        for col in df.columns:
            if 'yield' in col.lower():
                yield_col = col
                break

        if not yield_col and y_col:
            yield_col = y_col

        if yield_col and yield_col in df.columns and treatment_col and treatment_col in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Box plot by treatment
            treatment_groups = df.groupby(treatment_col)[yield_col].apply(list)

            bp = ax.boxplot([treatment_groups[t] for t in treatment_groups.index],
                           labels=treatment_groups.index,
                           patch_artist=True,
                           showmeans=True)

            # Color boxes
            colors = plt.cm.Set3(np.linspace(0, 1, len(bp['boxes'])))
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)

            # Add mean values as text
            means = [np.mean(treatment_groups[t]) for t in treatment_groups.index]
            for i, mean in enumerate(means):
                ax.text(i+1, mean, f'{mean:.2f}', ha='center', va='bottom',
                       fontweight='bold', fontsize=10)

            ax.set_xlabel('Treatment Group', fontsize=12, fontweight='bold')
            ax.set_ylabel('Yield', fontsize=12, fontweight='bold')
            ax.set_title('Yield Optimization Analysis', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')

            path = output_dir / "mfg_yield_optimization.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["mfg_yield_optimization"] = str(path)
            logger.info(f"[Manufacturing] Generated yield optimization chart")
    except Exception as e:
        logger.error(f"[Manufacturing] Yield optimization failed: {e}")

    # 3. Downtime Analysis (Pareto Chart)
    try:
        # Look for downtime or defect columns
        downtime_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['downtime', 'defect', 'failure', 'issue']):
                downtime_col = col
                break

        machine_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['machine', 'equipment', 'line', 'station']):
                machine_col = col
                break

        if downtime_col and downtime_col in df.columns and machine_col and machine_col in df.columns:
            fig, ax1 = plt.subplots(figsize=(12, 6))

            # Aggregate downtime by machine
            downtime_by_machine = df.groupby(machine_col)[downtime_col].sum().sort_values(ascending=False)

            # Pareto chart
            x_pos = np.arange(len(downtime_by_machine))
            ax1.bar(x_pos, downtime_by_machine.values, color='steelblue', alpha=0.8)
            ax1.set_xlabel('Machine/Line', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Total Downtime', fontsize=12, fontweight='bold', color='steelblue')
            ax1.set_title('Downtime Pareto Analysis', fontsize=14, fontweight='bold')
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels(downtime_by_machine.index, rotation=45, ha='right')
            ax1.tick_params(axis='y', labelcolor='steelblue')

            # Cumulative percentage line
            ax2 = ax1.twinx()
            cumulative_pct = (downtime_by_machine.cumsum() / downtime_by_machine.sum()) * 100
            ax2.plot(x_pos, cumulative_pct.values, 'r-o', linewidth=2, markersize=6)
            ax2.set_ylabel('Cumulative %', fontsize=12, fontweight='bold', color='red')
            ax2.tick_params(axis='y', labelcolor='red')
            ax2.set_ylim([0, 105])
            ax2.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='80% line')

            ax1.grid(True, alpha=0.3, axis='y')

            path = output_dir / "mfg_downtime_pareto.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["mfg_downtime_pareto"] = str(path)
            logger.info(f"[Manufacturing] Generated downtime Pareto chart")
        else:
            # Fallback: simple bar chart
            logger.warning(f"[Manufacturing] Downtime/machine columns not found, using fallback")
    except Exception as e:
        logger.error(f"[Manufacturing] Downtime analysis failed: {e}")

    # 4. Supply Chain Lead Time Distribution
    try:
        # Look for lead time or delivery time
        leadtime_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['lead_time', 'leadtime', 'delivery_time', 'transit']):
                leadtime_col = col
                break

        if leadtime_col and leadtime_col in df.columns:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            lead_times = df[leadtime_col].dropna()

            # Histogram
            ax1.hist(lead_times, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
            ax1.axvline(lead_times.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {lead_times.mean():.1f}')
            ax1.axvline(lead_times.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {lead_times.median():.1f}')
            ax1.set_xlabel('Lead Time', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold')
            ax1.set_title('Lead Time Distribution', fontsize=14, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3, axis='y')

            # Box plot
            ax2.boxplot(lead_times, vert=True, patch_artist=True,
                       boxprops=dict(facecolor='lightblue', alpha=0.7),
                       medianprops=dict(color='red', linewidth=2))
            ax2.set_ylabel('Lead Time', fontsize=12, fontweight='bold')
            ax2.set_title('Lead Time Box Plot', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')

            # Add statistics text
            stats_text = f"Mean: {lead_times.mean():.1f}\nMedian: {lead_times.median():.1f}\nStd: {lead_times.std():.1f}\nMin: {lead_times.min():.1f}\nMax: {lead_times.max():.1f}"
            ax2.text(1.15, 0.5, stats_text, transform=ax2.transAxes,
                    fontsize=10, verticalalignment='center',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

            path = output_dir / "mfg_leadtime_distribution.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["mfg_leadtime_distribution"] = str(path)
            logger.info(f"[Manufacturing] Generated lead time distribution")
    except Exception as e:
        logger.error(f"[Manufacturing] Lead time analysis failed: {e}")

    logger.info(f"[Manufacturing] Generated {len(figures)} figures")
    return figures
