"""Shared wording helpers for the narrative conclusions."""

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_p
from saber11.models.analysis.analysis_models import HotellingPair, ManovaResult
from saber11.models.dataset.dataset_models import SHIFT_LABELS


def shift_label(code: str) -> str:
    """Return the Spanish label of a shift code."""
    return SHIFT_LABELS.get(code, code)


def p_text(p: float) -> str:
    """Return '< 0,001' or '= x' to follow a 'p'."""
    return fmt_p(p) if p < 0.001 else "= " + fmt_p(p)


def manova_clause(manova: ManovaResult) -> str:
    """Return '(Pillai = x, p ..., η² parcial = y)'."""
    return (f"(Pillai = {fmt_num(manova.pillai)}, p {p_text(manova.pillai_p)}, "
            f"η² parcial = {fmt_num(manova.partial_eta_squared)})")


def differing_pairs(pairs: list[HotellingPair], alpha: float) -> list[str]:
    """Return 'A y B (p ajustado ...)' for every pair that differs after Bonferroni."""
    return [f"{shift_label(p.group_a)} y {shift_label(p.group_b)} (p ajustado {p_text(p.p_bonferroni)})"
            for p in pairs if p.p_bonferroni < alpha]
