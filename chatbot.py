"""
ClinIQ Care - Chatbot layer (Hugging Face powered).

The chatbot lets users describe their symptoms in plain language instead of
ticking checkboxes. It maps that free text onto the known FACTS, then hands the
matched symptoms to the rule-based inference engine in rules.py.

Symptom extraction strategy:
  1. Hugging Face zero-shot classification (facebook/bart-large-mnli) via the
     free Inference API - if a HF_TOKEN is configured.
  2. A keyword/synonym fallback so the chatbot still works fully offline.

Set your token in a .env file or the environment:
    HF_TOKEN=hf_xxx
Optionally override the model:
    HF_MODEL=facebook/bart-large-mnli
"""

import os
import requests

from rules import FACTS, diagnose

HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
HF_MODEL = os.environ.get("HF_MODEL", "facebook/bart-large-mnli").strip()
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

# Confidence threshold for accepting a zero-shot label as "present".
ZS_THRESHOLD = 0.55

# Keyword / synonym map used by the offline fallback and to boost the model.
SYNONYMS = {
    "F1":  ["fever", "high temperature", "hot", "temperature", "feverish"],
    "F2":  ["skin rash", "rash on skin", "spots"],
    "F3":  ["swollen glands", "swollen lymph", "swollen neck"],
    "F4":  ["headache", "head ache", "head pain"],
    "F5":  ["sore throat", "throat pain", "painful throat"],
    "F6":  ["chills", "shivering", "shivers", "cold sweats"],
    "F7":  ["cough", "coughing"],
    "F8":  ["loss of taste", "loss of smell", "can't taste", "can't smell", "no taste", "no smell"],
    "F9":  ["runny nose", "running nose", "nose running", "nasal discharge"],
    "F10": ["sneezing", "sneeze"],
    "F11": ["itchy skin", "itching", "itch", "itchy"],
    "F12": ["nausea", "nauseous", "feel sick", "queasy"],
    "F13": ["vomiting", "vomit", "throwing up", "throw up"],
    "F14": ["diarrhea", "diarrhoea", "loose stool", "loose motion"],
    "F15": ["body aches", "body ache", "muscle pain", "aching", "joint pain"],
    "F16": ["chest pain", "chest hurts", "pain in chest"],
    "F17": ["fatigue", "tired", "exhausted", "weak", "no energy"],
    "F18": ["shortness of breath", "short of breath", "breathless", "hard to breathe", "can't breathe"],
    "F19": ["bloating", "bloated"],
    "F20": ["constipated", "constipation"],
    "F21": ["abdominal pain", "stomach pain", "stomach ache", "belly pain", "tummy pain"],
    "F22": ["loss of appetite", "no appetite", "not hungry"],
    "F23": ["light sensitivity", "sensitive to light", "bright light hurts"],
    "F24": ["stiff neck", "neck stiffness", "stiff in neck"],
    "F25": ["dizziness", "dizzy", "lightheaded"],
    "F26": ["white patches in throat", "white spots throat", "white patches"],
    "F27": ["hoarseness", "hoarse", "lost voice", "raspy voice"],
    "F28": ["difficulty swallowing", "hard to swallow", "trouble swallowing", "painful swallowing"],
    "F29": ["blisters", "blister"],
    "F30": ["skin redness", "red skin", "redness"],
    "F31": ["rash", "general rash"],
}


def _extract_with_keywords(text):
    """Offline fallback: match facts by keyword/synonym presence."""
    text_l = text.lower()
    found = []
    for fact_id, words in SYNONYMS.items():
        if any(w in text_l for w in words):
            found.append(fact_id)
    return found


def _extract_with_hf(text):
    """Use Hugging Face zero-shot classification to detect symptoms.

    Returns a list of fact IDs, or None if the API is unavailable so the
    caller can fall back to keywords.
    """
    if not HF_TOKEN:
        return None

    labels = [FACTS[f] for f in FACTS]
    payload = {
        "inputs": text,
        "parameters": {"candidate_labels": labels, "multi_label": True},
    }
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        resp = requests.post(HF_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None

    if not isinstance(data, dict) or "labels" not in data:
        return None

    label_to_fact = {FACTS[f]: f for f in FACTS}
    found = []
    for label, score in zip(data["labels"], data["scores"]):
        if score >= ZS_THRESHOLD and label in label_to_fact:
            found.append(label_to_fact[label])
    return found


def extract_symptoms(text):
    """Map free text to fact IDs, preferring HF, falling back to keywords.

    Keyword hits are always merged in so obvious mentions are never missed.
    """
    facts = set(_extract_with_keywords(text))
    hf = _extract_with_hf(text)
    if hf:
        facts.update(hf)
    return sorted(facts, key=lambda f: int(f[1:]))


def chat_diagnose(text, age=None):
    """Full chatbot turn: understand the message, then run the rule engine."""
    facts = extract_symptoms(text)
    result = diagnose(facts, age=age)
    result["understood_symptoms"] = [FACTS[f] for f in facts]
    result["used_hf"] = bool(HF_TOKEN)
    return result


def reply_text(result):
    """Build a friendly chatbot reply from a diagnosis result."""
    understood = result.get("understood_symptoms", [])
    if not understood:
        return ("I could not pick out any clear symptoms from that. Try describing "
                "how you feel, e.g. \"I have a fever, headache and chills\".")

    lines = [f"I understood these symptoms: {', '.join(understood)}.",
             f"\nMost likely: {result['diagnosis']} "
             f"(confidence ~{result['confidence']}%).",
             f"\nRecommended: {result['severity_label']}.",
             f"\n{result['advice']}",
             "\n\nNote: ClinIQ Care offers general guidance only and does not replace a doctor."]
    return "".join(lines)
