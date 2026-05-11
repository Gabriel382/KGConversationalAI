from kgconvai.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.llm_mode == "template"
    assert s.whisper_model == "base"
    assert 0.0 <= s.faq_confidence_threshold <= 1.0


def test_settings_overridden_via_kwargs():
    s = Settings(llm_mode="api", whisper_model="small")
    assert s.llm_mode == "api"
    assert s.whisper_model == "small"


def test_settings_paths_compose_data_dir(tmp_path):
    s = Settings(data_dir=tmp_path)
    assert s.conversation_graph_path == tmp_path / "conversation_graph.json"
    assert s.faq_path == tmp_path / "faq.json"
    assert s.templates_path == tmp_path / "templates.json"
