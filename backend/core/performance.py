"""
Performance Measurement Module - 可視化仕様書準拠

Measures chart file size and rendering performance.
Targets: ≤200KB per chart, ≤1.5s LCP

Reference: /home/hirokionodera/CQO/可視化.pdf p.9
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import os
from dataclasses import dataclass


@dataclass
class ChartPerformanceMetrics:
    """Performance metrics for a single chart"""
    chart_id: str
    file_path: str
    file_size_kb: float
    file_size_mb: float
    generation_time_ms: float
    meets_size_target: bool  # ≤200KB
    meets_time_target: bool  # Generation ≤500ms (proxy for LCP ≤1.5s)

    def to_dict(self) -> Dict:
        return {
            "chart_id": self.chart_id,
            "file_path": self.file_path,
            "file_size_kb": round(self.file_size_kb, 2),
            "file_size_mb": round(self.file_size_mb, 4),
            "generation_time_ms": round(self.generation_time_ms, 2),
            "meets_size_target": self.meets_size_target,
            "meets_time_target": self.meets_time_target,
            "status": "✅ PASS" if (self.meets_size_target and self.meets_time_target) else "❌ FAIL",
        }


@dataclass
class PerformanceReport:
    """Aggregate performance report for all charts"""
    total_charts: int
    passed_charts: int
    failed_charts: int
    total_size_mb: float
    avg_size_kb: float
    max_size_kb: float
    avg_generation_time_ms: float
    max_generation_time_ms: float
    charts: List[ChartPerformanceMetrics]

    def to_dict(self) -> Dict:
        return {
            "summary": {
                "total_charts": self.total_charts,
                "passed_charts": self.passed_charts,
                "failed_charts": self.failed_charts,
                "pass_rate": f"{(self.passed_charts / self.total_charts * 100):.1f}%",
                "total_size_mb": round(self.total_size_mb, 2),
                "avg_size_kb": round(self.avg_size_kb, 2),
                "max_size_kb": round(self.max_size_kb, 2),
                "avg_generation_time_ms": round(self.avg_generation_time_ms, 2),
                "max_generation_time_ms": round(self.max_generation_time_ms, 2),
            },
            "charts": [chart.to_dict() for chart in self.charts],
        }


class PerformanceMonitor:
    """Performance monitoring for chart generation"""

    SIZE_TARGET_KB = 200  # Maximum chart size in KB
    TIME_TARGET_MS = 500  # Maximum generation time (proxy for LCP)

    def __init__(self):
        self.metrics: List[ChartPerformanceMetrics] = []
        self.start_times: Dict[str, float] = {}

    def start_measurement(self, chart_id: str):
        """Start timing for a chart generation"""
        self.start_times[chart_id] = time.time()

    def end_measurement(self, chart_id: str, file_path: Path) -> ChartPerformanceMetrics:
        """
        End timing and measure file size

        Args:
            chart_id: Unique identifier for the chart
            file_path: Path to generated chart file

        Returns:
            ChartPerformanceMetrics object
        """
        if chart_id not in self.start_times:
            raise ValueError(f"No start time found for chart {chart_id}")

        # Calculate generation time
        generation_time_s = time.time() - self.start_times[chart_id]
        generation_time_ms = generation_time_s * 1000

        # Measure file size
        if not file_path.exists():
            raise FileNotFoundError(f"Chart file not found: {file_path}")

        file_size_bytes = os.path.getsize(file_path)
        file_size_kb = file_size_bytes / 1024
        file_size_mb = file_size_kb / 1024

        # Check targets
        meets_size_target = file_size_kb <= self.SIZE_TARGET_KB
        meets_time_target = generation_time_ms <= self.TIME_TARGET_MS

        metrics = ChartPerformanceMetrics(
            chart_id=chart_id,
            file_path=str(file_path),
            file_size_kb=file_size_kb,
            file_size_mb=file_size_mb,
            generation_time_ms=generation_time_ms,
            meets_size_target=meets_size_target,
            meets_time_target=meets_time_target,
        )

        self.metrics.append(metrics)
        del self.start_times[chart_id]

        return metrics

    def generate_report(self) -> PerformanceReport:
        """Generate aggregate performance report"""
        if not self.metrics:
            raise ValueError("No metrics recorded")

        total_charts = len(self.metrics)
        passed_charts = sum(
            1 for m in self.metrics
            if m.meets_size_target and m.meets_time_target
        )
        failed_charts = total_charts - passed_charts

        total_size_mb = sum(m.file_size_mb for m in self.metrics)
        avg_size_kb = sum(m.file_size_kb for m in self.metrics) / total_charts
        max_size_kb = max(m.file_size_kb for m in self.metrics)

        avg_generation_time_ms = sum(m.generation_time_ms for m in self.metrics) / total_charts
        max_generation_time_ms = max(m.generation_time_ms for m in self.metrics)

        return PerformanceReport(
            total_charts=total_charts,
            passed_charts=passed_charts,
            failed_charts=failed_charts,
            total_size_mb=total_size_mb,
            avg_size_kb=avg_size_kb,
            max_size_kb=max_size_kb,
            avg_generation_time_ms=avg_generation_time_ms,
            max_generation_time_ms=max_generation_time_ms,
            charts=self.metrics,
        )

    def reset(self):
        """Reset all metrics"""
        self.metrics = []
        self.start_times = {}


def optimize_html_size(html_path: Path) -> Tuple[Path, float]:
    """
    Optimize HTML file size by:
    1. Minifying HTML
    2. Reducing data points (if applicable)
    3. Compressing inline data

    Args:
        html_path: Path to HTML file

    Returns:
        (optimized_path, size_reduction_pct)
    """
    original_size = os.path.getsize(html_path)

    # Read HTML content
    with open(html_path, 'r') as f:
        content = f.read()

    # Simple minification: remove extra whitespace
    import re
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'> <', '><', content)

    # Write optimized content
    optimized_path = html_path.parent / f"{html_path.stem}_optimized{html_path.suffix}"
    with open(optimized_path, 'w') as f:
        f.write(content)

    optimized_size = os.path.getsize(optimized_path)
    size_reduction_pct = (1 - optimized_size / original_size) * 100

    return optimized_path, size_reduction_pct


def analyze_large_charts(report: PerformanceReport, threshold_kb: float = 200) -> List[str]:
    """
    Identify charts exceeding size threshold

    Args:
        report: Performance report
        threshold_kb: Size threshold in KB

    Returns:
        List of chart IDs exceeding threshold with recommendations
    """
    large_charts = []

    for chart in report.charts:
        if chart.file_size_kb > threshold_kb:
            excess_kb = chart.file_size_kb - threshold_kb
            excess_pct = (excess_kb / threshold_kb) * 100

            recommendation = f"Chart {chart.chart_id}: {chart.file_size_kb:.1f}KB "
            recommendation += f"(+{excess_kb:.1f}KB / +{excess_pct:.1f}% over target). "

            # Specific recommendations
            if "surface" in chart.chart_id or "contour" in chart.chart_id:
                recommendation += "Reduce grid resolution from 30x30 to 20x20."
            elif "sankey" in chart.chart_id:
                recommendation += "Simplify flow paths."
            elif "animation" in chart.chart_id:
                recommendation += "Reduce frame count or use static image."
            else:
                recommendation += "Reduce data points or use sampling."

            large_charts.append(recommendation)

    return large_charts
