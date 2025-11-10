"""
Multi-Domain Analysis
Supports analyzing datasets that span multiple domains simultaneously
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from backend.inference.domain_detector import DomainDetector
from backend.engine.figure_selector import FigureSelector

logger = logging.getLogger(__name__)


class MultiDomainAnalyzer:
    """
    Analyze datasets with multiple domain characteristics

    Example: Healthcare + Finance (medical treatments + insurance costs)
    """

    def __init__(self, df: pd.DataFrame, mapping: Dict[str, str],
                 min_domain_confidence: float = 0.25):
        """
        Initialize multi-domain analyzer

        Args:
            df: Input dataframe
            mapping: Column role mapping
            min_domain_confidence: Minimum confidence to include domain (default: 0.25)
        """
        self.df = df
        self.mapping = mapping
        self.min_confidence = min_domain_confidence

        # Detect all relevant domains
        self.detector = DomainDetector()
        self.domain_scores = self.detector.detect_domain(df, mapping)

        # Filter domains above threshold
        self.active_domains = [
            domain for domain, score in self.domain_scores.items()
            if score >= min_domain_confidence
        ]

        logger.info(f"[MultiDomainAnalyzer] Active domains: {self.active_domains}")
        logger.info(f"[MultiDomainAnalyzer] Domain scores: {self.domain_scores}")

    def analyze_all_domains(self) -> Dict[str, Any]:
        """
        Analyze data from all active domains

        Returns:
            {
                "primary_domain": "medical",
                "active_domains": ["medical", "finance"],
                "domain_confidence": {...},
                "domain_figures": {
                    "medical": {
                        "confidence": 0.65,
                        "recommended_figures": [...],
                        "figure_details": {...}
                    },
                    "finance": {...}
                },
                "total_figures": 12
            }
        """
        result = {
            "primary_domain": self._get_primary_domain(),
            "active_domains": self.active_domains,
            "domain_confidence": self.domain_scores,
            "domain_figures": {},
            "total_figures": 0
        }

        # Analyze each active domain
        for domain in self.active_domains:
            domain_result = self._analyze_domain(domain)
            result["domain_figures"][domain] = domain_result
            result["total_figures"] += len(domain_result["recommended_figures"])

        logger.info(f"[MultiDomainAnalyzer] Total figures across {len(self.active_domains)} domains: {result['total_figures']}")

        return result

    def _get_primary_domain(self) -> str:
        """Get domain with highest confidence"""
        if not self.domain_scores:
            return "generic"
        return max(self.domain_scores.items(), key=lambda x: x[1])[0]

    def _analyze_domain(self, domain: str) -> Dict[str, Any]:
        """
        Analyze a single domain

        Returns:
            {
                "confidence": 0.65,
                "recommended_figures": ["medical_km_survival", ...],
                "figure_details": {...},
                "skipped_figures": [...]
            }
        """
        try:
            selector = FigureSelector(self.df, self.mapping, domain)
            report = selector.get_selection_report()

            return {
                "confidence": self.domain_scores.get(domain, 0.0),
                "recommended_figures": report["recommended_figures"],
                "figure_details": report["details"],
                "skipped_figures": report["skipped_figures"],
                "total_available": report["total_figures"],
                "total_recommended": report["recommended"]
            }
        except Exception as e:
            logger.error(f"[MultiDomainAnalyzer] Failed to analyze domain {domain}: {e}")
            return {
                "confidence": self.domain_scores.get(domain, 0.0),
                "recommended_figures": [],
                "figure_details": {},
                "skipped_figures": [],
                "error": str(e)
            }

    def get_figure_generation_plan(self) -> Dict[str, List[str]]:
        """
        Get organized plan for figure generation

        Returns:
            {
                "high_priority": ["medical_km_survival", "finance_pnl"],
                "medium_priority": [...],
                "low_priority": [...]
            }
        """
        all_results = self.analyze_all_domains()

        high_priority = []
        medium_priority = []
        low_priority = []

        for domain, domain_data in all_results["domain_figures"].items():
            confidence = domain_data["confidence"]
            figures = domain_data["recommended_figures"]

            if confidence >= 0.5:
                high_priority.extend(figures)
            elif confidence >= 0.35:
                medium_priority.extend(figures)
            else:
                low_priority.extend(figures)

        return {
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
            "total": len(high_priority) + len(medium_priority) + len(low_priority)
        }

    def generate_multi_domain_report(self) -> str:
        """
        Generate human-readable multi-domain analysis report

        Returns:
            Formatted string report
        """
        analysis = self.analyze_all_domains()

        lines = [
            "=" * 60,
            "MULTI-DOMAIN ANALYSIS REPORT",
            "=" * 60,
            "",
            f"Primary Domain: {analysis['primary_domain'].upper()}",
            f"Active Domains: {len(analysis['active_domains'])}",
            ""
        ]

        # Domain confidence breakdown
        lines.append("Domain Confidence Scores:")
        lines.append("-" * 40)
        for domain, score in sorted(analysis['domain_confidence'].items(),
                                    key=lambda x: x[1], reverse=True):
            if score >= self.min_confidence:
                bar = "█" * int(score * 20)
                lines.append(f"  {domain:15} {score:.2f} {bar}")
        lines.append("")

        # Figure summary per domain
        lines.append("Recommended Figures by Domain:")
        lines.append("-" * 40)
        for domain in analysis['active_domains']:
            domain_data = analysis['domain_figures'][domain]
            lines.append(f"\n{domain.upper()} (confidence: {domain_data['confidence']:.2f}):")
            lines.append(f"  Recommended: {domain_data['total_recommended']}/{domain_data['total_available']} figures")

            if domain_data['recommended_figures']:
                for fig in domain_data['recommended_figures'][:5]:  # Show top 5
                    fig_detail = domain_data['figure_details'].get(fig, {})
                    conf = fig_detail.get('confidence', 1.0)
                    lines.append(f"    ✓ {fig} (confidence: {conf:.2f})")

                if len(domain_data['recommended_figures']) > 5:
                    lines.append(f"    ... and {len(domain_data['recommended_figures']) - 5} more")

        lines.append("")
        lines.append(f"Total Figures to Generate: {analysis['total_figures']}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def get_cross_domain_insights(self) -> Dict[str, Any]:
        """
        Identify potential cross-domain insights

        Returns:
            {
                "domain_overlap_analysis": {...},
                "suggested_comparisons": [...],
                "unique_value_propositions": [...]
            }
        """
        insights = {
            "domain_overlap_analysis": {},
            "suggested_comparisons": [],
            "unique_value_propositions": []
        }

        # Check for specific multi-domain combinations
        active_set = set(self.active_domains)

        # Medical + Finance = Healthcare Economics
        if {"medical", "finance"}.issubset(active_set):
            insights["suggested_comparisons"].append({
                "name": "Healthcare Economics Analysis",
                "domains": ["medical", "finance"],
                "description": "Compare treatment effectiveness with cost-effectiveness",
                "recommended_metrics": ["QALY", "Cost per outcome", "ROI of intervention"]
            })
            insights["unique_value_propositions"].append(
                "Combine clinical outcomes (medical) with financial impact (finance) for comprehensive healthcare ROI analysis"
            )

        # Retail + Network = Social Commerce
        if {"retail", "network"}.issubset(active_set):
            insights["suggested_comparisons"].append({
                "name": "Social Commerce Analysis",
                "domains": ["retail", "network"],
                "description": "Analyze how social network influences purchasing",
                "recommended_metrics": ["Network spillover effect", "Viral coefficient", "Peer influence on sales"]
            })
            insights["unique_value_propositions"].append(
                "Leverage network effects (network) to optimize marketing campaigns (retail)"
            )

        # Education + Policy = Education Policy Impact
        if {"education", "policy"}.issubset(active_set):
            insights["suggested_comparisons"].append({
                "name": "Education Policy Impact",
                "domains": ["education", "policy"],
                "description": "Evaluate policy interventions on educational outcomes",
                "recommended_metrics": ["Regional achievement gaps", "Policy effectiveness", "Geographic disparity"]
            })

        # Manufacturing + Energy = Sustainable Manufacturing
        if {"manufacturing", "energy"}.issubset(active_set):
            insights["suggested_comparisons"].append({
                "name": "Sustainable Manufacturing",
                "domains": ["manufacturing", "energy"],
                "description": "Optimize production while minimizing energy consumption",
                "recommended_metrics": ["Energy efficiency", "Carbon footprint per unit", "Green manufacturing ROI"]
            })

        return insights


# Convenience functions

def analyze_multi_domain(df: pd.DataFrame,
                         mapping: Dict[str, str],
                         min_confidence: float = 0.25) -> Dict[str, Any]:
    """
    Convenience function for multi-domain analysis

    Args:
        df: Input dataframe
        mapping: Column role mapping
        min_confidence: Minimum domain confidence

    Returns:
        Multi-domain analysis results
    """
    analyzer = MultiDomainAnalyzer(df, mapping, min_confidence)
    return analyzer.analyze_all_domains()


def get_multi_domain_report(df: pd.DataFrame,
                             mapping: Dict[str, str]) -> str:
    """
    Generate multi-domain report

    Returns:
        Formatted string report
    """
    analyzer = MultiDomainAnalyzer(df, mapping)
    return analyzer.generate_multi_domain_report()


# Example usage
if __name__ == "__main__":
    # Test with healthcare+finance data
    df = pd.DataFrame({
        "patient_id": range(100),
        "drug": np.random.choice(["DrugA", "Placebo"], 100),
        "outcome_days": np.random.randint(50, 500, 100),
        "treatment_cost": np.random.randint(1000, 50000, 100),
        "insurance_claim": np.random.randint(5000, 100000, 100),
        "hospital_id": np.random.choice(["H1", "H2", "H3"], 100)
    })

    mapping = {
        "y": "outcome_days",
        "treatment": "drug",
        "unit_id": "patient_id"
    }

    analyzer = MultiDomainAnalyzer(df, mapping)

    print(analyzer.generate_multi_domain_report())
    print("\n")

    insights = analyzer.get_cross_domain_insights()
    print("Cross-Domain Insights:")
    for vp in insights["unique_value_propositions"]:
        print(f"  • {vp}")
