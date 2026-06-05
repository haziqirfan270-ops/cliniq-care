"""
ClinIQ Care - Knowledge Base and Inference Engine.

This module holds the FACTS (symptoms / patient attributes) and the RULE BASE
(IF-THEN production rules) for the ClinIQ Care expert system, plus a simple
forward-chaining inference engine.

Improvements over the original report:
  * Specificity-based conflict resolution (the rule that matches the most
    symptoms wins) so overlapping rules no longer fire ambiguously.
  * A transparent confidence score derived from how many of a rule's
    conditions the user actually selected.
"""

# ---------------------------------------------------------------------------
# 1. FACTS - each fact is a symptom or a patient attribute.
# ---------------------------------------------------------------------------
FACTS = {
    "F1":  "fever",
    "F2":  "skin rash",
    "F3":  "swollen glands",
    "F4":  "headache",
    "F5":  "sore throat",
    "F6":  "chills",
    "F7":  "cough",
    "F8":  "loss of taste or smell",
    "F9":  "runny nose",
    "F10": "sneezing",
    "F11": "itchy skin",
    "F12": "nausea",
    "F13": "vomiting",
    "F14": "diarrhea",
    "F15": "body aches",
    "F16": "chest pain",
    "F17": "fatigue",
    "F18": "shortness of breath",
    "F19": "bloating",
    "F20": "constipation",
    "F21": "abdominal pain",
    "F22": "loss of appetite",
    "F23": "light sensitivity",
    "F24": "stiff neck",
    "F25": "dizziness",
    "F26": "white patches in throat",
    "F27": "hoarseness",
    "F28": "difficulty swallowing",
    "F29": "blisters",
    "F30": "skin redness",
    "F31": "rash (general)",
}

# Symptoms grouped by category for the step-by-step UI.
CATEGORIES = {
    "Fever":      ["F1", "F2", "F3", "F4", "F5", "F6", "F15"],
    "Respiratory": ["F7", "F8", "F9", "F10", "F16", "F17", "F18"],
    "Throat":     ["F5", "F26", "F27", "F28"],
    "Digestive":  ["F12", "F13", "F14", "F19", "F20", "F21", "F22"],
    "Headache":   ["F4", "F23", "F24", "F25"],
    "Skin / Allergy": ["F11", "F2", "F29", "F30", "F31"],
}

