"""The rows built from the model's answer carry English keys and options, also when the
model answers with the Italian keys of the versions before 2.0."""
import json

from quaesitor.blueprints.ai import ai_rows_from_json, AI_NODES_PROMPT
from quaesitor.ontology import ai_rules


def test_rows_from_an_italian_answer():
    d = {"nodes": [
        {"key": "n1", "type": "person", "value": "Mario Rossi", "birth": "1980-03-12"},
        {"key": "n2", "type": "place", "value": "Roma"},
        {"key": "n3", "type": "drug", "fields": {"sostanza": "cocaina", "quantita": "12", "unita": "g"}},
        {"key": "n4", "type": "vehicle", "value": "AB 123 CD", "brand": "Fiat", "color": "white"}],
        "links": [{"from": "n1", "to": "n2", "label": "nato a", "direction": "forward"},
                  {"from": "n1", "to": "n3", "label": "seized", "direction": "forward"}]}
    rows = ai_rows_from_json(d)
    birth = next(r for r in rows if r.get("name2") == "Roma")
    assert birth["rel"] == "place of birth" and birth["type1"] == "person" and birth["type2"] == "place"
    assert birth["birth1"] == "1980-03-12"
    drug = next(r for r in rows if r.get("type2") == "drug")
    assert json.loads(drug["fields2"]) == {"substance": "Cocaine", "quantity": "12", "unit": "g"}
    car = next(r for r in rows if r.get("type1") == "vehicle")
    assert car["name1"] == "AB123CD" and car["color1"] == "White"


def test_prompt_asks_for_english_keys_and_labels():
    rules = ai_rules()
    assert "substance options:" in rules and "Drug trafficking" in rules
    for word in ("sostanza", "residenza", "città di nascita", "indagato"):
        assert word not in rules and word not in AI_NODES_PROMPT, word
