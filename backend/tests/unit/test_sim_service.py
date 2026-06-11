import pytest

from app.modules.cli.schemas import ClimateOverride
from app.modules.sim.service import resolve_simulation_climate


def test_resolve_named_scenario() -> None:
    climate = resolve_simulation_climate("heavy_rain")

    assert climate.precip_mm == 35
    assert climate.humidity_pct == 95


def test_override_wins_over_scenario() -> None:
    override = ClimateOverride(temperature_c=1, humidity_pct=2, precip_mm=3, uv_index=4)

    assert resolve_simulation_climate("dry", override) == override


def test_unknown_scenario_raises() -> None:
    with pytest.raises(ValueError):
        resolve_simulation_climate("storm")