# ---------------------------------------------------------------------------
# 2. RULE BASE - IF (set of facts) THEN (diagnosis + advice + severity).
#    severity: "self-care" | "monitor" | "see-doctor" | "urgent"
# ---------------------------------------------------------------------------
RULES = [
    # --- Fever ---
    {"id": 1,  "if": ["F1", "F2", "F3"], "min_age": None, "max_age": 17,
     "diagnosis": "Likely Chickenpox (children)", "severity": "see-doctor",
     "advice": "Rest, keep hydrated, avoid scratching the rash, and see a doctor for antiviral options."},
    {"id": 2,  "if": ["F1", "F2", "F3"], "min_age": 18, "max_age": None,
     "diagnosis": "Likely Chickenpox (adults)", "severity": "see-doctor",
     "advice": "Adults can develop complications - rest, hydrate, and consult a doctor promptly."},
    {"id": 3,  "if": ["F1", "F4", "F5", "F6"],
     "diagnosis": "Likely Influenza (Flu)", "severity": "self-care",
     "advice": "Rest, drink fluids, and take fever relief. See a doctor if symptoms worsen after 3-4 days."},
    {"id": 4,  "if": ["F1", "F7", "F8"],
     "diagnosis": "Possible COVID-19", "severity": "see-doctor",
     "advice": "Isolate, take a COVID test, monitor breathing, and seek care if you feel short of breath."},
    {"id": 5,  "if": ["F1", "F4", "F15"],
     "diagnosis": "Possible Dengue", "severity": "see-doctor",
     "advice": "Hydrate well, avoid ibuprofen/aspirin, and get a blood test - watch for warning signs."},
    {"id": 6,  "if": ["F1", "F4", "F6"],
     "diagnosis": "Possible Malaria", "severity": "see-doctor",
     "advice": "If you have travelled to a malaria area, see a doctor for a blood test soon."},
    {"id": 7,  "if": ["F1", "F21"],
     "diagnosis": "Possible Typhoid", "severity": "see-doctor",
     "advice": "Persistent fever with abdominal pain needs a doctor's assessment and possibly a stool/blood test."},
    {"id": 8,  "if": ["F1", "F9", "F2"],
     "diagnosis": "Possible Measles", "severity": "see-doctor",
     "advice": "Isolate to avoid spreading, rest, hydrate, and consult a doctor."},
    {"id": 9,  "if": ["F1", "F7"],
     "diagnosis": "Mild Respiratory Infection", "severity": "self-care",
     "advice": "Rest, warm fluids, and monitor. See a doctor if it lasts more than a week."},
    {"id": 10, "if": ["F1"],
     "diagnosis": "General Fever", "severity": "monitor",
     "advice": "Rest, stay hydrated, and monitor your temperature. Seek care if it stays high for over 3 days."},

    # --- Respiratory / Cough ---
    {"id": 11, "if": ["F7", "F16"],
     "diagnosis": "Persistent Cough with Chest Pain", "severity": "see-doctor",
     "advice": "A lasting cough with chest pain should be checked by a doctor to rule out infection."},
    {"id": 12, "if": ["F7", "F17"],
     "diagnosis": "Possible Bronchitis", "severity": "self-care",
     "advice": "Rest, warm fluids, and a humidifier may help. See a doctor if it persists beyond 10 days."},
    {"id": 13, "if": ["F7", "F18"],
     "diagnosis": "Possible Asthma or Bronchitis", "severity": "see-doctor",
     "advice": "Cough with shortness of breath should be evaluated by a doctor."},
    {"id": 14, "if": ["F10", "F9"],
     "diagnosis": "Likely Common Cold", "severity": "self-care",
     "advice": "Rest, fluids, and over-the-counter cold relief. Usually clears within a week."},

    # --- Throat / Mouth ---
    {"id": 15, "if": ["F5"],
     "diagnosis": "Possible Throat Infection", "severity": "self-care",
     "advice": "Warm salt-water gargle, fluids, and rest. See a doctor if it worsens or lasts over a week."},
    {"id": 16, "if": ["F5", "F26"],
     "diagnosis": "Possible Tonsillitis", "severity": "see-doctor",
     "advice": "White patches with a sore throat may need antibiotics - see a doctor."},
    {"id": 17, "if": ["F5", "F27"],
     "diagnosis": "Possible Laryngitis", "severity": "self-care",
     "advice": "Rest your voice, drink warm fluids. See a doctor if hoarseness lasts over 2 weeks."},
    {"id": 18, "if": ["F5", "F28"],
     "diagnosis": "Throat Infection", "severity": "see-doctor",
     "advice": "Difficulty swallowing needs a doctor's check to ensure your airway is clear."},

    # --- Digestive ---
    {"id": 19, "if": ["F12", "F13", "F14"],
     "diagnosis": "Likely Food Poisoning", "severity": "self-care",
     "advice": "Hydrate with oral rehydration salts, rest. Seek care if it lasts over 2 days or you see blood."},
    {"id": 20, "if": ["F19", "F20"],
     "diagnosis": "Constipation", "severity": "self-care",
     "advice": "Increase fibre and water, stay active. See a doctor if it persists over a week."},
    {"id": 21, "if": ["F21", "F22"],
     "diagnosis": "Possible Gastritis", "severity": "self-care",
     "advice": "Eat smaller meals, avoid spicy/acidic food. See a doctor if pain is severe or recurring."},
    {"id": 22, "if": ["F12", "F19"],
     "diagnosis": "Indigestion", "severity": "self-care",
     "advice": "Eat slowly, avoid heavy meals. Antacids may help. See a doctor if it keeps happening."},

    # --- Headache / General ---
    {"id": 23, "if": ["F4", "F12", "F23"],
     "diagnosis": "Possible Migraine", "severity": "self-care",
     "advice": "Rest in a dark, quiet room, hydrate. See a doctor if migraines are frequent."},
    {"id": 24, "if": ["F4", "F24"],
     "diagnosis": "Possible Meningitis", "severity": "urgent",
     "advice": "Headache with a stiff neck can be an emergency - seek urgent medical care now."},
    {"id": 25, "if": ["F4", "F25"],
     "diagnosis": "Tension Headache", "severity": "self-care",
     "advice": "Rest, hydrate, and reduce screen time/stress. Pain relief may help."},

    # --- Itchy Skin / Allergy ---
    {"id": 30, "if": ["F11", "F12"],
     "diagnosis": "Possible Food Allergy", "severity": "see-doctor",
     "advice": "Avoid suspected foods. Seek urgent care if you have swelling or trouble breathing."},
    {"id": 31, "if": ["F11"],
     "diagnosis": "Normal Itching", "severity": "self-care",
     "advice": "Moisturise, avoid irritants. See a doctor if it spreads or won't settle."},
    {"id": 32, "if": ["F11", "F29"],
     "diagnosis": "Possible Scabies", "severity": "see-doctor",
     "advice": "Scabies is contagious - see a doctor for prescription treatment."},
    {"id": 33, "if": ["F11", "F30"],
     "diagnosis": "Possible Eczema", "severity": "self-care",
     "advice": "Use a gentle moisturiser, avoid harsh soaps. See a doctor for persistent flare-ups."},
    {"id": 34, "if": ["F11", "F31"],
     "diagnosis": "Allergic Skin Reaction", "severity": "self-care",
     "advice": "Antihistamines may help. Seek care if it spreads quickly or you feel unwell."},
]

