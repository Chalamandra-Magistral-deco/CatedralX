import pytest

from ENERGY.virtual_vanadium_battery import VirtualVanadiumBattery


def make_battery(**overrides):
    values = {
        "operational_capacity": 600,
        "adaptive_capacity": 400,
        "operational_initial": 500,
        "adaptive_initial": 300,
        "max_discharge_per_cycle": 150,
        "operational_reserve": 100,
        "adaptive_reserve": 50,
    }
    values.update(overrides)
    return VirtualVanadiumBattery(**values)


def test_dual_reservoir_snapshot_separates_capacity_and_charge():
    battery = make_battery()
    state = battery.snapshot()
    assert state["total_capacity"] == 1000
    assert state["total_charge"] == 800
    assert state["state_of_charge"] == pytest.approx(0.8)
    assert state["operational"].capacity == 600
    assert state["adaptive"].charge == 300


def test_discharge_respects_reserve_and_power_limit():
    battery = make_battery()
    receipt = battery.discharge("operational", 150, transaction_id="cycle-1")
    assert receipt.balance == 350
    with pytest.raises(ValueError, match="potencia máxima"):
        battery.discharge("operational", 151)
    with pytest.raises(ValueError, match="Reserva insuficiente"):
        battery.discharge("operational", 251)


def test_charge_cannot_exceed_capacity_and_requires_explicit_input():
    battery = make_battery()
    with pytest.raises(ValueError, match="capacidad disponible"):
        battery.charge("adaptive", 101)
    assert battery.snapshot()["adaptive"].charge == 300
    battery.charge("adaptive", 100, transaction_id="external-budget-1")
    assert battery.snapshot()["adaptive"].charge == 400


def test_duplicate_transaction_is_rejected_without_mutating_balance():
    battery = make_battery()
    battery.discharge("operational", 50, transaction_id="same-id")
    before = battery.snapshot()["operational"].charge
    with pytest.raises(ValueError, match="duplicado"):
        battery.discharge("operational", 25, transaction_id="same-id")
    assert battery.snapshot()["operational"].charge == before


@pytest.mark.parametrize("amount", [-1, float("nan"), float("inf"), True])
def test_invalid_amount_is_rejected(amount):
    battery = make_battery()
    with pytest.raises(ValueError):
        battery.discharge("operational", amount)


def test_unknown_reservoir_is_rejected():
    battery = make_battery()
    with pytest.raises(ValueError, match="desconocido"):
        battery.discharge("other", 1)


def test_zero_capacity_has_zero_state_of_charge():
    battery = VirtualVanadiumBattery(
        operational_capacity=0, adaptive_capacity=0, max_discharge_per_cycle=0
    )
    assert battery.snapshot()["state_of_charge"] == 0
    assert battery.snapshot()["status"] == "depleted"