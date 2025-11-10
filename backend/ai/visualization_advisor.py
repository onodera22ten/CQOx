"""
AI-Powered Visualization Advisor
Uses LLM to recommend optimal visualizations based on data characteristics
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import json
import logging
import os

logger = logging.getLogger(__name__)


class AIVisualizationAdvisor:
    """
    LLM-based visualization recommendation system

    Analyzes data and suggests optimal visualizations based on:
    - Domain
    - Analysis goal
    - Data characteristics
    - Available figures
    """

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize advisor

        Args:
            model: LLM model to use for recommendations
        """
        self.model = model
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def recommend_visualizations(self,
                                  df: pd.DataFrame,
                                  mapping: Dict[str, str],
                                  domain: str,
                                  analysis_goal: str = "comprehensive_analysis") -> List[Dict[str, Any]]:
        """
        Get AI-powered visualization recommendations

        Args:
            df: Input dataframe
            mapping: Column role mapping
            domain: Detected domain
            analysis_goal: Analysis objective
                - "exploratory": Exploratory data analysis
                - "causal_validation": Validate causal effect
                - "presentation": Create presentation materials
                - "comprehensive_analysis": Full analysis

        Returns:
            List of recommended visualizations with reasoning
            [
                {
                    "figure_name": "medical_km_survival",
                    "priority": "high",
                    "reasoning": "...",
                    "estimated_insight": "...",
                    "required_preprocessing": [...]
                },
                ...
            ]
        """
        try:
            # Prepare data summary for LLM
            summary = self._create_data_summary(df, mapping, domain)

            # Get available figures for this domain
            available_figures = self._get_available_figures(domain)

            # Create prompt
            prompt = self._build_recommendation_prompt(summary, available_figures, analysis_goal)

            # Call LLM
            recommendations = self._call_llm(prompt)

            logger.info(f"[AIVisualizationAdvisor] Generated {len(recommendations)} recommendations for {domain} domain")

            return recommendations

        except Exception as e:
            logger.error(f"[AIVisualizationAdvisor] Recommendation failed: {e}")
            return self._fallback_recommendations(domain)

    def _create_data_summary(self, df: pd.DataFrame, mapping: Dict[str, str], domain: str) -> Dict[str, Any]:
        """Create comprehensive data summary for LLM"""
        summary = {
            "domain": domain,
            "n_rows": len(df),
            "n_cols": len(df.columns),
            "columns": {},
            "mapping": mapping,
            "data_quality": {}
        }

        # Column details
        for col in df.columns:
            col_info = {
                "dtype": str(df[col].dtype),
                "n_unique": int(df[col].nunique()),
                "missing_pct": float(df[col].isnull().mean() * 100),
                "sample_values": df[col].dropna().head(3).tolist() if len(df[col].dropna()) > 0 else []
            }

            # Add statistics for numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info.update({
                    "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                    "std": float(df[col].std()) if not df[col].isnull().all() else None,
                    "min": float(df[col].min()) if not df[col].isnull().all() else None,
                    "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    "skewness": float(df[col].skew()) if not df[col].isnull().all() else None
                })

            summary["columns"][col] = col_info

        # Data quality assessment
        summary["data_quality"] = {
            "overall_missing_pct": float(df.isnull().mean().mean() * 100),
            "complete_cases": int(df.dropna().shape[0]),
            "duplicate_rows": int(df.duplicated().sum())
        }

        # Correlations (for numeric columns)
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] >= 2:
            try:
                corr_matrix = numeric_df.corr()
                # Get top correlations
                high_corr = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.5:
                            high_corr.append({
                                "col1": corr_matrix.columns[i],
                                "col2": corr_matrix.columns[j],
                                "correlation": float(corr_val)
                            })
                summary["high_correlations"] = high_corr[:10]  # Top 10
            except:
                summary["high_correlations"] = []

        return summary

    def _get_available_figures(self, domain: str) -> Dict[str, str]:
        """Get available figure definitions for domain"""
        from backend.engine.figure_selector import FigureSelector

        # Get figure requirements from FigureSelector
        all_figures = FigureSelector.FIGURE_REQUIREMENTS

        # Filter by domain
        domain_figures = {
            name: req["description"]
            for name, req in all_figures.items()
            if name.startswith(f"{domain}_")
        }

        return domain_figures

    def _build_recommendation_prompt(self, summary: Dict[str, Any],
                                     available_figures: Dict[str, str],
                                     analysis_goal: str) -> str:
        """Build LLM prompt for recommendations"""
        goal_descriptions = {
            "exploratory": "Exploratory data analysis - understand patterns, distributions, and relationships",
            "causal_validation": "Validate causal effect - confirm treatment impact, check assumptions",
            "presentation": "Create presentation materials - clear, impactful visualizations for stakeholders",
            "comprehensive_analysis": "Comprehensive analysis - full diagnostic and inferential analysis"
        }

        goal_desc = goal_descriptions.get(analysis_goal, analysis_goal)

        prompt = f"""You are an expert in causal inference and data visualization. Analyze the following dataset and recommend the most appropriate visualizations.

**Analysis Goal**: {goal_desc}

**Domain**: {summary['domain']}

**Dataset Summary**:
- Rows: {summary['n_rows']}
- Columns: {summary['n_cols']}
- Missing data: {summary['data_quality']['overall_missing_pct']:.1f}%

**Column Mapping**:
{json.dumps(summary['mapping'], indent=2)}

**Column Details** (key columns only):
{self._format_column_details(summary['columns'], summary['mapping'])}

**Available Visualizations for {summary['domain']} domain**:
{self._format_available_figures(available_figures)}

**Task**: Recommend the top 5 visualizations that would provide the most valuable insights for this analysis goal.

For each recommendation, provide:
1. **figure_name**: Exact name from available visualizations
2. **priority**: "high", "medium", or "low"
3. **reasoning**: Why this visualization is valuable (2-3 sentences)
4. **estimated_insight**: What specific insight this will reveal (1 sentence)
5. **required_preprocessing**: List of any data preparation steps needed (or empty list if none)

**Output Format** (JSON array):
```json
[
  {{
    "figure_name": "medical_km_survival",
    "priority": "high",
    "reasoning": "The dataset contains survival time data (outcome_days) with treatment groups. KM curves are essential for visualizing time-to-event data and comparing survival rates between treated and control groups.",
    "estimated_insight": "Treatment group shows 20% higher survival rate at 1-year mark",
    "required_preprocessing": ["Handle censored observations", "Check proportional hazards assumption"]
  }},
  ...
]
```

Prioritize visualizations that:
- Match the analysis goal
- Leverage available data columns
- Address data quality issues
- Provide actionable insights

Respond with ONLY the JSON array, no additional text.
"""

        return prompt

    def _format_column_details(self, columns: Dict, mapping: Dict) -> str:
        """Format key column details for prompt"""
        lines = []

        # Mapped columns first
        for role, col in mapping.items():
            if col and col in columns:
                col_info = columns[col]
                lines.append(f"- **{col}** ({role}): {col_info['dtype']}, {col_info['n_unique']} unique, {col_info['missing_pct']:.1f}% missing")

        # Other interesting columns (high cardinality, numeric, etc.)
        other_cols = [c for c in columns if c not in mapping.values()]
        for col in other_cols[:5]:  # Top 5
            col_info = columns[col]
            lines.append(f"- {col}: {col_info['dtype']}, {col_info['n_unique']} unique")

        return "\n".join(lines)

    def _format_available_figures(self, available_figures: Dict[str, str]) -> str:
        """Format available figures list"""
        lines = []
        for fig_name, description in available_figures.items():
            lines.append(f"- **{fig_name}**: {description}")
        return "\n".join(lines)

    def _call_llm(self, prompt: str) -> List[Dict[str, Any]]:
        """Call LLM API for recommendations"""
        try:
            # Try Anthropic Claude API
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            response = client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = response.content[0].text

            # Extract JSON from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            json_str = response_text[json_start:json_end]

            recommendations = json.loads(json_str)

            return recommendations

        except ImportError:
            logger.warning("[AIVisualizationAdvisor] anthropic package not installed, using fallback")
            return self._fallback_recommendations("")

        except Exception as e:
            logger.error(f"[AIVisualizationAdvisor] LLM call failed: {e}")
            return self._fallback_recommendations("")

    def _fallback_recommendations(self, domain: str) -> List[Dict[str, Any]]:
        """Fallback recommendations if LLM unavailable"""
        fallback_by_domain = {
            "medical": [
                {
                    "figure_name": "medical_km_survival",
                    "priority": "high",
                    "reasoning": "Standard visualization for survival analysis in medical studies",
                    "estimated_insight": "Compare survival curves between treatment groups",
                    "required_preprocessing": []
                },
                {
                    "figure_name": "medical_sensitivity",
                    "priority": "high",
                    "reasoning": "Essential for robustness checking in observational studies",
                    "estimated_insight": "Assess sensitivity to unmeasured confounding",
                    "required_preprocessing": []
                }
            ],
            "education": [
                {
                    "figure_name": "education_gain_distrib",
                    "priority": "high",
                    "reasoning": "Shows distribution of learning gains across students",
                    "estimated_insight": "Identify high and low performers",
                    "required_preprocessing": []
                }
            ],
            "retail": [
                {
                    "figure_name": "retail_uplift_curve",
                    "priority": "high",
                    "reasoning": "Critical for targeting and ROI optimization",
                    "estimated_insight": "Identify high-uplift customer segments",
                    "required_preprocessing": []
                }
            ]
        }

        return fallback_by_domain.get(domain, [
            {
                "figure_name": "generic_distribution",
                "priority": "medium",
                "reasoning": "Basic distribution analysis",
                "estimated_insight": "Understand data patterns",
                "required_preprocessing": []
            }
        ])

    def explain_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """Generate human-readable explanation of recommendations"""
        if not recommendations:
            return "No recommendations available"

        lines = [
            "=== AI Visualization Recommendations ===\n",
            f"Total Recommendations: {len(recommendations)}\n"
        ]

        for i, rec in enumerate(recommendations, 1):
            priority_symbol = {
                "high": "🔥",
                "medium": "⚡",
                "low": "💡"
            }.get(rec["priority"], "•")

            lines.append(f"\n{i}. {priority_symbol} {rec['figure_name'].upper()} (Priority: {rec['priority']})")
            lines.append(f"   Reasoning: {rec['reasoning']}")
            lines.append(f"   Expected Insight: {rec['estimated_insight']}")

            if rec.get("required_preprocessing"):
                lines.append(f"   Preprocessing: {', '.join(rec['required_preprocessing'])}")

        return "\n".join(lines)


# Convenience functions

def get_ai_recommendations(df: pd.DataFrame,
                            mapping: Dict[str, str],
                            domain: str,
                            analysis_goal: str = "comprehensive_analysis") -> List[Dict[str, Any]]:
    """
    Get AI-powered visualization recommendations

    Args:
        df: Input dataframe
        mapping: Column mapping
        domain: Domain name
        analysis_goal: Analysis objective

    Returns:
        List of recommendations
    """
    advisor = AIVisualizationAdvisor()
    return advisor.recommend_visualizations(df, mapping, domain, analysis_goal)
