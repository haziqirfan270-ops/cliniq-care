# ClinIQ Care — Validation

This document records the validation of the ClinIQ Care inference engine against
a set of representative test cases. Every case below is also encoded as an
automated test in [`tests/test_rules.py`](tests/test_rules.py) and runs with:

```bash
python -m pytest -q
```

**Result: 28/28 tests passing.**

## 1. Diagnostic test cases

Each case feeds a set of selected symptoms (and patient age where relevant) to
`diagnose()` and checks the inferred diagnosis and recommended severity.

| # | Symptoms (facts) | Age | Expected diagnosis | Severity | Pass |
|---|------------------|-----|--------------------|----------|------|
| 1 | fever, headache, sore throat, chills (F1,F4,F5,F6) | 30 | Likely Influenza (Flu) | Self-care | ✅ |
| 2 | fever, cough, loss of taste/smell (F1,F7,F8) | 40 | Possible COVID-19 | See doctor | ✅ |
| 3 | fever, headache, body aches (F1,F4,F15) | 25 | Possible Dengue | See doctor | ✅ |
| 4 | fever, headache, chills (F1,F4,F6) | 35 | Possible Malaria | See doctor | ✅ |
| 5 | fever, skin rash, swollen glands (F1,F2,F3) | 10 | Likely Chickenpox (children) | See doctor | ✅ |
| 6 | fever, skin rash, swollen glands (F1,F2,F3) | 30 | Likely Chickenpox (adults) | See doctor | ✅ |
| 7 | fever (F1) | 30 | General Fever | Monitor | ✅ |
| 8 | sneezing, runny nose (F10,F9) | 22 | Likely Common Cold | Self-care | ✅ |
| 9 | cough, fatigue (F7,F17) | 45 | Possible Bronchitis | Self-care | ✅ |
| 10 | cough, shortness of breath (F7,F18) | 50 | Possible Asthma or Bronchitis | See doctor | ✅ |
| 11 | sore throat, white patches (F5,F26) | 18 | Possible Tonsillitis | See doctor | ✅ |
| 12 | sore throat, hoarseness (F5,F27) | 33 | Possible Laryngitis | Self-care | ✅ |
| 13 | sore throat (F5) | 28 | Possible Throat Infection | Self-care | ✅ |
| 14 | nausea, vomiting, diarrhea (F12,F13,F14) | 27 | Likely Food Poisoning | Self-care | ✅ |
| 15 | bloating, constipated (F19,F20) | 60 | Constipation | Self-care | ✅ |
| 16 | abdominal pain, loss of appetite (F21,F22) | 41 | Possible Gastritis | Self-care | ✅ |
| 17 | headache, nausea, light sensitivity (F4,F12,F23) | 29 | Possible Migraine | Self-care | ✅ |
| 18 | headache, stiff neck (F4,F24) | 20 | Possible Meningitis | **Urgent** | ✅ |
| 19 | headache, dizziness (F4,F25) | 38 | Tension Headache | Self-care | ✅ |
| 20 | itchy skin, blisters (F11,F29) | 24 | Possible Scabies | See doctor | ✅ |
| 21 | itchy skin, skin redness (F11,F30) | 31 | Possible Eczema | Self-care | ✅ |
| 22 | itchy skin (F11) | 26 | Normal Itching | Self-care | ✅ |

## 2. Conflict-resolution test

The original rule base had overlapping rules (e.g. the malaria rule
`F1+F4+F6` is a subset of the flu rule `F1+F4+F5+F6`). ClinIQ Care resolves
this by **specificity** — the rule matching the most symptoms wins.

| Symptoms | Competing rules | Expected winner | Pass |
|----------|-----------------|-----------------|------|
| fever, headache, sore throat, chills | #3 Flu (4 facts) vs #6 Malaria (3 facts) | #3 Flu | ✅ |

## 3. Safety-net (edge-case) tests

| Scenario | Input | Expected response | Pass |
|----------|-------|-------------------|------|
| No symptoms | `[]` | "No symptoms selected" prompt | ✅ |
| Too many symptoms | 12 symptoms | "Too many symptoms selected" advice | ✅ |
| No matching rule | bloating alone (F19) | "No specific match" → rest/monitor | ✅ |

## 4. Confidence scoring

Confidence scales with how many symptoms support the diagnosis, so a single
symptom never reports false certainty.

| Input | Matched rule | Confidence | Pass |
|-------|--------------|-----------|------|
| nausea, vomiting, diarrhea (3 symptoms) | #19 Food Poisoning | 85% | ✅ |
| sore throat (1 symptom) | #15 Throat Infection | 50% | ✅ |

## 5. Chatbot symptom extraction

| Free-text message | Extracted facts (offline keyword path) | Pass |
|-------------------|----------------------------------------|------|
| "I have a fever, headache and chills" | F1 (fever), F4 (headache), F6 (chills) | ✅ |

---

*Validation performed against the rule base in `rules.py`. Re-run any time with
`python -m pytest -q`.*