SEVERITY_LABEL = {
    "self-care":  "Self-care at home",
    "monitor":    "Monitor and rest",
    "see-doctor": "Consider seeing a doctor",
    "urgent":     "Seek medical care urgently",
}


def diagnose(selected_facts, age=None):
    """Forward-chaining inference with specificity-based conflict resolution.

    Args:
        selected_facts: iterable of fact IDs the user selected (e.g. ["F1","F4"]).
        age: optional integer age, used by age-specific rules.

    Returns a dict describing the result.
    """
    selected = set(selected_facts)

    # --- Meta / safety-net rules (from the report) ---
    if len(selected) == 0:
        return {"diagnosis": "No symptoms selected",
                "advice": "Please select at least one symptom so we can help.",
                "severity": "monitor", "severity_label": SEVERITY_LABEL["monitor"],
                "confidence": 0, "matched_symptoms": [], "fired_rule": None}

    if len(selected) > 10:
        return {"diagnosis": "Too many symptoms selected",
                "advice": "That is a lot of symptoms at once - please refine to your main ones, "
                          "and consider seeing a doctor.",
                "severity": "see-doctor", "severity_label": SEVERITY_LABEL["see-doctor"],
                "confidence": 0, "matched_symptoms": [], "fired_rule": None}

    # --- Match all rules whose conditions are a subset of selected facts ---
    matches = []
    for rule in RULES:
        if not set(rule["if"]).issubset(selected):
            continue
        if rule.get("max_age") is not None and (age is None or age > rule["max_age"]):
            continue
        if rule.get("min_age") is not None and (age is None or age < rule["min_age"]):
            continue
        matches.append(rule)

    if not matches:
        return {"diagnosis": "No specific match",
                "advice": "Your symptoms do not match a known pattern. Rest, hydrate, monitor your "
                          "health, and see a doctor if you feel worse.",
                "severity": "monitor", "severity_label": SEVERITY_LABEL["monitor"],
                "confidence": 0, "matched_symptoms": [FACTS[f] for f in selected if f in FACTS],
                "fired_rule": None}

    # --- Conflict resolution: most specific rule (most matched conditions) wins.
    #     Ties broken by lower rule id (priority order in the rule base). ---
    matches.sort(key=lambda r: (-len(r["if"]), r["id"]))
    best = matches[0]

    matched_symptoms = [FACTS[f] for f in best["if"] if f in FACTS]
    # Confidence reflects how well-supported the diagnosis is:
    #   - more matched symptoms -> a more specific, more confident match
    #   - extra unexplained symptoms the user selected lower it (noise)
    n = len(best["if"])
    base = {1: 50, 2: 70, 3: 85}.get(n, 95)
    extra = len(selected) - n
    confidence = max(40, base - extra * 10)

    return {
        "diagnosis": best["diagnosis"],
        "advice": best["advice"],
        "severity": best["severity"],
        "severity_label": SEVERITY_LABEL[best["severity"]],
        "confidence": confidence,
        "matched_symptoms": matched_symptoms,
        "fired_rule": best["id"],
    }
