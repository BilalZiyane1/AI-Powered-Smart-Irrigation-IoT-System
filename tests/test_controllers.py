from src.irrigation.controllers import ControllerConfig, PredictiveController, RuleController


def test_rule_controller_hysteresis_and_runtime_limit():
    controller = RuleController(ControllerConfig(min_activation_interval_minutes=30, max_pump_runtime_minutes=20))
    assert controller.decide(minute=0, moisture=39) is True
    assert controller.decide(minute=10, moisture=55) is True
    assert controller.decide(minute=20, moisture=55) is False
    assert controller.decide(minute=21, moisture=39) is False
    assert controller.decide(minute=31, moisture=39) is True


def test_predictive_controller_falls_back_to_current_moisture():
    controller = PredictiveController()
    assert controller.decide(minute=0, moisture=50, predicted_moisture=35) is True
    controller = PredictiveController()
    assert controller.decide(minute=0, moisture=50, predicted_moisture=None, prediction_fresh=False) is False
