"""
Visualization SSOT Module - 可視化仕様書準拠

Single Source of Truth for:
- Colors (Marketing channels: Search, Social, Display, Email, Video)
- Units (USD, %, days, etc.)
- Periods (2024-Q1, etc.)
- Thresholds (SMD=0.1, IV F=10, etc.)
- Download formats (PNG, CSV)
- Performance targets (≤200KB, ≤1.5s LCP)

Reference: /home/hirokionodera/CQO/可視化.pdf
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import os


# ============================================================================
# COLOR SSOT - Marketing Channels (可視化.pdf p.3)
# ============================================================================

class ChannelColor:
    """Marketing channel color palette - SSOT"""
    SEARCH = "#3B82F6"   # Blue
    SOCIAL = "#EF4444"   # Red
    DISPLAY = "#10B981"  # Green
    EMAIL = "#A855F7"    # Purple
    VIDEO = "#F59E0B"    # Orange

    # Additional channels
    AFFILIATE = "#EC4899"  # Pink
    DIRECT = "#6B7280"     # Gray
    REFERRAL = "#14B8A6"   # Teal

    @classmethod
    def get_channel_color(cls, channel_name: str) -> str:
        """Get color for channel name (case-insensitive)"""
        channel_upper = channel_name.upper()
        return getattr(cls, channel_upper, cls.DIRECT)

    @classmethod
    def get_all_colors(cls) -> List[str]:
        """Get all defined colors as list"""
        return [
            cls.SEARCH, cls.SOCIAL, cls.DISPLAY,
            cls.EMAIL, cls.VIDEO, cls.AFFILIATE,
            cls.DIRECT, cls.REFERRAL
        ]


# ============================================================================
# THRESHOLD SSOT - Statistical Quality Gates (可視化.pdf p.7)
# ============================================================================

@dataclass(frozen=True)
class ThresholdSSOT:
    """Statistical thresholds for quality diagnostics"""

    # Balance checks
    SMD_THRESHOLD: float = 0.1          # Standardized Mean Difference
    SMD_IDEAL: float = 0.05             # Ideal SMD target

    # IV checks
    IV_F_THRESHOLD: float = 10.0        # First-stage F-statistic
    IV_F_STRONG: float = 20.0           # Strong instrument threshold

    # Overlap checks
    OVERLAP_MIN: float = 0.1            # Minimum propensity overlap
    OVERLAP_MAX: float = 0.9            # Maximum propensity overlap

    # CI significance
    CI_LEVEL: float = 0.95              # 95% confidence interval
    ALPHA: float = 0.05                 # Significance level

    # Performance
    MAX_CHART_SIZE_KB: int = 200        # Maximum chart size
    MAX_LCP_SECONDS: float = 1.5        # Largest Contentful Paint target

    # ROI thresholds
    ROI_BREAK_EVEN: float = 0.0         # Break-even ROI
    ROI_GOOD: float = 1.0               # 100% ROI = 2x return
    ROI_EXCELLENT: float = 3.0          # 300% ROI = 4x return


THRESHOLDS = ThresholdSSOT()


# ============================================================================
# UNIT SSOT - Measurement Units (可視化.pdf p.4)
# ============================================================================

class Unit(str, Enum):
    """Measurement unit SSOT"""
    USD = "USD"
    PERCENT = "%"
    RATIO = "ratio"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    COUNT = "count"
    RATE = "rate"
    PROBABILITY = "probability"


@dataclass(frozen=True)
class CurrencyFormat:
    """Currency formatting SSOT"""
    symbol: str = "$"
    decimals: int = 2
    thousands_sep: str = ","

    def format(self, value: float) -> str:
        """Format value as currency"""
        if value >= 1_000_000:
            return f"{self.symbol}{value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{self.symbol}{value/1_000:.1f}K"
        else:
            return f"{self.symbol}{value:,.{self.decimals}f}"


CURRENCY = CurrencyFormat(
    symbol=os.getenv("CURRENCY_SYMBOL", "$"),
    decimals=int(os.getenv("DECIMAL_PLACES", "2"))
)


# ============================================================================
# CHART METADATA - Title, Period, Sample Size (可視化.pdf p.5)
# ============================================================================

@dataclass
class ChartMetadata:
    """
    Chart metadata for standardized titles

    Title format: "{title} ({unit}, {period}, n={sample_size})"
    Example: "ROI by Channel (USD, 2024-Q1, n=1,234)"
    """
    title: str
    unit: Unit
    period: str
    sample_size: int
    subtitle: Optional[str] = None

    def format_title(self) -> str:
        """Format complete chart title with metadata"""
        base = f"{self.title} ({self.unit.value}, {self.period}, n={self.sample_size:,})"
        if self.subtitle:
            return f"{base}\n{self.subtitle}"
        return base


# ============================================================================
# CONFIDENCE INTERVAL - CI Band Configuration (可視化.pdf p.6)
# ============================================================================

@dataclass
class CIConfig:
    """
    Confidence interval visualization configuration

    Methods:
    - Error bars for discrete data (bar charts)
    - Ribbons/bands for continuous data (line charts)
    """
    level: float = 0.95           # 95% CI
    method: str = "bootstrap"     # bootstrap, percentile, normal
    n_bootstrap: int = 1000       # Bootstrap iterations

    # Visual styling
    error_bar_color: str = "#1F2937"     # Dark gray
    error_bar_width: float = 2.0
    ribbon_opacity: float = 0.2
    ribbon_color: str = "#60A5FA"        # Light blue


CI_CONFIG = CIConfig()


# ============================================================================
# CHART TYPE MAPPING - 3D → 2D Conversion (可視化.pdf p.1-2)
# ============================================================================

class ChartType(str, Enum):
    """Chart types following specification"""

    # 2D Primary (3D → 2D conversion)
    CONTOUR_2D = "contour_2d"           # ROI Surface: 3D → 2D contour + heatmap
    HEATMAP = "heatmap"                 # Budget allocation grid
    LINE_CI = "line_ci"                 # Time series with CI ribbons
    BAR_CI = "bar_ci"                   # Bar chart with error bars
    SCATTER_2D = "scatter_2d"           # Pareto frontier (2D scatter)
    WATERFALL = "waterfall"             # Budget delta waterfall
    SANKEY = "sankey"                   # Customer journey flow
    RADAR = "radar"                     # Shapley values (optional, bar preferred)
    HISTOGRAM_KDE = "histogram_kde"     # LTV distribution with KDE overlay
    SURVIVAL_CURVE = "survival_curve"   # Kaplan-Meier with CI bands

    # Advanced (only when spec allows)
    ANIMATION_2D = "animation_2d"       # Optimization process animation
    TABLE_SPARKLINE = "table_sparkline" # Recommendations with mini-charts


# ============================================================================
# DOWNLOAD CONFIGURATION (可視化.pdf p.8)
# ============================================================================

@dataclass
class DownloadConfig:
    """Chart download configuration"""
    enable_png: bool = True
    enable_csv: bool = True
    png_width: int = 1200
    png_height: int = 800
    png_dpi: int = 150
    csv_decimal: str = "."
    csv_separator: str = ","


DOWNLOAD_CONFIG = DownloadConfig()


# ============================================================================
# ERROR DISPLAY CONFIGURATION (可視化.pdf p.9)
# ============================================================================

@dataclass
class ErrorDisplay:
    """Error display configuration for failed visualizations"""
    show_execution_id: bool = True
    show_failed_step: bool = True
    show_retry_button: bool = True
    show_fallback_message: bool = True

    def format_error_message(
        self,
        execution_id: str,
        failed_step: str,
        error_message: str
    ) -> Dict[str, Any]:
        """Format error information for display"""
        return {
            "type": "visualization_error",
            "execution_id": execution_id,
            "failed_step": failed_step,
            "message": error_message,
            "actions": [
                {"label": "Retry", "action": "retry"},
                {"label": "View Logs", "action": f"logs/{execution_id}"},
                {"label": "Report Issue", "action": "report"}
            ]
        }


ERROR_DISPLAY = ErrorDisplay()


# ============================================================================
# CHART LIBRARY - 18 Marketing Charts Specification (可視化.pdf p.10-21)
# ============================================================================

@dataclass
class MarketingChartSpec:
    """Specification for one of the 18 marketing charts"""
    chart_id: str
    name: str
    chart_type: ChartType
    unit: Unit
    requires_ci: bool
    thresholds: Optional[List[Tuple[str, float]]] = None
    description: str = ""


# 18 Marketing Charts (可視化.pdf complete list)
MARKETING_CHARTS = [
    MarketingChartSpec(
        chart_id="roi_surface",
        name="ROI Surface (2D Contour)",
        chart_type=ChartType.CONTOUR_2D,
        unit=Unit.USD,
        requires_ci=False,
        description="2D contour + heatmap replacing 3D surface. Shows optimal allocation point."
    ),
    MarketingChartSpec(
        chart_id="budget_contour",
        name="Budget Allocation Contour",
        chart_type=ChartType.CONTOUR_2D,
        unit=Unit.USD,
        requires_ci=False,
        description="2D contour with gradient vectors showing optimization direction."
    ),
    MarketingChartSpec(
        chart_id="saturation_curves",
        name="Saturation Curves",
        chart_type=ChartType.LINE_CI,
        unit=Unit.RATIO,
        requires_ci=True,
        description="2D line chart per channel with 95% CI ribbons."
    ),
    MarketingChartSpec(
        chart_id="budget_waterfall",
        name="Budget Waterfall",
        chart_type=ChartType.WATERFALL,
        unit=Unit.USD,
        requires_ci=False,
        description="2D waterfall showing budget deltas across channels."
    ),
    MarketingChartSpec(
        chart_id="marginal_roi",
        name="Marginal ROI",
        chart_type=ChartType.BAR_CI,
        unit=Unit.RATIO,
        requires_ci=True,
        description="2D bar chart with error bars per channel."
    ),
    MarketingChartSpec(
        chart_id="pareto_frontier",
        name="Pareto Frontier",
        chart_type=ChartType.SCATTER_2D,
        unit=Unit.RATIO,
        requires_ci=False,
        description="2D scatter plot with frontier line (not surface)."
    ),
    MarketingChartSpec(
        chart_id="journey_sankey",
        name="Customer Journey Sankey",
        chart_type=ChartType.SANKEY,
        unit=Unit.COUNT,
        requires_ci=False,
        description="2D flow diagram with flow conservation check."
    ),
    MarketingChartSpec(
        chart_id="shapley_attribution",
        name="Shapley Attribution",
        chart_type=ChartType.BAR_CI,  # Bar chart preferred over radar
        unit=Unit.PERCENT,
        requires_ci=True,
        thresholds=[("sum_constraint", 1.0)],
        description="Bar chart (radar optional). Must sum to 100% with assertion."
    ),
    MarketingChartSpec(
        chart_id="ltv_distribution",
        name="LTV Distribution",
        chart_type=ChartType.HISTOGRAM_KDE,
        unit=Unit.USD,
        requires_ci=True,
        description="2D histogram + KDE overlay with percentile markers."
    ),
    MarketingChartSpec(
        chart_id="survival_curve",
        name="Survival Curve (Kaplan-Meier)",
        chart_type=ChartType.SURVIVAL_CURVE,
        unit=Unit.PROBABILITY,
        requires_ci=True,
        description="2D KM curve with 95% CI bands. Must be monotone decreasing."
    ),
    MarketingChartSpec(
        chart_id="ltv_confidence",
        name="LTV Confidence Intervals",
        chart_type=ChartType.BAR_CI,
        unit=Unit.USD,
        requires_ci=True,
        description="2D bar chart with error bars per segment."
    ),
    MarketingChartSpec(
        chart_id="adstock_timeseries",
        name="Adstock Time Series",
        chart_type=ChartType.LINE_CI,
        unit=Unit.RATIO,
        requires_ci=True,
        description="2D dual-axis line chart with CI ribbons."
    ),
    MarketingChartSpec(
        chart_id="scenario_heatmap",
        name="Scenario Comparison Heatmap",
        chart_type=ChartType.HEATMAP,
        unit=Unit.RATIO,
        requires_ci=False,
        description="2D heatmap with ratio annotations in cells."
    ),
    MarketingChartSpec(
        chart_id="optimal_mix",
        name="Optimal Channel Mix",
        chart_type=ChartType.BAR_CI,  # Stacked bar, not donut
        unit=Unit.PERCENT,
        requires_ci=False,
        description="Stacked bar chart (not donut pie). Shows allocation %."
    ),
    MarketingChartSpec(
        chart_id="kpi_dashboard",
        name="KPI Dashboard",
        chart_type=ChartType.LINE_CI,
        unit=Unit.RATIO,
        requires_ci=True,
        description="2D small multiples (4x grid) with CI ribbons."
    ),
    MarketingChartSpec(
        chart_id="alert_timeline",
        name="Alert Timeline",
        chart_type=ChartType.SCATTER_2D,
        unit=Unit.COUNT,
        requires_ci=False,
        description="2D scatter on time axis with severity colors."
    ),
    MarketingChartSpec(
        chart_id="ai_recommendations",
        name="AI Recommendations",
        chart_type=ChartType.TABLE_SPARKLINE,
        unit=Unit.USD,
        requires_ci=False,
        description="Table with embedded sparklines per recommendation."
    ),
    MarketingChartSpec(
        chart_id="optimization_animation",
        name="Optimization Process Animation",
        chart_type=ChartType.ANIMATION_2D,
        unit=Unit.RATIO,
        requires_ci=False,
        description="2D animation showing convergence (limited use only)."
    ),
]


def get_chart_spec(chart_id: str) -> Optional[MarketingChartSpec]:
    """Get chart specification by ID"""
    for spec in MARKETING_CHARTS:
        if spec.chart_id == chart_id:
            return spec
    return None


# ============================================================================
# PLOTLY LAYOUT HELPERS - Standardized Configuration
# ============================================================================

def get_plotly_layout_config(
    meta: ChartMetadata,
    height: int = 600,
    show_legend: bool = True,
) -> Dict[str, Any]:
    """
    Get standardized Plotly layout configuration

    Enforces:
    - Title format with unit/period/sample size
    - Font sizes and families
    - Margins and padding
    - Grid and axis styling
    """
    return {
        "title": {
            "text": meta.format_title(),
            "font": {"size": 18, "family": "Inter, sans-serif", "color": "#1F2937"},
            "x": 0.5,
            "xanchor": "center",
        },
        "height": height,
        "font": {"family": "Inter, sans-serif", "size": 12, "color": "#374151"},
        "showlegend": show_legend,
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.2,
            "xanchor": "center",
            "x": 0.5,
        },
        "margin": {"l": 80, "r": 40, "t": 100, "b": 80},
        "plot_bgcolor": "#FFFFFF",
        "paper_bgcolor": "#FFFFFF",
        "xaxis": {
            "showgrid": True,
            "gridcolor": "#E5E7EB",
            "linecolor": "#9CA3AF",
            "linewidth": 1,
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": "#E5E7EB",
            "linecolor": "#9CA3AF",
            "linewidth": 1,
        },
    }


def get_plotly_config() -> Dict[str, Any]:
    """
    Get Plotly config for downloads and interactions

    Enables:
    - PNG download button
    - Zoom, pan, reset
    - Disables Plotly logo
    """
    return {
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToAdd": ["downloadSvg"],
        "toImageButtonOptions": {
            "format": "png",
            "filename": "cqox_chart",
            "height": DOWNLOAD_CONFIG.png_height,
            "width": DOWNLOAD_CONFIG.png_width,
            "scale": DOWNLOAD_CONFIG.png_dpi / 96,  # Convert DPI to scale
        },
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    }


# ============================================================================
# ANNOTATION HELPERS - Optimal Points, Thresholds (可視化.pdf p.12)
# ============================================================================

def create_threshold_line(
    threshold_value: float,
    threshold_name: str,
    axis: str = "x",  # "x" or "y"
    color: str = "#DC2626",  # Red
    dash: str = "dash",
) -> Dict[str, Any]:
    """
    Create Plotly shape for threshold line

    Used for:
    - SMD threshold (0.1)
    - IV F-statistic threshold (10)
    - ROI break-even (0.0)
    """
    if axis == "y":
        return {
            "type": "line",
            "xref": "paper",
            "yref": "y",
            "x0": 0,
            "x1": 1,
            "y0": threshold_value,
            "y1": threshold_value,
            "line": {"color": color, "width": 2, "dash": dash},
        }
    else:  # x axis
        return {
            "type": "line",
            "xref": "x",
            "yref": "paper",
            "x0": threshold_value,
            "x1": threshold_value,
            "y0": 0,
            "y1": 1,
            "line": {"color": color, "width": 2, "dash": dash},
        }


def create_optimal_point_annotation(
    x: float,
    y: float,
    text: str = "Optimal",
    color: str = "#10B981",  # Green
) -> Dict[str, Any]:
    """
    Create annotation for optimal point on chart

    Used for:
    - Optimal budget allocation on ROI surface
    - Pareto optimal points
    """
    return {
        "x": x,
        "y": y,
        "text": f"★ {text}",
        "showarrow": True,
        "arrowhead": 2,
        "arrowsize": 1,
        "arrowwidth": 2,
        "arrowcolor": color,
        "ax": 30,
        "ay": -40,
        "font": {"size": 14, "color": color, "family": "Inter, sans-serif"},
        "bgcolor": "rgba(255, 255, 255, 0.9)",
        "bordercolor": color,
        "borderwidth": 2,
        "borderpad": 4,
    }
