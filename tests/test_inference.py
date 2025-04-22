import pytest
from run import extract_features_from_code, infer_requirements

def test_feature_extraction():
    code = '''
# validate something
def foo(): pass
bar = "test"
'''
    features = extract_features_from_code(code)
    assert "foo" in [f["name"] for f in features["functions"]]
    assert "bar" in features["variables"]
    assert "test" in features["strings"]
    assert any("validate" in c for c in features["comments"])

def test_inference_with_mock_glossary():
    features = {
        "functions": [{"name": "charge_late_fee", "doc": ""}],
        "variables": ["customer_id"],
        "strings": [],
        "comments": ["# validate input"]
    }
    glossary = {"customer_id": "A unique ID for a customer"}
    reqs = infer_requirements(features, glossary)
    assert any("customer_id" in r["text"] for r in reqs)
    assert all(0.0 <= r["confidence"] <= 1.0 for r in reqs)
