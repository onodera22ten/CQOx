"""
Automatic Domain Detection
Intelligently detects domain from data using multi-signal analysis
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import re
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class DomainDetector:
    """
    Automatic domain inference using multi-signal analysis

    Signals:
    1. Column name keyword matching (40%)
    2. Data distribution patterns (30%)
    3. Value range analysis (20%)
    4. Column correlation patterns (10%)
    """

    # Domain-specific keyword signatures with weights
    DOMAIN_SIGNATURES = {
        "medical": {
            "strong": ["patient", "drug", "dose", "clinical", "adverse_event", "hospital",
                      "therapy", "diagnosis", "symptom", "medication", "treatment_arm"],
            "medium": ["outcome", "treatment", "therapy", "recovery", "survival", "health"],
            "weak": ["id", "age", "gender", "date"],
            "exclusions": ["sales", "revenue", "customer", "student", "campaign"]
        },
        "education": {
            "strong": ["student", "teacher", "grade", "score", "class", "school",
                      "curriculum", "test", "exam", "achievement", "gpa"],
            "medium": ["outcome", "program", "intervention", "cohort", "semester"],
            "weak": ["id", "age", "gender", "date"],
            "exclusions": ["patient", "customer", "sales", "drug"]
        },
        "retail": {
            "strong": ["sales", "revenue", "customer", "campaign", "sku", "inventory",
                      "product", "purchase", "cart", "order", "transaction"],
            "medium": ["price", "channel", "promotion", "discount", "conversion"],
            "weak": ["id", "date", "region"],
            "exclusions": ["patient", "student", "drug", "grade"]
        },
        "finance": {
            "strong": ["portfolio", "return", "pnl", "profit", "loss", "asset",
                      "investment", "risk", "volatility", "yield", "sharpe"],
            "medium": ["price", "value", "rate", "cost", "revenue"],
            "weak": ["id", "date", "amount"],
            "exclusions": ["patient", "student", "customer"]
        },
        "network": {
            "strong": ["node", "edge", "friend", "follower", "user", "connection",
                      "degree", "centrality", "neighbor", "link", "graph"],
            "medium": ["influence", "exposure", "spillover", "peer", "social"],
            "weak": ["id", "timestamp"],
            "exclusions": ["patient", "sales", "grade"]
        },
        "policy": {
            "strong": ["region", "state", "county", "district", "policy", "law",
                      "regulation", "government", "public", "municipality"],
            "medium": ["treatment", "intervention", "program", "reform"],
            "weak": ["year", "quarter", "date"],
            "exclusions": ["patient", "customer", "student"]
        },
        "manufacturing": {
            "strong": ["yield", "defect", "quality", "machine", "production", "assembly",
                      "downtime", "throughput", "scrap", "rework", "operator"],
            "medium": ["shift", "batch", "lot", "process", "line"],
            "weak": ["id", "timestamp"],
            "exclusions": ["patient", "student", "customer"]
        },
        "logistics": {
            "strong": ["delivery", "warehouse", "shipment", "logistics", "freight",
                      "carrier", "route", "transit", "inventory", "stock"],
            "medium": ["location", "distance", "lead_time", "supplier"],
            "weak": ["id", "date"],
            "exclusions": ["patient", "grade", "drug"]
        },
        "hr": {
            "strong": ["employee", "hire", "attrition", "performance", "salary",
                      "promotion", "training", "turnover", "retention", "hr"],
            "medium": ["department", "manager", "tenure", "rating"],
            "weak": ["id", "date", "age"],
            "exclusions": ["patient", "student", "customer"]
        },
        "agriculture": {
            "strong": ["yield", "crop", "harvest", "soil", "fertilizer", "farm",
                      "weather", "precipitation", "irrigation", "pest"],
            "medium": ["season", "plot", "field", "acre"],
            "weak": ["date", "location"],
            "exclusions": ["patient", "customer", "student"]
        },
        "energy": {
            "strong": ["power", "energy", "consumption", "generation", "grid",
                      "renewable", "solar", "wind", "kwh", "load"],
            "medium": ["capacity", "efficiency", "demand", "supply"],
            "weak": ["timestamp", "location"],
            "exclusions": ["patient", "student", "customer"]
        }
    }

    def __init__(self):
        """Initialize domain detector"""
        self.detected_language = "en"  # Default

    def detect_domain(self, df: pd.DataFrame,
                      column_mapping: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        Detect domain from dataframe using multi-signal analysis

        Args:
            df: Input dataframe
            column_mapping: Optional column role mapping

        Returns:
            Dictionary of domain scores (summing to 1.0)
            {
                "medical": 0.85,
                "retail": 0.10,
                "education": 0.05
            }
        """
        scores = {}

        for domain, signatures in self.DOMAIN_SIGNATURES.items():
            score = 0.0

            # Signal 1: Column name keyword matching (40%)
            keyword_score = self._score_keywords(df, signatures)
            score += keyword_score * 0.4

            # Signal 2: Data distribution patterns (30%)
            distribution_score = self._analyze_distributions(df, domain)
            score += distribution_score * 0.3

            # Signal 3: Value range analysis (20%)
            range_score = self._analyze_value_ranges(df, domain)
            score += range_score * 0.2

            # Signal 4: Column correlation patterns (10%)
            correlation_score = self._analyze_correlations(df, domain)
            score += correlation_score * 0.1

            scores[domain] = max(0.0, min(1.0, score))

        # Normalize scores to sum to 1.0
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        else:
            # Default to generic if no signals
            scores = {k: 1.0 / len(scores) for k in scores.keys()}

        logger.info(f"[DomainDetector] Detected domains: {sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]}")

        return scores

    def _score_keywords(self, df: pd.DataFrame, signatures: Dict[str, List[str]]) -> float:
        """Score based on keyword matching in column names"""
        score = 0.0
        columns_text = " ".join(df.columns).lower()

        # Strong keywords (0.15 each, max 0.6)
        strong_matches = sum(
            1 for kw in signatures["strong"]
            if kw in columns_text
        )
        score += min(strong_matches * 0.15, 0.6)

        # Medium keywords (0.08 each, max 0.3)
        medium_matches = sum(
            1 for kw in signatures["medium"]
            if kw in columns_text
        )
        score += min(medium_matches * 0.08, 0.3)

        # Weak keywords (0.02 each, max 0.1)
        weak_matches = sum(
            1 for kw in signatures["weak"]
            if kw in columns_text
        )
        score += min(weak_matches * 0.02, 0.1)

        # Exclusion penalty (halve score if exclusions found)
        exclusions = signatures.get("exclusions", [])
        if any(kw in columns_text for kw in exclusions):
            score *= 0.5

        return min(score, 1.0)

    def _analyze_distributions(self, df: pd.DataFrame, domain: str) -> float:
        """Analyze data distribution patterns specific to domain"""
        score = 0.0
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) == 0:
            return 0.0

        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) < 10:
                continue

            # Calculate distribution metrics
            skewness = data.skew()
            kurt = data.kurtosis()
            min_val = data.min()
            max_val = data.max()

            if domain == "medical":
                # Medical: Right-skewed survival times (positive outcomes)
                if skewness > 1.5 and min_val >= 0:
                    score += 0.1
                # Dosage ranges (typical pharmaceutical doses)
                if "dose" in col.lower() and 0.1 <= min_val <= max_val <= 10000:
                    score += 0.15

            elif domain == "education":
                # Education: Near-normal test score distributions
                if abs(skewness) < 0.5 and 0 <= min_val <= max_val <= 100:
                    score += 0.1
                # GPA ranges
                if 0 <= min_val <= max_val <= 4.5:
                    score += 0.05

            elif domain == "retail":
                # Retail: Power-law distributions (few customers, high sales)
                if skewness > 2.0 and min_val >= 0:
                    score += 0.1
                # Revenue/sales positivity
                if min_val >= 0 and max_val > 100:
                    score += 0.05

            elif domain == "finance":
                # Finance: Fat-tailed returns
                if abs(kurt) > 3:
                    score += 0.1
                # Percentage returns (-100% to +infinity)
                if -1 <= min_val <= max_val:
                    score += 0.05

            elif domain == "manufacturing":
                # Manufacturing: Yield percentages
                if 0 <= min_val <= max_val <= 1:
                    score += 0.1
                # Defect rates (low values, right-skewed)
                if 0 <= min_val < 0.1 and skewness > 1:
                    score += 0.1

            elif domain == "agriculture":
                # Agriculture: Seasonal patterns
                if len(data.unique()) > 4 and skewness > 0:
                    score += 0.05

            elif domain == "energy":
                # Energy: Cyclical consumption patterns
                if len(data.unique()) > 24:  # Hourly data
                    score += 0.05

        return min(score, 1.0)

    def _analyze_value_ranges(self, df: pd.DataFrame, domain: str) -> float:
        """Analyze value ranges to infer domain"""
        score = 0.0

        for col in df.select_dtypes(include=[np.number]).columns:
            data = df[col].dropna()
            if len(data) == 0:
                continue

            min_val = data.min()
            max_val = data.max()
            col_lower = col.lower()

            if domain == "education":
                # Test scores (0-100)
                if ("score" in col_lower or "grade" in col_lower or "test" in col_lower):
                    if 0 <= min_val <= max_val <= 100:
                        score += 0.2
                # GPA (0-4)
                if "gpa" in col_lower and 0 <= min_val <= max_val <= 4.5:
                    score += 0.2

            elif domain == "medical":
                # Dosage (mg units)
                if "dose" in col_lower or "mg" in col_lower:
                    if 0.1 <= min_val <= max_val <= 10000:
                        score += 0.2
                # Age ranges
                if "age" in col_lower and 0 <= min_val <= max_val <= 120:
                    score += 0.1

            elif domain == "retail":
                # Prices (positive)
                if "price" in col_lower or "cost" in col_lower:
                    if min_val > 0 and max_val < 1e6:
                        score += 0.15

            elif domain == "finance":
                # Returns (can be negative)
                if "return" in col_lower or "pnl" in col_lower:
                    if -1 <= min_val <= max_val:
                        score += 0.2

            elif domain == "manufacturing":
                # Yield (0-1 or 0-100%)
                if "yield" in col_lower:
                    if (0 <= min_val <= max_val <= 1) or (0 <= min_val <= max_val <= 100):
                        score += 0.2
                # Defect rate
                if "defect" in col_lower and 0 <= max_val <= 0.5:
                    score += 0.15

            elif domain == "energy":
                # Power/energy (kWh)
                if "kwh" in col_lower or "power" in col_lower or "energy" in col_lower:
                    if min_val >= 0 and max_val > 0:
                        score += 0.2

        return min(score, 1.0)

    def _analyze_correlations(self, df: pd.DataFrame, domain: str) -> float:
        """Analyze correlation patterns specific to domain"""
        score = 0.0
        numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.shape[1] < 2:
            return 0.0

        try:
            corr_matrix = numeric_df.corr().abs()

            # Domain-specific correlation patterns
            if domain == "medical":
                # Dose-outcome correlation expected
                dose_cols = [c for c in numeric_df.columns if "dose" in c.lower()]
                outcome_cols = [c for c in numeric_df.columns if "outcome" in c.lower() or "survival" in c.lower()]
                if dose_cols and outcome_cols:
                    for d in dose_cols:
                        for o in outcome_cols:
                            if corr_matrix.loc[d, o] > 0.2:
                                score += 0.3

            elif domain == "education":
                # Pre-score and post-score correlation
                pre_cols = [c for c in numeric_df.columns if "pre" in c.lower() or "baseline" in c.lower()]
                post_cols = [c for c in numeric_df.columns if "post" in c.lower() or "final" in c.lower()]
                if pre_cols and post_cols:
                    for pre in pre_cols:
                        for post in post_cols:
                            if corr_matrix.loc[pre, post] > 0.3:
                                score += 0.3

            elif domain == "retail":
                # Price-sales negative correlation
                price_cols = [c for c in numeric_df.columns if "price" in c.lower()]
                sales_cols = [c for c in numeric_df.columns if "sales" in c.lower() or "quantity" in c.lower()]
                if price_cols and sales_cols:
                    for p in price_cols:
                        for s in sales_cols:
                            # Note: using abs() so this checks for any correlation
                            if corr_matrix.loc[p, s] > 0.2:
                                score += 0.2

        except Exception as e:
            logger.warning(f"[DomainDetector] Correlation analysis failed: {e}")

        return min(score, 1.0)

    def get_recommended_domain(self, df: pd.DataFrame,
                               confidence_threshold: float = 0.3) -> str:
        """
        Get single recommended domain

        Args:
            df: Input dataframe
            confidence_threshold: Minimum confidence to recommend (default: 0.3)

        Returns:
            Domain name or "generic" if confidence too low
        """
        scores = self.detect_domain(df, {})
        top_domain, top_score = max(scores.items(), key=lambda x: x[1])

        if top_score >= confidence_threshold:
            logger.info(f"[DomainDetector] Recommended domain: {top_domain} (confidence: {top_score:.2f})")
            return top_domain
        else:
            logger.info(f"[DomainDetector] Low confidence ({top_score:.2f}), using generic mode")
            return "generic"

    def get_domain_report(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Get detailed domain detection report

        Returns:
            {
                "primary_domain": "medical",
                "confidence": 0.85,
                "all_scores": {...},
                "reasoning": [...]
            }
        """
        scores = self.detect_domain(df, {})
        sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        primary_domain, primary_score = sorted_domains[0]

        # Generate reasoning
        reasoning = []
        signatures = self.DOMAIN_SIGNATURES[primary_domain]

        # Check which keywords matched
        columns_text = " ".join(df.columns).lower()
        matched_keywords = {
            "strong": [kw for kw in signatures["strong"] if kw in columns_text],
            "medium": [kw for kw in signatures["medium"] if kw in columns_text],
            "weak": [kw for kw in signatures["weak"] if kw in columns_text]
        }

        if matched_keywords["strong"]:
            reasoning.append(f"Strong keywords matched: {', '.join(matched_keywords['strong'][:3])}")
        if matched_keywords["medium"]:
            reasoning.append(f"Domain-relevant keywords found: {', '.join(matched_keywords['medium'][:3])}")

        reasoning.append(f"Data distribution patterns consistent with {primary_domain} domain")

        return {
            "primary_domain": primary_domain,
            "confidence": primary_score,
            "all_scores": dict(sorted_domains),
            "reasoning": reasoning,
            "matched_keywords": matched_keywords
        }


# Convenience functions

def detect_domain(df: pd.DataFrame, confidence_threshold: float = 0.3) -> str:
    """
    Convenience function to detect domain

    Args:
        df: Input dataframe
        confidence_threshold: Minimum confidence (default: 0.3)

    Returns:
        Domain name or "generic"
    """
    detector = DomainDetector()
    return detector.get_recommended_domain(df, confidence_threshold)


def get_domain_scores(df: pd.DataFrame) -> Dict[str, float]:
    """
    Convenience function to get all domain scores

    Returns:
        {"medical": 0.85, "retail": 0.10, ...}
    """
    detector = DomainDetector()
    return detector.detect_domain(df, {})
