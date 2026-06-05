# ClinIQ Care — Common Illness Expert System

A web-based **rule-based expert system** that suggests possible common illnesses
from a user's symptoms and recommends next steps (self-care, monitor, see a
doctor, or seek urgent care). Built for the *Knowledge Based System (ISP543)*
course and rebuilt here with a **Hugging Face–powered chatbot** on top of the
original rule engine.

> ⚠️ ClinIQ Care provides general guidance only and is **not** a substitute for
> professional medical advice.

## Features

- **Forward-chaining inference engine** over ~30 IF–THEN production rules
  (`rules.py`), covering fever, respiratory, throat, digestive, headache and
  skin/allergy conditions.
- **Specificity-based conflict resolution** — when several rules match, the most
  specific one wins, with a transparent confidence score (an improvement over
  the original ambiguous rule base).
- **Two ways to interact:**
  1. **Guided mode** — login → patient info → pick a category → tick symptoms →
     diagnosis (mirrors the original project flow).
  2. **Chatbot mode** — describe symptoms in plain language; a Hugging Face
     zero-shot model maps your text to known symptoms, then the rule engine
     diagnoses. Falls back to offline keyword matching if no token is set.
- **Safety-net rules** for no symptoms, too many symptoms, and no match.

## Tech stack

- Python 3.10+ / **Flask**
- HTML + CSS (Jinja templates, red & white theme)
- **Hugging Face Inference API** (`facebook/bart-large-mnli` zero-shot
  classification) for the chatbot

## Getting started

```bash
# 1. Clone and enter the project
git clone https://github.com/<your-username>/cliniq-care.git
cd cliniq-care

# 2. Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. (Optional) enable the smart chatbot
cp .env.example .env
# then paste your free Hugging Face token into .env (HF_TOKEN=hf_xxx)

# 4. Run
python app.py
```

Open <http://localhost:5050> in your browser.
(macOS uses port 5000 for AirPlay, so ClinIQ Care defaults to 5050. Override
with `PORT=8000 python app.py` if needed.)

> The chatbot works **without** a token using keyword matching; adding a
> `HF_TOKEN` upgrades it to natural-language understanding.

## Project structure

```
cliniq-care/
├── app.py            # Flask routes (page flow + chatbot API)
├── rules.py          # Facts, rule base, inference engine
├── chatbot.py        # Hugging Face symptom extraction + replies
├── requirements.txt
├── .env.example
├── templates/        # welcome, login, input, category, symptoms, result, chat
└── static/style.css
```

## How the expert system works

1. **Facts** — each symptom or patient attribute is a fact (`F1` = fever, …).
2. **Rules** — each rule is `IF <facts> THEN <diagnosis + advice + severity>`.
3. **Inference** — forward chaining collects every rule whose conditions are a
   subset of the selected symptoms, then conflict resolution picks the most
   specific match and reports a confidence score.

## Testing & validation

The inference engine is validated against 28 automated test cases (one per
diagnosis, plus conflict-resolution, safety-net, confidence and chatbot tests):

```bash
python -m pytest -q
```

The same cases are documented as a human-readable table in
[VALIDATION.md](VALIDATION.md).

## Authors

Original ISP543 group project, rebuilt and extended.

## License

[MIT](LICENSE)
