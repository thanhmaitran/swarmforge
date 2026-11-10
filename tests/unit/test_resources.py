import pytest
from helpers import STANDARD

from swarmforge.core.exceptions import ValidationError
from swarmforge.resources.battery import Battery
from swarmforge.resources.energy_model import EnergyModel
from swarmforge.resources.reservation import ReservationManager


def test_battery_bounds():
    b = Battery(100, 50)
    assert b.consume(80) == 50 and b.level == 0
    assert b.charge(500) == 100 and b.fraction == 1.0
    with pytest.raises(ValidationError):
        Battery(0)
    with pytest.raises(ValidationError):
        Battery(10, 20)


def test_energy_model_monotone_in_load():
    m = EnergyModel(STANDARD, idle_power=0.1)
    assert m.travel_energy(10, 0) == pytest.approx(10.0)
    assert m.travel_energy(10, 100) > m.travel_energy(10, 50) > m.travel_energy(10, 0)
    assert m.idle_energy(10) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        m.travel_energy(-1)


def test_reservation_request_grant_release_timeout():
    rm = ReservationManager()
    assert rm.request("cs1", "A", 0.0, timeout=5.0)
    assert not rm.request("cs1", "B", 1.0) and rm.conflicts == 1
    assert rm.request("cs1", "A", 2.0, timeout=5.0)  # re-entrant for the holder; timeout restarts at t=2
    assert rm.holder("cs1", 3.0) == "A"
    assert rm.holder("cs1", 8.0) is None  # timed out
    assert rm.request("cs1", "B", 8.0)
    assert not rm.release("cs1", "A") and rm.release("cs1", "B")
