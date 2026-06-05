"""
ClinIQ Care - Common Illness Expert System (Flask app).

Page flow (mirrors the project report):
    welcome -> login -> patient info -> category -> symptoms -> result
Plus a Hugging Face powered chatbot for free-text symptom description.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify)

from rules import FACTS, CATEGORIES, diagnose
from chatbot import chat_diagnose, reply_text

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cliniq-care-dev-secret")


@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Lightweight, accountless "login" - just a name to personalise the session.
    if request.method == "POST":
        session["user"] = request.form.get("username", "Guest").strip() or "Guest"
        return redirect(url_for("patient_info"))
    return render_template("login.html")


@app.route("/patient", methods=["GET", "POST"])
def patient_info():
    if request.method == "POST":
        session["name"] = request.form.get("name", "").strip()
        try:
            session["age"] = int(request.form.get("age", ""))
        except ValueError:
            session["age"] = None
        session["gender"] = request.form.get("gender", "")
        return redirect(url_for("category"))
    return render_template("input.html")


@app.route("/category")
def category():
    return render_template("category.html", categories=CATEGORIES)


@app.route("/symptoms/<cat>")
def symptoms(cat):
    if cat not in CATEGORIES:
        return redirect(url_for("category"))
    items = [(fid, FACTS[fid]) for fid in CATEGORIES[cat]]
    return render_template("symptoms.html", category=cat, items=items)


@app.route("/diagnose", methods=["POST"])
def do_diagnose():
    selected = request.form.getlist("symptoms")
    result = diagnose(selected, age=session.get("age"))
    return render_template("result.html",
                           result=result,
                           name=session.get("name") or session.get("user", "Guest"),
                           age=session.get("age"),
                           gender=session.get("gender"))


# ----------------------------- Chatbot ------------------------------------
@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"reply": "Please tell me how you are feeling."})
    result = chat_diagnose(message, age=session.get("age"))
    return jsonify({
        "reply": reply_text(result),
        "diagnosis": result["diagnosis"],
        "severity": result["severity"],
        "confidence": result["confidence"],
        "understood": result.get("understood_symptoms", []),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(debug=True, host="0.0.0.0", port=port)
