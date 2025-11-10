"""
Multilingual Column Selection
Supports column detection in multiple languages (English, Japanese, Chinese, Spanish, German, French)
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import re
from backend.inference.column_selection import ColumnSelector


class MultilingualColumnSelector(ColumnSelector):
    """
    Extended column selector with multilingual support

    Supported languages:
    - English (en)
    - Japanese (ja)
    - Chinese (zh)
    - Spanish (es)
    - German (de)
    - French (fr)
    """

    # Multilingual keyword dictionaries
    OUTCOME_KEYWORDS_ML = {
        "en": ["outcome", "result", "y", "target", "score", "value", "response",
               "sales", "revenue", "profit", "spend", "days", "recovery", "test",
               "grade", "performance", "return", "yield"],
        "ja": ["結果", "成果", "アウトカム", "目標", "売上", "収益", "利益",
               "スコア", "点数", "成績", "回復", "日数", "収量"],
        "zh": ["结果", "成果", "目标", "销售", "收入", "利润", "分数", "成绩", "收益"],
        "es": ["resultado", "objetivo", "ventas", "ingresos", "beneficio", "puntuación"],
        "de": ["ergebnis", "ziel", "umsatz", "gewinn", "punktzahl", "leistung"],
        "fr": ["résultat", "objectif", "ventes", "revenus", "bénéfice", "score", "performance"]
    }

    TREATMENT_KEYWORDS_ML = {
        "en": ["treatment", "treat", "intervention", "policy", "program", "drug",
               "therapy", "condition", "group", "arm", "dose", "campaign", "promo",
               "portfolio", "strategy"],
        "ja": ["処置", "治療", "介入", "政策", "プログラム", "薬剤", "投薬",
               "条件", "群", "群分け", "キャンペーン", "施策"],
        "zh": ["治疗", "干预", "政策", "项目", "药物", "条件", "组", "活动"],
        "es": ["tratamiento", "intervención", "política", "programa", "medicamento",
               "condición", "grupo", "campaña"],
        "de": ["behandlung", "intervention", "politik", "programm", "medikament",
               "bedingung", "gruppe", "kampagne"],
        "fr": ["traitement", "intervention", "politique", "programme", "médicament",
               "condition", "groupe", "campagne"]
    }

    UNIT_ID_KEYWORDS_ML = {
        "en": ["id", "identifier", "patient", "customer", "student", "account",
               "user", "subject", "person", "unit", "entity", "node", "region"],
        "ja": ["id", "識別子", "患者", "顧客", "学生", "ユーザー", "対象", "個人", "単位"],
        "zh": ["id", "标识", "患者", "客户", "学生", "用户", "对象", "个人", "单位"],
        "es": ["id", "identificador", "paciente", "cliente", "estudiante", "usuario", "sujeto"],
        "de": ["id", "kennung", "patient", "kunde", "student", "benutzer", "einheit"],
        "fr": ["id", "identifiant", "patient", "client", "étudiant", "utilisateur", "sujet"]
    }

    TIME_KEYWORDS_ML = {
        "en": ["time", "date", "year", "month", "week", "day", "period", "quarter",
               "timestamp", "datetime", "when", "cohort"],
        "ja": ["時間", "日付", "年", "月", "週", "日", "期間", "四半期", "タイムスタンプ", "時刻"],
        "zh": ["时间", "日期", "年", "月", "周", "日", "期间", "季度", "时间戳"],
        "es": ["tiempo", "fecha", "año", "mes", "semana", "día", "período", "trimestre"],
        "de": ["zeit", "datum", "jahr", "monat", "woche", "tag", "zeitraum", "quartal"],
        "fr": ["temps", "date", "année", "mois", "semaine", "jour", "période", "trimestre"]
    }

    def __init__(self, df: pd.DataFrame):
        """Initialize multilingual column selector"""
        super().__init__(df)
        self.detected_language = self._detect_language()

        # Override parent keywords with multilingual versions
        self.OUTCOME_KEYWORDS = self._get_keywords("outcome")
        self.TREATMENT_KEYWORDS = self._get_keywords("treatment")
        self.UNIT_ID_KEYWORDS = self._get_keywords("unit_id")
        self.TIME_KEYWORDS = self._get_keywords("time")

        # Recompute scores with multilingual keywords
        self.column_scores = self._compute_column_scores()

    def _detect_language(self) -> str:
        """
        Detect language from column names

        Returns:
            Language code: "en", "ja", "zh", "es", "de", "fr"
        """
        text = " ".join(self.df.columns)

        # Japanese: Hiragana/Katakana
        if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
            return "ja"

        # Chinese: CJK characters (excluding common Japanese kanji)
        if re.search(r'[\u4e00-\u9fff]', text):
            # Check for Japanese-specific characters
            if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
                return "ja"
            return "zh"

        # Cyrillic (Russian, etc.)
        if re.search(r'[а-яА-Я]', text):
            return "ru"

        # Spanish-specific characters
        if re.search(r'[áéíóúñü]', text.lower()):
            return "es"

        # French-specific characters
        if re.search(r'[àâçéèêëîïôùûü]', text.lower()):
            return "fr"

        # German-specific characters
        if re.search(r'[äöüß]', text.lower()):
            return "de"

        # Default to English
        return "en"

    def _get_keywords(self, role: str) -> List[str]:
        """
        Get keywords for a role in detected language + English fallback

        Args:
            role: "outcome", "treatment", "unit_id", or "time"

        Returns:
            Combined keyword list
        """
        keyword_map = {
            "outcome": self.OUTCOME_KEYWORDS_ML,
            "treatment": self.TREATMENT_KEYWORDS_ML,
            "unit_id": self.UNIT_ID_KEYWORDS_ML,
            "time": self.TIME_KEYWORDS_ML
        }

        keywords_dict = keyword_map.get(role, {})

        # Combine detected language + English (for mixed datasets)
        keywords = []
        keywords.extend(keywords_dict.get(self.detected_language, []))
        if self.detected_language != "en":
            keywords.extend(keywords_dict.get("en", []))

        return keywords

    def get_language_info(self) -> Dict[str, any]:
        """
        Get detected language information

        Returns:
            {
                "detected_language": "ja",
                "language_name": "Japanese",
                "sample_columns": ["患者ID", "治療", "結果"]
            }
        """
        language_names = {
            "en": "English",
            "ja": "Japanese",
            "zh": "Chinese",
            "es": "Spanish",
            "de": "German",
            "fr": "French",
            "ru": "Russian"
        }

        return {
            "detected_language": self.detected_language,
            "language_name": language_names.get(self.detected_language, "Unknown"),
            "sample_columns": list(self.df.columns[:5])
        }

    def explain_selection(self) -> str:
        """Human-readable explanation with language info"""
        lang_info = self.get_language_info()
        lines = [
            "=== Multilingual Column Selection ===",
            f"Detected Language: {lang_info['language_name']} ({lang_info['detected_language']})",
            ""
        ]

        # Call parent's explain_selection and append
        parent_explanation = super().explain_selection()
        lines.append(parent_explanation)

        return "\n".join(lines)


# Convenience functions

def auto_select_columns_ml(df: pd.DataFrame, confidence_threshold: float = 0.3) -> Dict[str, any]:
    """
    Multilingual column selection

    Args:
        df: Input dataframe
        confidence_threshold: Minimum confidence score

    Returns:
        Selected columns with language info
    """
    selector = MultilingualColumnSelector(df)
    result = selector.select_columns(confidence_threshold)

    # Add language detection info
    result["language_info"] = selector.get_language_info()

    return result


def detect_column_language(df: pd.DataFrame) -> str:
    """
    Detect language of column names

    Returns:
        Language code: "en", "ja", "zh", etc.
    """
    selector = MultilingualColumnSelector(df)
    return selector.detected_language


# Example usage
if __name__ == "__main__":
    import sys

    # Test with sample data
    print("=== Multilingual Column Selector Test ===\n")

    # English example
    df_en = pd.DataFrame({
        "patient_id": [1, 2, 3],
        "treatment": ["A", "B", "A"],
        "outcome_days": [100, 200, 150]
    })
    selector_en = MultilingualColumnSelector(df_en)
    print("English Dataset:")
    print(selector_en.explain_selection())
    print()

    # Japanese example
    df_ja = pd.DataFrame({
        "患者ID": [1, 2, 3],
        "治療群": ["A", "B", "A"],
        "結果日数": [100, 200, 150]
    })
    selector_ja = MultilingualColumnSelector(df_ja)
    print("Japanese Dataset:")
    print(selector_ja.explain_selection())
    print()

    # Chinese example
    df_zh = pd.DataFrame({
        "患者编号": [1, 2, 3],
        "治疗组": ["A", "B", "A"],
        "结果天数": [100, 200, 150]
    })
    selector_zh = MultilingualColumnSelector(df_zh)
    print("Chinese Dataset:")
    print(selector_zh.explain_selection())
