import json

from src.irrigation.sensor_sim import is_valid_soil_reading


def test_missing_and_invalid_sensor_readings_are_rejected():
    assert is_valid_soil_reading(None) is False
    assert is_valid_soil_reading(-1) is False
    assert is_valid_soil_reading(101) is False
    assert is_valid_soil_reading("not-a-number") is False
    assert is_valid_soil_reading(42.5) is True


def test_nodered_flow_rejects_missing_values_and_uses_internal_gateway():
    with open("nodered/flows.json", encoding="utf-8") as handle:
        flows = json.load(handle)
    by_name = {node.get("name"): node for node in flows}

    for name in ("Validate and retain", "Safe irrigation decision"):
        function = by_name[name]["func"]
        assert "soil_moisture == null" in function
        assert "moisture < 0" in function or "value < 0" in function

    assert "http://coap-gateway:8081/pump" in by_name["Safe irrigation decision"]["func"]
    assert "http://coap-gateway:8081/pump" in by_name["Prepare manual CoAP command"]["func"]
    assert "host.containers.internal" not in json.dumps(flows)
