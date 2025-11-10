"""
Energy Domain Figures
Specialized visualizations for energy and power systems analysis
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


def generate_energy_figures(df: pd.DataFrame, mapping: Dict[str, str], output_dir: Path) -> Dict[str, str]:
    """
    Generate Energy domain figures (4 figures)

    Figures:
    1. Power Generation vs Consumption
    2. Renewable Energy Mix Analysis
    3. Grid Load Pattern (24h cyclical)
    4. Efficiency Optimization by Source
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {}

    logger.info(f"[Energy] Generating figures for {len(df)} rows")

    # 1. Power Generation vs Consumption
    try:
        gen_col = None
        cons_col = None

        for col in df.columns:
            if any(kw in col.lower() for kw in ['generation', 'output', 'produced', 'supply']):
                gen_col = col
            if any(kw in col.lower() for kw in ['consumption', 'demand', 'load', 'usage']):
                cons_col = col

        time_col = mapping.get("time")

        if gen_col and cons_col and all(c in df.columns for c in [gen_col, cons_col]):
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # Time series plot (if time exists)
            if time_col and time_col in df.columns:
                ax1.plot(df[time_col], df[gen_col], label='Generation', linewidth=2, color='green')
                ax1.plot(df[time_col], df[cons_col], label='Consumption', linewidth=2, color='red')
                ax1.fill_between(df[time_col],
                                df[gen_col], df[cons_col],
                                where=(df[gen_col] >= df[cons_col]),
                                alpha=0.3, color='green', label='Surplus')
                ax1.fill_between(df[time_col],
                                df[gen_col], df[cons_col],
                                where=(df[gen_col] < df[cons_col]),
                                alpha=0.3, color='red', label='Deficit')
                ax1.set_xlabel('Time', fontsize=12, fontweight='bold')
                ax1.tick_params(axis='x', rotation=45)
            else:
                ax1.plot(df[gen_col].values, label='Generation', linewidth=2, color='green')
                ax1.plot(df[cons_col].values, label='Consumption', linewidth=2, color='red')
                ax1.set_xlabel('Sample', fontsize=12, fontweight='bold')

            ax1.set_ylabel('Power (kWh)', fontsize=12, fontweight='bold')
            ax1.set_title('Power Generation vs Consumption', fontsize=14, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Balance analysis
            balance = df[gen_col] - df[cons_col]
            ax2.hist(balance, bins=30, color='lightblue', edgecolor='black', alpha=0.7)
            ax2.axvline(0, color='red', linestyle='--', linewidth=2, label='Balance Point')
            ax2.axvline(balance.mean(), color='green', linestyle='--', linewidth=2,
                       label=f'Mean: {balance.mean():.1f}')
            ax2.set_xlabel('Generation - Consumption', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Frequency', fontsize=12, fontweight='bold')
            ax2.set_title('Power Balance Distribution', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis='y')

            path = output_dir / "energy_generation_consumption.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["energy_generation_consumption"] = str(path)
            logger.info(f"[Energy] Generated power generation chart")
    except Exception as e:
        logger.error(f"[Energy] Power generation chart failed: {e}")

    # 2. Renewable Energy Mix Analysis
    try:
        source_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['source', 'type', 'energy_type', 'fuel']):
                source_col = col
                break

        if not source_col:
            source_col = mapping.get("treatment")

        output_col = mapping.get("y")

        if source_col and output_col and all(c in df.columns for c in [source_col, output_col]):
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # Pie chart: Energy mix
            energy_by_source = df.groupby(source_col)[output_col].sum()
            colors = plt.cm.Set3(np.linspace(0, 1, len(energy_by_source)))

            ax1.pie(energy_by_source.values, labels=energy_by_source.index,
                   autopct='%1.1f%%', startangle=90, colors=colors)
            ax1.set_title('Energy Generation Mix', fontsize=14, fontweight='bold')

            # Bar chart: Output by source
            ax2.bar(range(len(energy_by_source)), energy_by_source.values, color=colors)
            ax2.set_xticks(range(len(energy_by_source)))
            ax2.set_xticklabels(energy_by_source.index, rotation=45, ha='right')
            ax2.set_ylabel('Total Output (kWh)', fontsize=12, fontweight='bold')
            ax2.set_title('Output by Energy Source', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')

            for i, val in enumerate(energy_by_source.values):
                ax2.text(i, val, f'{val:.0f}', ha='center', va='bottom', fontsize=9)

            path = output_dir / "energy_renewable_mix.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["energy_renewable_mix"] = str(path)
            logger.info(f"[Energy] Generated renewable mix chart")
    except Exception as e:
        logger.error(f"[Energy] Renewable mix chart failed: {e}")

    # 3. Grid Load Pattern (24h cyclical)
    try:
        load_col = mapping.get("y")
        time_col = mapping.get("time")

        if load_col and load_col in df.columns:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

            # Time series
            if time_col and time_col in df.columns:
                ax1.plot(df[time_col], df[load_col], linewidth=2, color='darkblue')
                ax1.set_xlabel('Time', fontsize=12, fontweight='bold')
                ax1.tick_params(axis='x', rotation=45)
            else:
                ax1.plot(df[load_col].values, linewidth=2, color='darkblue')
                ax1.set_xlabel('Sample', fontsize=12, fontweight='bold')

            ax1.set_ylabel('Load (kWh)', fontsize=12, fontweight='bold')
            ax1.set_title('Grid Load Over Time', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)

            # Load duration curve
            sorted_load = np.sort(df[load_col].dropna())[::-1]
            duration_pct = np.arange(len(sorted_load)) / len(sorted_load) * 100

            ax2.plot(duration_pct, sorted_load, linewidth=2, color='darkred')
            ax2.fill_between(duration_pct, sorted_load, alpha=0.3, color='red')

            # Mark peak, median, base load
            peak_load = sorted_load[0]
            median_load = sorted_load[len(sorted_load)//2]
            base_load = sorted_load[-1]

            ax2.axhline(peak_load, color='red', linestyle='--', alpha=0.5, label=f'Peak: {peak_load:.0f}')
            ax2.axhline(median_load, color='orange', linestyle='--', alpha=0.5, label=f'Median: {median_load:.0f}')
            ax2.axhline(base_load, color='green', linestyle='--', alpha=0.5, label=f'Base: {base_load:.0f}')

            ax2.set_xlabel('Duration (%)', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Load (kWh)', fontsize=12, fontweight='bold')
            ax2.set_title('Load Duration Curve', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            path = output_dir / "energy_grid_load_pattern.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["energy_grid_load_pattern"] = str(path)
            logger.info(f"[Energy] Generated grid load pattern")
    except Exception as e:
        logger.error(f"[Energy] Grid load pattern failed: {e}")

    # 4. Efficiency Optimization by Source
    try:
        source_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['source', 'type', 'plant']):
                source_col = col
                break

        if not source_col:
            source_col = mapping.get("treatment")

        efficiency_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['efficiency', 'utilization', 'capacity_factor']):
                efficiency_col = col
                break

        if not efficiency_col:
            efficiency_col = mapping.get("y")

        if source_col and efficiency_col and all(c in df.columns for c in [source_col, efficiency_col]):
            fig, ax = plt.subplots(figsize=(12, 6))

            # Box plot: Efficiency by source
            source_groups = df.groupby(source_col)[efficiency_col].apply(list)
            bp = ax.boxplot([source_groups[s] for s in source_groups.index],
                           labels=source_groups.index,
                           patch_artist=True,
                           showmeans=True)

            colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(bp['boxes'])))
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)

            ax.set_xlabel('Energy Source', fontsize=12, fontweight='bold')
            ax.set_ylabel('Efficiency', fontsize=12, fontweight='bold')
            ax.set_title('Efficiency by Energy Source', fontsize=14, fontweight='bold')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3, axis='y')

            # Add mean values as text
            means = [np.mean(source_groups[s]) for s in source_groups.index]
            for i, mean in enumerate(means):
                ax.text(i+1, ax.get_ylim()[1] * 0.95, f'μ={mean:.2f}',
                       ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

            path = output_dir / "energy_efficiency_optimization.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["energy_efficiency_optimization"] = str(path)
            logger.info(f"[Energy] Generated efficiency optimization chart")
    except Exception as e:
        logger.error(f"[Energy] Efficiency optimization failed: {e}")

    logger.info(f"[Energy] Generated {len(figures)} figures")
    return figures
