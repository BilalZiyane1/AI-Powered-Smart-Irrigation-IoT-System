from src.irrigation.env_model import SoilEnv


def test_moisture_stays_in_bounds_and_pump_adds_water():
    env = SoilEnv(initial_moisture=50, seed=4, noise_std=0)
    before = env.step(10, pump_on=False).soil_moisture
    after = env.step(10, pump_on=True).soil_moisture
    assert 0 <= before <= 100
    assert 0 <= after <= 100
    assert after > before


def test_seed_reproduces_measurements():
    first = SoilEnv(seed=12)
    second = SoilEnv(seed=12)
    a = [first.step(10, False).soil_moisture for _ in range(5)]
    b = [second.step(10, False).soil_moisture for _ in range(5)]
    assert a == b
