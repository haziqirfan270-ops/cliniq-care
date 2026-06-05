"""Validation tests for the ClinIQ Care inference engine.

Each case maps a set of selected symptoms (and optional age) to the diagnosis
the rule base should infer. These double as the project's validation evidence -
the same cases are documented in VALIDATION.md.
"""

import pytest

from rules import diagnose

# (test id, selected fact IDs, age, expected diagnosis, expected severity)
CASES = [
    # --- Fever category ---
    ("flu",            ["F1", "F4", "F5", "F6"],       30,   "Likely Influenza (Flu)",      "self-care"),
    ("covid",          ["F1", "F7", "F8"],             40,   "Possible COVID-19",           "see-doctor"),
    ("dengue",         ["F1", "F4", "F15"],            25,   "Possible Dengue",             "see-doctor"),
    ("malaria",        ["F1", "F4", "F6"],             35,   "Possible Malaria",            "see-doctor"),
    ("chickenpox_kid", ["F1", "F2", "F3"],             10,   "Likely Chickenpox (children)","see-doctor"),
    ("chickenpox_adt", ["F1", "F2", "F3"],             30,   "Likely Chickenpox (adults)",  "see-doctor"),
    ("general_fever",  ["F1"],                         30,   "General Fever",               "monitor"),

    # --- Respiratory ---
    ("common_cold",    ["F10", "F9"],                  22,   "Likely Common Cold",          "self-care"),
    ("bronchitis",     ["F7", "F17"],                  45,   "Possible Bronchitis",         "self-care"),
    ("asthma",         ["F7", "F18"],                  50,   "Possible Asthma or Bronchitis","see-doctor"),

    # --- Throat ---
    ("tonsillitis",    ["F5", "F26"],                  18,   "Possible Tonsillitis",        "see-doctor"),
    ("laryngitis",     ["F5", "F27"],                  33,   "Possible Laryngitis",         "self-care"),
    ("throat_infect",  ["F5"],                         28,   "Possible Throat Infection",   "self-care"),

    # --- Digestive ---
    ("food_poisoning", ["F12", "F13", "F14"],          27,   "Likely Food Poisoning",       "self-care"),
    ("constipation",   ["F19", "F20"],                 60,   "Constipation",                "self-care"),
    ("gastritis",      ["F21", "F22"],                 41,   "Possible Gastritis",          "self-care"),

    # --- Headache / urgent ---
    ("migraine",       ["F4", "F12", "F23"],           29,   "Possible Migraine",           "self-care"),
    ("meningitis",     ["F4", "F24"],                  20,   "Possible Meningitis",         "urgent"),
    ("tension_head",   ["F4", "F25"],                  38,   "Tension Headache",            "self-care"),

    # --- Skin / allergy ---
    ("scabies",        ["F11", "F29"],                 24,   "Possible Scabies",            "see-doctor"),
    ("eczema",         ["F11", "F30"],                 31,   "Possible Eczema",             "self-care"),
    ("normal_itch",    ["F11"],                        26,   "Normal Itching",              "self-care"),
]


@pytest.mark.parametrize("name,facts,age,exp_dx,exp_sev",
                         CASES, ids=[c[0] for c in CASES])
def test_diagnosis(name, facts, age, exp_dx, exp_sev):
    result = diagnose(facts, age=age)
    assert result["diagnosis"] == exp_dx
    assert result["severity"] == exp_sev


def test_conflict_resolution_prefers_specific_rule():
    """Flu (4 symptoms) must beat the subsumed malaria rule (3 symptoms)."""
    result = diagnose(["F1", "F4", "F5", "F6"], age=30)
    assert result["diagnosis"] == "Likely Influenza (Flu)"
    assert result["fired_rule"] == 3


def test_no_symptoms_safety_net():
    result = diagnose([], age=30)
    assert result["diagnosis"] == "No symptoms selected"


def test_too_many_symptoms_safety_net():
    many = [f"F{i}" for i in range(1, 13)]  # 12 symptoms
    result = diagnose(many, age=30)
    assert result["diagnosis"] == "Too many symptoms selected"


def test_no_matching_rule_safety_net():
    result = diagnose(["F19"], age=30)  # bloating alone matches nothing
    assert result["diagnosis"] == "No specific match"


def test_confidence_scales_with_symptom_count():
    """More matched symptoms -> higher confidence; one symptom stays modest."""
    three = diagnose(["F12", "F13", "F14"], age=30)   # 3-symptom rule
    one = diagnose(["F5"], age=30)                     # 1-symptom rule
    assert three["confidence"] == 85
    assert one["confidence"] == 50
    assert one["confidence"] < three["confidence"]


def test_chatbot_keyword_extraction():
    """Offline keyword path maps free text to the right facts."""
    from chatbot import extract_symptoms
    facts = extract_symptoms("I have a fever, headache and chills")
    assert set(["F1", "F4", "F6"]).issubset(set(facts))
