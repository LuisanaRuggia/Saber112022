"""Spanish number formatting: decimal comma and thousands dot."""


def fmt_num(value: float, decimals: int = 3) -> str:
    """Format a number with decimal comma."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def fmt_p(value: float) -> str:
    """Format a p-value, using '< 0,001' when tiny."""
    return "< 0,001" if value < 0.001 else fmt_num(value, 3)


def fmt_p_clause(value: float) -> str:
    """Format 'p < 0,001' or 'p = x' without doubling the operator."""
    return "p < 0,001" if value < 0.001 else f"p = {fmt_num(value, 3)}"


def fmt_pct(ratio: float, decimals: int = 1) -> str:
    """Format a 0-1 ratio as a percentage."""
    return fmt_num(ratio * 100, decimals) + " %"
