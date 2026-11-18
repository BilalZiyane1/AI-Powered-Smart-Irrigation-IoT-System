from src.irrigation.anomaly import OnlineAnomalyDetector


def test_invalid_reading_is_reported():
    anomalies = OnlineAnomalyDetector().update(-1)
    assert anomalies[0].kind == "invalid_reading"


def test_pump_without_effect_is_reported():
    anomalies = OnlineAnomalyDetector().update(40, pump_on=True, irrigation_effect=0)
    assert anomalies[0].kind == "pump_no_response"
