from router.rule_based import select_model


def test_select_model_code_high_uses_code_rules():
    selection = select_model(band="high", task_type="code")
    assert selection.provider == "openai"
    assert selection.model == "gpt-4o"
    assert selection.band == "high"
    assert selection.route_source == "rules_v1"


def test_select_model_respects_force_model_override():
    selection = select_model(band="low", task_type="default", force_model="custom-model")
    assert selection.model == "custom-model"
    assert selection.route_source == "manual_override"
    assert selection.provider == "unknown"


def test_unknown_task_type_falls_back_to_default():
    selection = select_model(band="low", task_type="nonexistent")
    assert selection.provider == "openai"
    assert selection.model == "gpt-4o-mini"
    assert selection.route_source == "rules_v1"


def test_unknown_band_normalizes_to_medium():
    selection = select_model(band="extreme", task_type="default")
    assert selection.band == "medium"
    assert selection.provider == "openai"
    assert selection.model == "gpt-4o"
