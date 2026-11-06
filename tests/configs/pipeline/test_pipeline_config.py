import pytest

from saber11.configs.pipeline.pipeline_config import load_config
from saber11.core.errors.pipeline_errors import ConfigError


def test_defaults_use_api_and_guide_parameters():
    config = load_config({})
    assert (config.source, config.period, config.sample_per_group, config.seed) == ("api", "20224", 100, 123)


def test_dataicfes_requires_existing_file(tmp_path):
    with pytest.raises(ConfigError):
        load_config({"SABER11_SOURCE": "dataicfes"})
    data = tmp_path / "saber.txt"
    data.write_text("x")
    config = load_config({"SABER11_SOURCE": "dataicfes", "SABER11_DATAICFES_PATH": str(data)})
    assert config.dataicfes_path == data


@pytest.mark.parametrize(
    "env",
    [
        {"SABER11_SOURCE": "ftp"},
        {"SABER11_PERIOD": "2025"},
        {"SABER11_SAMPLE_PER_GROUP": "cien"},
        {"SABER11_SEED": "0"},
    ],
)
def test_invalid_values_fail_at_load(env):
    with pytest.raises(ConfigError):
        load_config(env)


def test_run_dir_is_per_period():
    assert str(load_config({"SABER11_PERIOD": "20252"}).run_dir) == "output/20252"


def test_directory_path_is_optional_but_must_exist(tmp_path):
    assert load_config({}).directory_path is None
    with pytest.raises(ConfigError):
        load_config({"SABER11_DIRECTORY_PATH": str(tmp_path / "missing.geojson")})
    geo = tmp_path / "colegios.geojson"
    geo.write_text("{}")
    assert load_config({"SABER11_DIRECTORY_PATH": str(geo)}).directory_path == geo
