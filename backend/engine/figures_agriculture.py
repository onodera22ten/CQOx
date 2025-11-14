"""
Agriculture Domain Figures
Specialized visualizations for agricultural and farming analysis
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


def generate_agriculture_figures(df: pd.DataFrame, mapping: Dict[str, str], output_dir: Path) -> Dict[str, str]:
    """
    Generate Agriculture domain figures (4 figures)

    Figures:
    1. Crop Yield Analysis
    2. Weather Impact on Production
    3. Fertilizer Effectiveness Comparison
    4. Seasonal Performance Heatmap
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {}

    logger.info(f"[Agriculture] Generating figures for {len(df)} rows")

    # 1. Crop Yield Analysis
    try:
        yield_col = mapping.get("y")
        treatment_col = mapping.get("treatment")

        if yield_col and treatment_col and all(c in df.columns for c in [yield_col, treatment_col]):
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # Box plot by treatment
            treatment_groups = df.groupby(treatment_col)[yield_col].apply(list)
            bp = ax1.boxplot([treatment_groups[t] for t in treatment_groups.index],
                            labels=treatment_groups.index,
                            patch_artist=True,
                            showmeans=True)

            colors = plt.cm.Greens(np.linspace(0.4, 0.9, len(bp['boxes'])))
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.8)

            ax1.set_xlabel('Treatment/Variety', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Yield', fontsize=12, fontweight='bold')
            ax1.set_title('Crop Yield by Treatment', fontsize=14, fontweight='bold')
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, alpha=0.3, axis='y')

            # Bar chart: Mean yield comparison
            mean_yield = df.groupby(treatment_col)[yield_col].mean().sort_values(ascending=False)
            colors = plt.cm.YlGn(np.linspace(0.4, 0.9, len(mean_yield)))
            bars = ax2.bar(range(len(mean_yield)), mean_yield.values, color=colors)
            ax2.set_xticks(range(len(mean_yield)))
            ax2.set_xticklabels(mean_yield.index, rotation=45, ha='right')
            ax2.set_ylabel('Mean Yield', fontsize=12, fontweight='bold')
            ax2.set_title('Average Yield Comparison', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')

            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}', ha='center', va='bottom', fontsize=9)

            path = output_dir / "agri_crop_yield.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["agri_crop_yield"] = str(path)
            logger.info(f"[Agriculture] Generated crop yield chart")
    except Exception as e:
        logger.error(f"[Agriculture] Crop yield failed: {e}")

    # 2. Weather Impact on Production
    try:
        weather_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['weather', 'rain', 'precipitation', 'temp', 'temperature']):
                weather_col = col
                break

        yield_col = mapping.get("y")

        if weather_col and yield_col and all(c in df.columns for c in [weather_col, yield_col]):
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # Scatter plot: Weather vs Yield
            ax1.scatter(df[weather_col], df[yield_col], alpha=0.5, color='skyblue', s=50)

            # Add trend line
            z = np.polyfit(df[weather_col].dropna(), df[yield_col].dropna(), 1)
            p = np.poly1d(z)
            x_trend = np.linspace(df[weather_col].min(), df[weather_col].max(), 100)
            ax1.plot(x_trend, p(x_trend), "r--", linewidth=2, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')

            ax1.set_xlabel('Weather Factor', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Yield', fontsize=12, fontweight='bold')
            ax1.set_title('Weather Impact on Yield', fontsize=14, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Binned analysis
            weather_bins = pd.cut(df[weather_col], bins=5)
            yield_by_weather = df.groupby(weather_bins)[yield_col].mean()

            ax2.bar(range(len(yield_by_weather)), yield_by_weather.values,
                   color='lightcoral', edgecolor='black', alpha=0.7)
            ax2.set_xticks(range(len(yield_by_weather)))
            ax2.set_xticklabels([f'{interval.left:.1f}-{interval.right:.1f}'
                                for interval in yield_by_weather.index], rotation=45, ha='right')
            ax2.set_xlabel('Weather Range', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Mean Yield', fontsize=12, fontweight='bold')
            ax2.set_title('Yield by Weather Condition', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')

            path = output_dir / "agri_weather_impact.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["agri_weather_impact"] = str(path)
            logger.info(f"[Agriculture] Generated weather impact chart")
    except Exception as e:
        logger.error(f"[Agriculture] Weather impact failed: {e}")

    # 3. Fertilizer Effectiveness Comparison
    try:
        fertilizer_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['fertilizer', 'nutrient', 'treatment']):
                fertilizer_col = col
                break

        if not fertilizer_col:
            fertilizer_col = mapping.get("treatment")

        yield_col = mapping.get("y")

        if fertilizer_col and yield_col and all(c in df.columns for c in [fertilizer_col, yield_col]):
            fig, ax = plt.subplots(figsize=(12, 6))

            # Calculate yield improvement
            baseline = df[df[fertilizer_col] == df[fertilizer_col].unique()[0]][yield_col].mean()
            yield_improvement = df.groupby(fertilizer_col)[yield_col].mean() - baseline

            colors = ['green' if x >= 0 else 'red' for x in yield_improvement.values]
            bars = ax.barh(range(len(yield_improvement)), yield_improvement.values, color=colors, alpha=0.7)

            ax.set_yticks(range(len(yield_improvement)))
            ax.set_yticklabels(yield_improvement.index)
            ax.set_xlabel('Yield Improvement vs Baseline', fontsize=12, fontweight='bold')
            ax.set_title('Fertilizer Effectiveness Comparison', fontsize=14, fontweight='bold')
            ax.axvline(x=0, color='black', linestyle='-', linewidth=1)
            ax.grid(True, alpha=0.3, axis='x')

            for i, val in enumerate(yield_improvement.values):
                ax.text(val, i, f'{val:+.1f}', va='center',
                       ha='left' if val >= 0 else 'right', fontsize=9)

            path = output_dir / "agri_fertilizer_effectiveness.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["agri_fertilizer_effectiveness"] = str(path)
            logger.info(f"[Agriculture] Generated fertilizer effectiveness chart")
    except Exception as e:
        logger.error(f"[Agriculture] Fertilizer effectiveness failed: {e}")

    # 4. Seasonal Performance Heatmap
    try:
        season_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['season', 'month', 'quarter', 'time']):
                season_col = col
                break

        if not season_col:
            season_col = mapping.get("time")

        plot_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['plot', 'field', 'region', 'location']):
                plot_col = col
                break

        yield_col = mapping.get("y")

        if season_col and plot_col and yield_col and all(c in df.columns for c in [season_col, plot_col, yield_col]):
            # Create pivot table
            pivot = df.pivot_table(values=yield_col, index=plot_col, columns=season_col, aggfunc='mean')

            fig, ax = plt.subplots(figsize=(12, 6))
            im = ax.imshow(pivot.values, cmap='YlGn', aspect='auto')

            # Set ticks
            ax.set_xticks(np.arange(len(pivot.columns)))
            ax.set_yticks(np.arange(len(pivot.index)))
            ax.set_xticklabels(pivot.columns, rotation=45, ha='right')
            ax.set_yticklabels(pivot.index)

            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Yield', fontsize=11, fontweight='bold')

            # Add values in cells
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    if not np.isnan(pivot.values[i, j]):
                        text = ax.text(j, i, f'{pivot.values[i, j]:.1f}',
                                     ha="center", va="center", color="black", fontsize=8)

            ax.set_xlabel('Season/Time', fontsize=12, fontweight='bold')
            ax.set_ylabel('Plot/Field', fontsize=12, fontweight='bold')
            ax.set_title('Seasonal Performance Heatmap', fontsize=14, fontweight='bold')

            path = output_dir / "agri_seasonal_heatmap.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["agri_seasonal_heatmap"] = str(path)
            logger.info(f"[Agriculture] Generated seasonal heatmap")
    except Exception as e:
        logger.error(f"[Agriculture] Seasonal heatmap failed: {e}")

    logger.info(f"[Agriculture] Generated {len(figures)} figures")
    return figures
