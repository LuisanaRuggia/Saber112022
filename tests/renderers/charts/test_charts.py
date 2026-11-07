import pytest

from saber11.renderers.charts.assumption_charts import mardia_chart
from saber11.renderers.charts.chart_style import SHIFT_COLORS
from saber11.renderers.charts.descriptive_charts import correlation_heatmap, dispersion_chart, means_chart
from saber11.renderers.charts.result_charts import locality_chart, pca_chart, private_share_chart
from tests.fakes.results_factory import build_results

PNG = b"\x89PNG\r\n\x1a\n"


@pytest.fixture(scope="module")
def results():
    return build_results()


def test_every_chart_renders_a_png(results):
    charts = [means_chart(results.descriptive.means), dispersion_chart(results.descriptive.std),
              correlation_heatmap(results.descriptive.correlation), mardia_chart(results.assumptions, 0.05),
              pca_chart(results.pca), private_share_chart(results.sensitivity.official_only.profile),
              locality_chart(results.spatial.localities.table)]
    assert all(chart.startswith(PNG) and len(chart) > 1000 for chart in charts)


def test_each_shift_has_its_own_fixed_color():
    assert list(SHIFT_COLORS) == ["COMPLETA", "MAÑANA", "TARDE", "UNICA"]
    assert len(set(SHIFT_COLORS.values())) == 4
