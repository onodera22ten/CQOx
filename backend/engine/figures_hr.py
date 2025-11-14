"""
Human Resources Domain Figures
Specialized visualizations for HR and talent management analysis
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


def generate_hr_figures(df: pd.DataFrame, mapping: Dict[str, str], output_dir: Path) -> Dict[str, str]:
    """
    Generate HR domain figures (4 figures)

    Figures:
    1. Attrition Analysis
    2. Training Effectiveness
    3. Performance Distribution by Department
    4. Retention Curve Analysis
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {}

    logger.info(f"[HR] Generating figures for {len(df)} rows")

    # 1. Attrition Analysis
    try:
        attrition_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['attrition', 'turnover', 'left', 'churn']):
                attrition_col = col
                break

        dept_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['department', 'dept', 'division', 'team']):
                dept_col = col
                break

        if attrition_col and attrition_col in df.columns:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # Overall attrition rate
            if pd.api.types.is_numeric_dtype(df[attrition_col]):
                attrition_rate = df[attrition_col].mean()
            else:
                attrition_rate = (df[attrition_col] == 1).sum() / len(df)

            ax1.bar(['Attrition Rate'], [attrition_rate * 100], color='salmon', width=0.5)
            ax1.set_ylabel('Attrition Rate (%)', fontsize=12, fontweight='bold')
            ax1.set_title('Overall Attrition Rate', fontsize=14, fontweight='bold')
            ax1.set_ylim([0, 100])
            ax1.axhline(y=15, color='red', linestyle='--', alpha=0.5, label='Industry Avg: 15%')
            ax1.text(0, attrition_rate * 100 + 3, f'{attrition_rate*100:.1f}%',
                    ha='center', fontweight='bold', fontsize=14)
            ax1.legend()
            ax1.grid(True, alpha=0.3, axis='y')

            # Attrition by department
            if dept_col and dept_col in df.columns:
                if pd.api.types.is_numeric_dtype(df[attrition_col]):
                    attrition_by_dept = df.groupby(dept_col)[attrition_col].mean() * 100
                else:
                    attrition_by_dept = df.groupby(dept_col)[attrition_col].apply(
                        lambda x: (x == 1).sum() / len(x) * 100
                    )

                colors = plt.cm.RdYlGn_r(attrition_by_dept / 100)
                ax2.barh(range(len(attrition_by_dept)), attrition_by_dept.values, color=colors)
                ax2.set_yticks(range(len(attrition_by_dept)))
                ax2.set_yticklabels(attrition_by_dept.index)
                ax2.set_xlabel('Attrition Rate (%)', fontsize=12, fontweight='bold')
                ax2.set_title('Attrition by Department', fontsize=14, fontweight='bold')
                ax2.grid(True, alpha=0.3, axis='x')

                for i, val in enumerate(attrition_by_dept.values):
                    ax2.text(val + 1, i, f'{val:.1f}%', va='center', fontsize=9)
            else:
                ax2.axis('off')

            path = output_dir / "hr_attrition_analysis.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["hr_attrition_analysis"] = str(path)
            logger.info(f"[HR] Generated attrition analysis")
    except Exception as e:
        logger.error(f"[HR] Attrition analysis failed: {e}")

    # 2. Training Effectiveness
    try:
        training_col = mapping.get("treatment")
        performance_col = mapping.get("y")

        if training_col and performance_col and all(c in df.columns for c in [training_col, performance_col]):
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # Box plot: Performance by training
            training_groups = df.groupby(training_col)[performance_col].apply(list)
            bp = ax1.boxplot([training_groups[t] for t in training_groups.index],
                            labels=training_groups.index,
                            patch_artist=True,
                            showmeans=True)

            colors = plt.cm.Set2(np.linspace(0, 1, len(bp['boxes'])))
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)

            ax1.set_xlabel('Training Program', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Performance Score', fontsize=12, fontweight='bold')
            ax1.set_title('Performance by Training Program', fontsize=14, fontweight='bold')
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, alpha=0.3, axis='y')

            # Bar chart: Mean performance improvement
            mean_perf = df.groupby(training_col)[performance_col].mean().sort_values(ascending=False)
            colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(mean_perf)))
            bars = ax2.bar(range(len(mean_perf)), mean_perf.values, color=colors)
            ax2.set_xticks(range(len(mean_perf)))
            ax2.set_xticklabels(mean_perf.index, rotation=45, ha='right')
            ax2.set_ylabel('Mean Performance', fontsize=12, fontweight='bold')
            ax2.set_title('Mean Performance by Training', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')

            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}', ha='center', va='bottom', fontsize=9)

            path = output_dir / "hr_training_effectiveness.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["hr_training_effectiveness"] = str(path)
            logger.info(f"[HR] Generated training effectiveness chart")
    except Exception as e:
        logger.error(f"[HR] Training effectiveness failed: {e}")

    # 3. Performance Distribution by Department
    try:
        perf_col = mapping.get("y")
        dept_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['department', 'dept', 'division']):
                dept_col = col
                break

        if perf_col and dept_col and all(c in df.columns for c in [perf_col, dept_col]):
            fig, ax = plt.subplots(figsize=(12, 6))

            dept_groups = df.groupby(dept_col)[perf_col].apply(list)
            positions = np.arange(len(dept_groups))

            # Violin plot
            parts = ax.violinplot([dept_groups[d] for d in dept_groups.index],
                                 positions=positions,
                                 showmeans=True,
                                 showmedians=True)

            ax.set_xticks(positions)
            ax.set_xticklabels(dept_groups.index, rotation=45, ha='right')
            ax.set_ylabel('Performance Score', fontsize=12, fontweight='bold')
            ax.set_xlabel('Department', fontsize=12, fontweight='bold')
            ax.set_title('Performance Distribution by Department', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')

            path = output_dir / "hr_performance_distribution.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["hr_performance_distribution"] = str(path)
            logger.info(f"[HR] Generated performance distribution chart")
    except Exception as e:
        logger.error(f"[HR] Performance distribution failed: {e}")

    # 4. Retention Curve Analysis
    try:
        tenure_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['tenure', 'years', 'months', 'duration']):
                tenure_col = col
                break

        if tenure_col and tenure_col in df.columns:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            tenure_data = df[tenure_col].dropna()

            # Histogram
            ax1.hist(tenure_data, bins=30, color='lightgreen', edgecolor='black', alpha=0.7)
            ax1.axvline(tenure_data.mean(), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {tenure_data.mean():.1f}')
            ax1.axvline(tenure_data.median(), color='blue', linestyle='--', linewidth=2,
                       label=f'Median: {tenure_data.median():.1f}')
            ax1.set_xlabel('Tenure', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold')
            ax1.set_title('Tenure Distribution', fontsize=14, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3, axis='y')

            # Retention curve (survival-like)
            sorted_tenure = np.sort(tenure_data)
            retention_pct = (1 - np.arange(len(sorted_tenure)) / len(sorted_tenure)) * 100
            ax2.plot(sorted_tenure, retention_pct, linewidth=2, color='darkgreen')
            ax2.set_xlabel('Tenure', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Retention Rate (%)', fontsize=12, fontweight='bold')
            ax2.set_title('Employee Retention Curve', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim([0, 105])

            path = output_dir / "hr_retention_curve.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["hr_retention_curve"] = str(path)
            logger.info(f"[HR] Generated retention curve")
    except Exception as e:
        logger.error(f"[HR] Retention curve failed: {e}")

    logger.info(f"[HR] Generated {len(figures)} figures")
    return figures
