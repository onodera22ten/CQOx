"""
Logistics Domain Figures
Specialized visualizations for logistics and supply chain analysis
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


def generate_logistics_figures(df: pd.DataFrame, mapping: Dict[str, str], output_dir: Path) -> Dict[str, str]:
    """
    Generate Logistics domain figures (4 figures)

    Figures:
    1. Delivery Performance Analysis
    2. Warehouse Efficiency Heatmap
    3. Route Optimization Comparison
    4. Inventory Turnover by Location
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {}

    logger.info(f"[Logistics] Generating figures for {len(df)} rows")

    # 1. Delivery Performance Analysis
    try:
        # Look for delivery time and treatment columns
        delivery_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['delivery', 'transit', 'shipment', 'lead']):
                delivery_col = col
                break

        treatment_col = mapping.get("treatment")

        if delivery_col and delivery_col in df.columns:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))

            # Subplot 1: Delivery time distribution
            ax = axes[0, 0]
            delivery_times = df[delivery_col].dropna()
            ax.hist(delivery_times, bins=30, color='lightcoral', edgecolor='black', alpha=0.7)
            ax.axvline(delivery_times.mean(), color='red', linestyle='--', linewidth=2,
                      label=f'Mean: {delivery_times.mean():.1f}')
            ax.set_xlabel('Delivery Time', fontsize=11, fontweight='bold')
            ax.set_ylabel('Frequency', fontsize=11, fontweight='bold')
            ax.set_title('Delivery Time Distribution', fontsize=12, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Subplot 2: On-time delivery rate (if treatment exists)
            ax = axes[0, 1]
            if treatment_col and treatment_col in df.columns:
                ontime_by_treatment = df.groupby(treatment_col)[delivery_col].apply(
                    lambda x: (x <= x.median()).sum() / len(x) * 100
                )
                colors = plt.cm.Greens(np.linspace(0.4, 0.8, len(ontime_by_treatment)))
                bars = ax.bar(range(len(ontime_by_treatment)), ontime_by_treatment.values, color=colors)
                ax.set_xticks(range(len(ontime_by_treatment)))
                ax.set_xticklabels(ontime_by_treatment.index, rotation=45, ha='right')
                ax.set_ylabel('On-Time Rate (%)', fontsize=11, fontweight='bold')
                ax.set_title('On-Time Delivery by Method', fontsize=12, fontweight='bold')
                ax.axhline(y=95, color='green', linestyle='--', alpha=0.5, label='Target: 95%')
                ax.legend()

                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
            else:
                ax.text(0.5, 0.5, 'Treatment column\nnot available',
                       ha='center', va='center', fontsize=12, transform=ax.transAxes)
                ax.axis('off')
            ax.grid(True, alpha=0.3, axis='y')

            # Subplot 3: Delivery time box plot by treatment
            ax = axes[1, 0]
            if treatment_col and treatment_col in df.columns:
                treatment_groups = df.groupby(treatment_col)[delivery_col].apply(list)
                bp = ax.boxplot([treatment_groups[t] for t in treatment_groups.index],
                               labels=treatment_groups.index,
                               patch_artist=True)
                for patch in bp['boxes']:
                    patch.set_facecolor('lightblue')
                    patch.set_alpha(0.7)
                ax.set_xticklabels(treatment_groups.index, rotation=45, ha='right')
                ax.set_ylabel('Delivery Time', fontsize=11, fontweight='bold')
                ax.set_title('Delivery Time by Method', fontsize=12, fontweight='bold')
            else:
                ax.text(0.5, 0.5, 'Treatment column\nnot available',
                       ha='center', va='center', fontsize=12, transform=ax.transAxes)
                ax.axis('off')
            ax.grid(True, alpha=0.3, axis='y')

            # Subplot 4: Cumulative delivery curve
            ax = axes[1, 1]
            sorted_times = np.sort(delivery_times)
            cumulative = np.arange(1, len(sorted_times)+1) / len(sorted_times) * 100
            ax.plot(sorted_times, cumulative, linewidth=2, color='darkblue')
            ax.set_xlabel('Delivery Time', fontsize=11, fontweight='bold')
            ax.set_ylabel('Cumulative %', fontsize=11, fontweight='bold')
            ax.set_title('Cumulative Delivery Performance', fontsize=12, fontweight='bold')
            ax.axhline(y=95, color='green', linestyle='--', alpha=0.5, label='95% target')
            ax.legend()
            ax.grid(True, alpha=0.3)

            path = output_dir / "logistics_delivery_performance.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["logistics_delivery_performance"] = str(path)
            logger.info(f"[Logistics] Generated delivery performance chart")
    except Exception as e:
        logger.error(f"[Logistics] Delivery performance failed: {e}")

    # 2. Warehouse Efficiency Heatmap
    try:
        # Look for warehouse and efficiency/inventory columns
        warehouse_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['warehouse', 'location', 'facility', 'site']):
                warehouse_col = col
                break

        time_col = mapping.get("time")
        y_col = mapping.get("y")

        if warehouse_col and warehouse_col in df.columns and time_col and time_col in df.columns and y_col and y_col in df.columns:
            # Create pivot table
            pivot = df.pivot_table(values=y_col, index=warehouse_col, columns=time_col, aggfunc='mean')

            fig, ax = plt.subplots(figsize=(12, 6))
            im = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto')

            # Set ticks
            ax.set_xticks(np.arange(len(pivot.columns)))
            ax.set_yticks(np.arange(len(pivot.index)))
            ax.set_xticklabels(pivot.columns, rotation=45, ha='right')
            ax.set_yticklabels(pivot.index)

            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Performance', fontsize=11, fontweight='bold')

            ax.set_xlabel('Time Period', fontsize=12, fontweight='bold')
            ax.set_ylabel('Warehouse', fontsize=12, fontweight='bold')
            ax.set_title('Warehouse Efficiency Heatmap', fontsize=14, fontweight='bold')

            path = output_dir / "logistics_warehouse_heatmap.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["logistics_warehouse_heatmap"] = str(path)
            logger.info(f"[Logistics] Generated warehouse heatmap")
    except Exception as e:
        logger.error(f"[Logistics] Warehouse heatmap failed: {e}")

    # 3. Route Optimization Comparison
    try:
        distance_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['distance', 'route', 'miles', 'km']):
                distance_col = col
                break

        cost_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['cost', 'expense', 'price']):
                cost_col = col
                break

        treatment_col = mapping.get("treatment")

        if distance_col and cost_col and treatment_col and all(c in df.columns for c in [distance_col, cost_col, treatment_col]):
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # Scatter plot: Distance vs Cost
            for treatment in df[treatment_col].unique():
                subset = df[df[treatment_col] == treatment]
                ax1.scatter(subset[distance_col], subset[cost_col],
                           label=treatment, alpha=0.6, s=50)

            ax1.set_xlabel('Distance', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Cost', fontsize=12, fontweight='bold')
            ax1.set_title('Route Distance vs Cost', fontsize=14, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Bar chart: Average cost per treatment
            avg_cost = df.groupby(treatment_col)[cost_col].mean().sort_values()
            colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(avg_cost)))
            bars = ax2.barh(range(len(avg_cost)), avg_cost.values, color=colors)
            ax2.set_yticks(range(len(avg_cost)))
            ax2.set_yticklabels(avg_cost.index)
            ax2.set_xlabel('Average Cost', fontsize=12, fontweight='bold')
            ax2.set_title('Average Cost by Route Type', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='x')

            # Add value labels
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax2.text(width, bar.get_y() + bar.get_height()/2.,
                        f'{width:.1f}', ha='left', va='center', fontsize=9)

            path = output_dir / "logistics_route_optimization.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["logistics_route_optimization"] = str(path)
            logger.info(f"[Logistics] Generated route optimization chart")
    except Exception as e:
        logger.error(f"[Logistics] Route optimization failed: {e}")

    # 4. Inventory Turnover by Location
    try:
        inventory_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['inventory', 'stock', 'quantity']):
                inventory_col = col
                break

        location_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['location', 'warehouse', 'region', 'site']):
                location_col = col
                break

        if inventory_col and location_col and all(c in df.columns for c in [inventory_col, location_col]):
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # Bar chart: Total inventory by location
            inventory_by_loc = df.groupby(location_col)[inventory_col].sum().sort_values(ascending=False)
            colors = plt.cm.Oranges(np.linspace(0.4, 0.9, len(inventory_by_loc)))
            ax1.bar(range(len(inventory_by_loc)), inventory_by_loc.values, color=colors)
            ax1.set_xticks(range(len(inventory_by_loc)))
            ax1.set_xticklabels(inventory_by_loc.index, rotation=45, ha='right')
            ax1.set_ylabel('Total Inventory', fontsize=12, fontweight='bold')
            ax1.set_title('Inventory by Location', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3, axis='y')

            # Pie chart: Inventory distribution
            ax2.pie(inventory_by_loc.values, labels=inventory_by_loc.index,
                   autopct='%1.1f%%', startangle=90, colors=colors)
            ax2.set_title('Inventory Distribution', fontsize=14, fontweight='bold')

            path = output_dir / "logistics_inventory_turnover.png"
            plt.tight_layout()
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close()
            figures["logistics_inventory_turnover"] = str(path)
            logger.info(f"[Logistics] Generated inventory turnover chart")
    except Exception as e:
        logger.error(f"[Logistics] Inventory turnover failed: {e}")

    logger.info(f"[Logistics] Generated {len(figures)} figures")
    return figures
