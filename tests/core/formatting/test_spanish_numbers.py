from saber11.core.formatting.spanish_numbers import fmt_num, fmt_p, fmt_pct


def test_decimal_comma():
    assert fmt_num(0.2021) == "0,202"


def test_thousands_dot():
    assert fmt_num(1234567.891, 1) == "1.234.567,9"


def test_tiny_p_value():
    assert fmt_p(0.00001) == "< 0,001"
    assert fmt_p(0.238) == "0,238"


def test_pct():
    assert fmt_pct(0.765) == "76,5 %"


def test_p_clause_never_doubles_the_operator():
    from saber11.core.formatting.spanish_numbers import fmt_p_clause
    assert fmt_p_clause(1e-9) == "p < 0,001"
    assert fmt_p_clause(0.2383) == "p = 0,238"
