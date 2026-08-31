from flask import Flask, request, session, redirect, url_for, render_template_string
from datetime import datetime, timezone
import sqlite3
import os
import requests

try:
    import psycopg2
except ImportError:
    psycopg2 = None

# ============================================================
# APP SETTINGS
# ============================================================

app = Flask(__name__)

# For testing this is okay.
# Before putting the app online, change SECRET_KEY to a long random value.
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "CHANGE-THIS-TO-A-LONG-RANDOM-SECRET-KEY"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER"))
)

EXAM_TIME = 30 * 60  # 30 minutes

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
DATABASE = os.environ.get("DATABASE_PATH", "cbt_results.db")

# WhatsApp Cloud API settings. Keep these in Render Environment Variables.
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "").strip()
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "").strip()
WHATSAPP_RECIPIENT = os.environ.get("WHATSAPP_RECIPIENT", "").strip()
WHATSAPP_TEMPLATE_NAME = os.environ.get(
    "WHATSAPP_TEMPLATE_NAME",
    "cbt_result_notification"
).strip()
WHATSAPP_TEMPLATE_LANGUAGE = os.environ.get(
    "WHATSAPP_TEMPLATE_LANGUAGE",
    "en_US"
).strip()
WHATSAPP_API_VERSION = os.environ.get(
    "WHATSAPP_API_VERSION",
    "v23.0"
).strip()


# ============================================================
# QUESTIONS
# ============================================================

QUESTIONS = [

    {
        "question": "Which of the following particles has no electrical charge?",
        "options": ["Proton", "Electron", "Neutron", "Positron"],
        "answer": "Neutron"
    },

    {
        "question": "Atoms of the same element having the same atomic number but different mass numbers are called:",
        "options": ["Isobars", "Isotopes", "Isomers", "Allotropes"],
        "answer": "Isotopes"
    },

    {
        "question": "What is the electronic configuration of sodium (atomic number 11)?",
        "options": ["2, 8, 1", "2, 7, 2", "2, 8, 2", "2, 6, 3"],
        "answer": "2, 8, 1"
    },

    {
        "question": "Which of the following elements belongs to Group 1?",
        "options": ["Calcium", "Sodium", "Chlorine", "Aluminium"],
        "answer": "Sodium"
    },

    {
        "question": "Across a period from left to right, atomic radius generally:",
        "options": [
            "Increases",
            "Decreases",
            "Remains constant",
            "First increases then decreases"
        ],
        "answer": "Decreases"
    },

    {
        "question": "A bond formed by the transfer of electrons from one atom to another is called:",
        "options": [
            "Covalent bond",
            "Metallic bond",
            "Ionic bond",
            "Coordinate bond"
        ],
        "answer": "Ionic bond"
    },

    {
        "question": "Which of the following is an ionic compound?",
        "options": ["CH₄", "H₂O", "NaCl", "CO₂"],
        "answer": "NaCl"
    },

    {
        "question": "Which of the following contains only covalent bonds?",
        "options": ["NaCl", "MgO", "CH₄", "KBr"],
        "answer": "CH₄"
    },

    {
        "question": "The attraction between positive metal ions and a sea of delocalised electrons is known as:",
        "options": [
            "Ionic bonding",
            "Covalent bonding",
            "Metallic bonding",
            "Hydrogen bonding"
        ],
        "answer": "Metallic bonding"
    },

    {
        "question": "How many particles are present in one mole of a substance?",
        "options": [
            "6.02 × 10²³",
            "3.01 × 10²³",
            "9.81 × 10²³",
            "1.60 × 10⁻¹⁹"
        ],
        "answer": "6.02 × 10²³"
    },

    {
        "question": "What is the relative molecular mass of water, H₂O? (H = 1, O = 16)",
        "options": ["16", "17", "18", "20"],
        "answer": "18"
    },

    {
        "question": "What is the empirical formula of benzene, C₆H₆?",
        "options": ["CH", "C₂H₂", "C₃H₃", "C₆H₆"],
        "answer": "CH"
    },

    {
        "question": "If the empirical formula of a compound is CH₂O and its relative molecular mass is 180, what is its molecular formula?",
        "options": [
            "CH₂O",
            "C₂H₄O₂",
            "C₆H₁₂O₆",
            "C₁₂H₂₄O₁"
        ],
        "answer": "C₆H₁₂O₆"
    },

    {
        "question": "Which of the following is the correctly balanced equation for the formation of water?",
        "options": [
            "H₂ + O₂ → H₂O",
            "2H₂ + O₂ → 2H₂O",
            "H₂ + 2O₂ → H₂O",
            "2H₂ + 2O₂ → 2H₂O"
        ],
        "answer": "2H₂ + O₂ → 2H₂O"
    },

    {
        "question": "What mass of oxygen is present in 2 moles of O₂? (O = 16)",
        "options": ["16 g", "32 g", "48 g", "64 g"],
        "answer": "64 g"
    },

    {
        "question": "At constant temperature, if the pressure of a fixed mass of gas is increased, its volume will:",
        "options": [
            "Increase",
            "Decrease",
            "Remain constant",
            "Become zero"
        ],
        "answer": "Decrease"
    },

    {
        "question": "According to the kinetic theory, gas particles are in:",
        "options": [
            "Complete rest",
            "Continuous random motion",
            "Fixed positions",
            "Circular motion only"
        ],
        "answer": "Continuous random motion"
    },

    {
        "question": "Which of the following is a strong acid?",
        "options": ["CH₃COOH", "HCl", "H₂CO₃", "H₂O"],
        "answer": "HCl"
    },

    {
        "question": "Which of the following is a base?",
        "options": ["HCl", "H₂SO₄", "NaOH", "CO₂"],
        "answer": "NaOH"
    },

    {
        "question": "Which of the following is a salt?",
        "options": ["HCl", "NaOH", "NaCl", "NH₃"],
        "answer": "NaCl"
    },

    {
        "question": "A solution with a pH of 3 is:",
        "options": [
            "Strongly alkaline",
            "Weakly alkaline",
            "Neutral",
            "Acidic"
        ],
        "answer": "Acidic"
    },

    {
        "question": "The reaction between an acid and a base produces:",
        "options": [
            "Salt and water",
            "Acid and water",
            "Base and hydrogen",
            "Salt and oxygen"
        ],
        "answer": "Salt and water"
    },

    {
        "question": "Which of the following substances is generally insoluble in water?",
        "options": [
            "Sodium chloride",
            "Potassium nitrate",
            "Silver chloride",
            "Ammonium chloride"
        ],
        "answer": "Silver chloride"
    },

    {
        "question": "Which method is used to separate a mixture of ethanol and water?",
        "options": [
            "Filtration",
            "Fractional distillation",
            "Sublimation",
            "Decantation"
        ],
        "answer": "Fractional distillation"
    },

    {
        "question": "The temporary hardness of water is mainly caused by the presence of:",
        "options": [
            "Sodium chloride",
            "Calcium and magnesium hydrogen carbonates",
            "Potassium nitrate",
            "Sodium hydroxide"
        ],
        "answer": "Calcium and magnesium hydrogen carbonates"
    },

    {
        "question": "The most abundant gas in the atmosphere is:",
        "options": [
            "Oxygen",
            "Nitrogen",
            "Carbon dioxide",
            "Hydrogen"
        ],
        "answer": "Nitrogen"
    },

    {
        "question": "When hydrogen burns in oxygen, the product formed is:",
        "options": [
            "Carbon dioxide",
            "Water",
            "Hydrogen peroxide only",
            "Nitrogen dioxide"
        ],
        "answer": "Water"
    },

    {
        "question": "Which gas relights a glowing splint?",
        "options": [
            "Hydrogen",
            "Nitrogen",
            "Oxygen",
            "Carbon dioxide"
        ],
        "answer": "Oxygen"
    },

    {
        "question": "The industrial method used to obtain nitrogen and oxygen from air is:",
        "options": [
            "Filtration",
            "Fractional distillation of liquid air",
            "Evaporation",
            "Chromatography"
        ],
        "answer": "Fractional distillation of liquid air"
    },

    {
        "question": "Chlorine gas is commonly identified by its:",
        "options": [
            "Colourless appearance",
            "Greenish-yellow colour",
            "Blue colour",
            "Black colour"
        ],
        "answer": "Greenish-yellow colour"
    },

    {
        "question": "Which allotrope of carbon is the hardest naturally occurring substance?",
        "options": [
            "Graphite",
            "Diamond",
            "Coke",
            "Charcoal"
        ],
        "answer": "Diamond"
    },

    {
        "question": "Which gas turns limewater milky?",
        "options": [
            "Oxygen",
            "Hydrogen",
            "Carbon dioxide",
            "Nitrogen"
        ],
        "answer": "Carbon dioxide"
    },

    {
        "question": "Organic compounds are mainly compounds containing:",
        "options": [
            "Calcium",
            "Carbon",
            "Sodium",
            "Chlorine"
        ],
        "answer": "Carbon"
    },

    {
        "question": "What is the general formula of alkanes?",
        "options": [
            "CₙH₂ₙ",
            "CₙH₂ₙ₋₂",
            "CₙH₂ₙ₊₂",
            "CₙHₙ"
        ],
        "answer": "CₙH₂ₙ₊₂"
    },

    {
        "question": "Which of the following is an alkene?",
        "options": [
            "Methane",
            "Ethane",
            "Ethene",
            "Propane"
        ],
        "answer": "Ethene"
    },

    {
        "question": "Which of the following is an alkyne?",
        "options": [
            "Ethane",
            "Ethene",
            "Ethyne",
            "Methane"
        ],
        "answer": "Ethyne"
    },

    {
        "question": "What is the functional group of alcohols?",
        "options": [
            "–COOH",
            "–OH",
            "–CHO",
            "–COO–"
        ],
        "answer": "–OH"
    },

    {
        "question": "Which functional group is present in carboxylic acids?",
        "options": [
            "–OH",
            "–COOH",
            "–CHO",
            "–NH₂"
        ],
        "answer": "–COOH"
    },

    {
        "question": "Esters are commonly formed by the reaction between:",
        "options": [
            "An alkane and an alkene",
            "An alcohol and a carboxylic acid",
            "An acid and a metal",
            "An alkene and water"
        ],
        "answer": "An alcohol and a carboxylic acid"
    },

    {
        "question": "The process by which many small molecules join together to form a polymer is called:",
        "options": [
            "Hydrolysis",
            "Polymerisation",
            "Neutralisation",
            "Combustion"
        ],
        "answer": "Polymerisation"
    },

    {
        "question": "The main method used to separate crude oil into useful fractions is:",
        "options": [
            "Filtration",
            "Fractional distillation",
            "Sublimation",
            "Crystallisation"
        ],
        "answer": "Fractional distillation"
    },

    {
        "question": "Which of the following will generally increase the rate of a reaction?",
        "options": [
            "Lowering the temperature",
            "Decreasing concentration",
            "Increasing temperature",
            "Removing the reactants"
        ],
        "answer": "Increasing temperature"
    },

    {
        "question": "At chemical equilibrium, the rates of the forward and reverse reactions are:",
        "options": [
            "Zero",
            "Equal",
            "Unequal",
            "Constantly increasing"
        ],
        "answer": "Equal"
    },

    {
        "question": "Reduction involves:",
        "options": [
            "Loss of electrons",
            "Gain of electrons",
            "Loss of neutrons",
            "Gain of oxygen only"
        ],
        "answer": "Gain of electrons"
    },

    {
        "question": "During electrolysis, positively charged ions move towards the:",
        "options": [
            "Anode",
            "Cathode",
            "Electrolyte",
            "Salt bridge"
        ],
        "answer": "Cathode"
    },

    {
        "question": "In a simple electrochemical cell, chemical energy is converted into:",
        "options": [
            "Heat energy only",
            "Electrical energy",
            "Light energy",
            "Sound energy"
        ],
        "answer": "Electrical energy"
    },

    {
        "question": "Which metal is commonly extracted from its ore by electrolysis?",
        "options": [
            "Aluminium",
            "Iron",
            "Copper",
            "Lead"
        ],
        "answer": "Aluminium"
    },

    {
        "question": "The rusting of iron requires:",
        "options": [
            "Nitrogen only",
            "Oxygen and water",
            "Carbon dioxide only",
            "Hydrogen and chlorine"
        ],
        "answer": "Oxygen and water"
    },

    {
        "question": "Which of the following is a nitrogenous fertilizer?",
        "options": [
            "Urea",
            "Sodium chloride",
            "Calcium carbonate",
            "Sand"
        ],
        "answer": "Urea"
    },

    {
        "question": "Which gas is a major contributor to the greenhouse effect?",
        "options": [
            "Carbon dioxide",
            "Nitrogen",
            "Hydrogen",
            "Helium"
        ],
        "answer": "Carbon dioxide"
    }
]


# ============================================================
# DATABASE
# ============================================================

def using_postgres():
    return bool(DATABASE_URL)


def get_db():
    """Use Render PostgreSQL online; use SQLite locally if DATABASE_URL is absent."""
    if DATABASE_URL:
        if psycopg2 is None:
            raise RuntimeError(
                "psycopg2-binary is required when DATABASE_URL is set."
            )
        return psycopg2.connect(DATABASE_URL)

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_db()

    if using_postgres():
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id SERIAL PRIMARY KEY,
                student_name TEXT NOT NULL,
                login_at TEXT NOT NULL,
                submitted_at TEXT,
                score INTEGER,
                total_questions INTEGER,
                percentage REAL,
                time_used INTEGER,
                submission_type TEXT
            )
        """)
    else:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                login_at TEXT NOT NULL,
                submitted_at TEXT,
                score INTEGER,
                total_questions INTEGER,
                percentage REAL,
                time_used INTEGER,
                submission_type TEXT
            )
        """)

    connection.commit()
    connection.close()


def create_attempt(student_name):
    login_at = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    connection = get_db()

    if using_postgres():
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO attempts (student_name, login_at)
            VALUES (%s, %s)
            RETURNING id
            """,
            (student_name, login_at)
        )
        attempt_id = cursor.fetchone()[0]
    else:
        cursor = connection.execute(
            """
            INSERT INTO attempts (student_name, login_at)
            VALUES (?, ?)
            """,
            (student_name, login_at)
        )
        attempt_id = cursor.lastrowid

    connection.commit()
    connection.close()
    return attempt_id, login_at


def save_attempt_result(
    attempt_id,
    score,
    total,
    percentage,
    time_used,
    submitted_at,
    submission_type
):
    connection = get_db()

    if using_postgres():
        connection.cursor().execute(
            """
            UPDATE attempts
            SET submitted_at = %s,
                score = %s,
                total_questions = %s,
                percentage = %s,
                time_used = %s,
                submission_type = %s
            WHERE id = %s
            """,
            (
                submitted_at,
                score,
                total,
                percentage,
                time_used,
                submission_type,
                attempt_id
            )
        )
    else:
        connection.execute(
            """
            UPDATE attempts
            SET submitted_at = ?,
                score = ?,
                total_questions = ?,
                percentage = ?,
                time_used = ?,
                submission_type = ?
            WHERE id = ?
            """,
            (
                submitted_at,
                score,
                total,
                percentage,
                time_used,
                submission_type,
                attempt_id
            )
        )

    connection.commit()
    connection.close()


def send_whatsapp_notification(
    student_name,
    score,
    total,
    percentage,
    login_at,
    submitted_at,
    time_used,
    submission_type
):
    """
    Send a WhatsApp template message to the administrator.
    It stays disabled until the WhatsApp environment variables are set.
    """
    if not (
        WHATSAPP_ACCESS_TOKEN
        and WHATSAPP_PHONE_NUMBER_ID
        and WHATSAPP_RECIPIENT
    ):
        print(
            "WhatsApp notification skipped: "
            "WhatsApp environment variables are not configured."
        )
        return

    url = (
        f"https://graph.facebook.com/"
        f"{WHATSAPP_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    submission_label = (
        "Automatic (time expired)"
        if submission_type == "automatic"
        else "Manual"
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": WHATSAPP_RECIPIENT,
        "type": "template",
        "template": {
            "name": WHATSAPP_TEMPLATE_NAME,
            "language": {
                "code": WHATSAPP_TEMPLATE_LANGUAGE
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": student_name},
                        {"type": "text", "text": f"{score}/{total}"},
                        {"type": "text", "text": f"{percentage:.1f}%"},
                        {"type": "text", "text": login_at},
                        {"type": "text", "text": submitted_at},
                        {"type": "text", "text": time_used},
                        {"type": "text", "text": submission_label}
                    ]
                }
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.ok:
            print("WhatsApp notification sent successfully.")
        else:
            print(
                "WhatsApp notification failed:",
                response.status_code,
                response.text
            )

    except Exception as error:
        # Never prevent the student's result from being saved.
        print("WhatsApp notification error:", error)


# ============================================================
# TIME
# ============================================================

def current_timestamp():

    return datetime.now(
        timezone.utc
    ).timestamp()


def format_time(seconds):

    minutes = seconds // 60
    seconds = seconds % 60

    return f"{minutes:02d}:{seconds:02d}"


# ============================================================
# CSS
# ============================================================

CSS = """

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background: #f4f6f9;

    color: #222;
}


.topbar {

    background: white;

    padding: 15px 5%;

    display: flex;

    justify-content: space-between;

    align-items: center;

    box-shadow:
        0 2px 10px rgba(0,0,0,0.08);

    position: sticky;

    top: 0;

    z-index: 10;
}


.logo-title {

    font-size: 20px;

    font-weight: bold;
}


.student {

    color: #666;

    margin-top: 4px;

    font-size: 14px;
}


.timer {

    color: #c62828;

    font-size: 22px;

    font-weight: bold;
}


.container {

    max-width: 900px;

    margin: 30px auto;

    padding: 0 20px;
}


.card {

    background: white;

    border-radius: 16px;

    padding: 30px;

    box-shadow:
        0 8px 25px rgba(0,0,0,0.07);
}


.center {

    min-height: 100vh;

    display: flex;

    align-items: center;

    justify-content: center;

    padding: 20px;
}


.login-card {

    width: 100%;

    max-width: 500px;

    text-align: center;
}


.logo {

    font-size: 55px;

    margin-bottom: 5px;
}


h1 {

    margin-top: 5px;

    margin-bottom: 10px;
}


.muted {

    color: #666;
}


input[type="text"] {

    width: 100%;

    padding: 14px;

    border:
        1px solid #ccc;

    border-radius: 9px;

    font-size: 16px;

    margin-top: 8px;
}


.primary,
.secondary,
.danger {

    border: none;

    border-radius: 9px;

    padding: 12px 20px;

    font-size: 15px;

    font-weight: bold;

    cursor: pointer;
}


.primary {

    background: #1976d2;

    color: white;
}


.secondary {

    background: #757575;

    color: white;
}


.danger {

    background: #c62828;

    color: white;
}


.full {

    width: 100%;

    margin-top: 20px;
}


.exam-info {

    margin-top: 25px;

    color: #555;
}


.notice {

    background: #e8f1ff;

    border-left:
        4px solid #1976d2;

    padding: 13px;

    border-radius: 8px;

    margin-bottom: 20px;
}


.warning {

    background: #fff3cd;

    color: #664d03;

    border-left:
        4px solid #ff9800;
}


.question-number {

    color: #666;

    font-weight: bold;

    margin-bottom: 15px;
}


.question {

    font-size: 21px;

    line-height: 1.5;

    margin-bottom: 25px;
}


.option {

    display: block;

    padding: 15px;

    border:
        1px solid #ddd;

    border-radius: 10px;

    margin-bottom: 12px;

    cursor: pointer;

    transition: 0.15s;
}


.option:hover {

    background: #f5f8fc;

    border-color: #1976d2;
}


.option input {

    margin-right: 12px;

    transform: scale(1.2);
}


.navigation {

    margin-top: 25px;

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 10px;

    flex-wrap: wrap;
}


.counter {

    font-weight: bold;

    margin: 0 10px;
}


button:disabled {

    opacity: 0.45;

    cursor: not-allowed;
}


.alert {

    background: #fff3cd;

    color: #664d03;

    padding: 12px;

    border-radius: 8px;

    margin: 15px 0;
}


.result {

    text-align: center;

    max-width: 550px;
}


.success {

    font-size: 60px;
}


.score {

    font-size: 60px;

    font-weight: bold;

    margin: 15px 0;
}


.percentage {

    font-size: 30px;

    font-weight: bold;
}


.result-info {

    margin-top: 25px;

    border-top:
        1px solid #ddd;

    border-bottom:
        1px solid #ddd;

    padding: 15px;
}


.result-row {

    display: flex;

    justify-content: space-between;

    padding: 8px 0;
}


@media(max-width:600px) {

    .topbar {

        padding: 12px 4%;
    }

    .timer {

        font-size: 18px;
    }

    .container {

        padding: 0 12px;
    }

    .card {

        padding: 20px;
    }

    .question {

        font-size: 18px;
    }

    .navigation button {

        flex: 1;

        min-width: 100px;
    }

    .counter {

        width: 100%;

        order: -1;

        text-align: center;
    }
}

"""


# ============================================================
# LOGIN PAGE
# ============================================================

LOGIN_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Chemistry CBT</title>

<style>

{{ css }}

</style>

</head>


<body>


<div class="center">


<div class="card login-card">


<div class="logo">
    🧪
</div>


<h1>
    Chemistry CBT
</h1>


<p class="muted">
    Welcome to the Chemistry Computer Based Test.
</p>


{% if error %}

<div class="alert">

{{ error }}

</div>

{% endif %}


<form method="POST">


<label>

<strong>
    Full Name
</strong>


<input
    type="text"
    name="student_name"
    placeholder="Enter your full name"
    maxlength="100"
    required
    autofocus
>


</label>


<button
    class="primary full"
    type="submit"
>

Start Examination

</button>


</form>


<div class="exam-info">

<strong>
    50 Questions
</strong>

&nbsp; • &nbsp;

<strong>
    30 Minutes
</strong>

</div>


</div>


</div>


</body>

</html>

"""


# ============================================================
# EXAM PAGE
# ============================================================

EXAM_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
    Chemistry CBT
</title>


<style>

{{ css }}

</style>

</head>


<body>


<header class="topbar">


<div>

<div class="logo-title">
    🧪 Chemistry CBT
</div>


<div class="student">

Student:
<strong>
    {{ student_name }}
</strong>

</div>

</div>


<div
    id="timer"
    class="timer"
>

30:00

</div>


</header>


<main class="container">


<div
    id="notice"
    class="notice"
>

Read each question carefully before selecting your answer.

</div>


<div class="card">


<div
    id="question-number"
    class="question-number"
>

Question 1 of 50

</div>


<div
    id="question"
    class="question"
>

</div>


<div id="options">

</div>


<div class="navigation">


<button
    type="button"
    id="previous"
    class="secondary"
>

Previous

</button>


<span
    id="counter"
    class="counter"
>

Question 1 of 50

</span>


<button
    type="button"
    id="next"
    class="primary"
>

Next

</button>


<button
    type="button"
    id="submit"
    class="danger"
>

Submit Exam

</button>


</div>


</div>


</main>


<script>


const questions = {{ questions | tojson }};


let currentQuestion = 0;


let answers = {};


let timeLeft = {{ remaining }};


let examSubmitted = false;


const questionElement =
    document.getElementById("question");


const optionsElement =
    document.getElementById("options");


const questionNumberElement =
    document.getElementById("question-number");


const counterElement =
    document.getElementById("counter");


const timerElement =
    document.getElementById("timer");


const noticeElement =
    document.getElementById("notice");


const previousButton =
    document.getElementById("previous");


const nextButton =
    document.getElementById("next");


const submitButton =
    document.getElementById("submit");



function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}



function saveCurrentAnswer() {

    const selected =
        document.querySelector(
            'input[name="answer"]:checked'
        );


    if (selected) {

        answers[currentQuestion] =
            selected.value;

    }

}



function displayQuestion() {

    const q =
        questions[currentQuestion];


    questionNumberElement.textContent =
        "Question " +
        (currentQuestion + 1) +
        " of " +
        questions.length;


    counterElement.textContent =
        "Question " +
        (currentQuestion + 1) +
        " of " +
        questions.length;


    questionElement.innerHTML =
        escapeHTML(q.question);


    optionsElement.innerHTML = "";


    q.options.forEach(
        function(option, index) {


            const label =
                document.createElement("label");


            label.className =
                "option";


            const radio =
                document.createElement("input");


            radio.type =
                "radio";


            radio.name =
                "answer";


            radio.value =
                option;


            if (
                answers[currentQuestion]
                === option
            ) {

                radio.checked = true;

            }


            const text =
                document.createElement("span");


            text.textContent =
                String.fromCharCode(65 + index)
                + ". "
                + option;


            label.appendChild(radio);

            label.appendChild(text);


            optionsElement.appendChild(label);

        }
    );


    previousButton.disabled =
        currentQuestion === 0;


    if (
        currentQuestion
        === questions.length - 1
    ) {

        nextButton.style.display =
            "none";

    } else {

        nextButton.style.display =
            "inline-block";

    }

}



previousButton.addEventListener(
    "click",
    function() {

        saveCurrentAnswer();

        if (currentQuestion > 0) {

            currentQuestion--;

            displayQuestion();

        }

    }
);



nextButton.addEventListener(
    "click",
    function() {

        saveCurrentAnswer();

        if (
            currentQuestion
            < questions.length - 1
        ) {

            currentQuestion++;

            displayQuestion();

        }

    }
);



function submitExam(autoSubmit = false) {

    if (examSubmitted) {

        return;

    }


    saveCurrentAnswer();


    if (!autoSubmit) {

        const confirmed =
            confirm(
                "Are you sure you want to submit your examination?"
            );


        if (!confirmed) {

            return;

        }

    }


    examSubmitted = true;


    const form =
        document.createElement("form");


    form.method =
        "POST";


    form.action =
        "{{ url_for('submit_exam') }}";


    Object.keys(answers).forEach(
        function(index) {

            const input =
                document.createElement("input");


            input.type =
                "hidden";


            input.name =
                "q_" + index;


            input.value =
                answers[index];


            form.appendChild(input);

        }
    );


    if (autoSubmit) {

        const auto =
            document.createElement("input");


        auto.type =
            "hidden";


        auto.name =
            "auto_submit";


        auto.value =
            "1";


        form.appendChild(auto);

    }


    document.body.appendChild(form);


    form.submit();

}



submitButton.addEventListener(
    "click",
    function() {

        submitExam(false);

    }
);



function formatTime(seconds) {

    const minutes =
        Math.floor(seconds / 60);


    const secondsPart =
        seconds % 60;


    return String(minutes)
        .padStart(2, "0")
        + ":"
        + String(secondsPart)
        .padStart(2, "0");

}



function updateTimer() {

    timerElement.textContent =
        formatTime(timeLeft);


    if (timeLeft === 20 * 60) {

        noticeElement.textContent =
            "🔔 You have 20 minutes remaining.";

        noticeElement.className =
            "notice warning";

    }


    if (timeLeft === 10 * 60) {

        noticeElement.textContent =
            "⚠️ You have 10 minutes remaining.";

        noticeElement.className =
            "notice warning";

    }


    if (timeLeft === 5 * 60) {

        noticeElement.textContent =
            "⚠️ You have 5 minutes remaining.";

        noticeElement.className =
            "notice warning";

    }


    if (timeLeft <= 0) {

        submitExam(true);

        return;

    }


    timeLeft--;

    setTimeout(
        updateTimer,
        1000
    );

}



displayQuestion();


updateTimer();


</script>


</body>

</html>

"""


# ============================================================
# RESULT PAGE
# ============================================================

RESULT_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
    Chemistry CBT Result
</title>


<style>

{{ css }}

</style>

</head>


<body>


<div class="center">


<div class="card result">


<div class="success">

✓

</div>


<h1>

{% if auto_submit %}

Time Up!

{% else %}

Exam Finished

{% endif %}

</h1>


<p>

Well done,

<strong>
    {{ student_name }}
</strong>

</p>


{% if auto_submit %}

<div class="alert">

Your examination was submitted automatically because your time expired.

</div>

{% endif %}


<div class="score">

{{ score }}/{{ total }}

</div>


<div class="percentage">

{{ percentage }}%

</div>


<div class="result-info">


<div class="result-row">

<span>
    Time Used
</span>

<strong>
    {{ time_used }}
</strong>

</div>


<div class="result-row">

<span>
    Status
</span>

<strong>
    Submitted
</strong>

</div>


<div class="result-row">

<span>
    Login Time
</span>

<strong>
    {{ login_at }}
</strong>

</div>


<div class="result-row">

<span>
    Submission Time
</span>

<strong>
    {{ submitted_at }}
</strong>

</div>


</div>


<p class="muted">

Your result has been recorded.

</p>


</div>


</div>


</body>

</html>

"""


# ============================================================
# LOGIN
# ============================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        student_name = request.form.get(
            "student_name",
            ""
        ).strip()
        if not student_name:

            return render_template_string(
                LOGIN_HTML,
                css=CSS,
                error="Please enter your full name."
            )


        session.clear()


        session["student_name"] = student_name

        # Record the student's login immediately.
        attempt_id, login_at = create_attempt(student_name)
        session["attempt_id"] = attempt_id
        session["login_at"] = login_at

        session["started_at"] = current_timestamp()


        return redirect(
            url_for("exam")
        )


    return render_template_string(
        LOGIN_HTML,
        css=CSS,
        error=None
    )


# ============================================================
# EXAM
# ============================================================

@app.route("/exam")
def exam():

    if "student_name" not in session:

        return redirect(
            url_for("login")
        )


    started_at = session.get(
            "started_at"
        )


    if not started_at:

        return redirect(
            url_for("login")
        )


    elapsed = int(
            current_timestamp()
            - started_at
        )


    remaining = max(
            0,
            EXAM_TIME - elapsed
        )


    if remaining <= 0:

        return redirect(
            url_for(
                "submit_exam",
                auto="1"
            )
        )


    return render_template_string(
        EXAM_HTML,

        css=CSS,

        questions=QUESTIONS,

        student_name=
            session["student_name"],

        remaining=remaining
    )


# ============================================================
# SUBMIT EXAM
# ============================================================

@app.route(
    "/submit",
    methods=["POST", "GET"]
)
def submit_exam():

    if "student_name" not in session:

        return redirect(
            url_for("login")
        )


    student_name =  session["student_name"]


    answers = {}


    # ----------------------------------------
    # MANUAL SUBMISSION
    # ----------------------------------------

    if request.method == "POST":

        for key, value in request.form.items():

            if key.startswith("q_"):

                question_index = key.replace(
                        "q_",
                        ""
                    )

                answers[question_index] = value


    # ----------------------------------------
    # AUTOMATIC SUBMISSION
    # ----------------------------------------

    auto_submit = request.args.get("auto") == "1"


    if request.method == "POST":

        auto_submit = request.form.get(
                "auto_submit"
            ) == "1"


    # ----------------------------------------
    # CALCULATE TIME
    # ----------------------------------------

    started_at = session.get(
            "started_at"
        )


    elapsed =  int( current_timestamp()
            - started_at
        )


    time_used = min(
            EXAM_TIME,
            max(0, elapsed)
        )


    # ----------------------------------------
    # CALCULATE SCORE
    # ----------------------------------------

    score = 0


    for index, question in enumerate(QUESTIONS):

        selected_answer = answers.get(
                str(index)
            )


        if selected_answer == question["answer"]:

            score += 1


    total = len(QUESTIONS)


    percentage = round(
            (score / total) * 100,
            1
        )


    # ----------------------------------------
    # SAVE RESULT
    # ----------------------------------------

    submitted_at = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    submission_type = (
        "automatic"
        if auto_submit
        else "manual"
    )

    attempt_id = session.get("attempt_id")

    if attempt_id:
        save_attempt_result(
            attempt_id=attempt_id,
            score=score,
            total=total,
            percentage=percentage,
            time_used=time_used,
            submitted_at=submitted_at,
            submission_type=submission_type
        )

    # Notify the administrator after the result is safely saved.
    send_whatsapp_notification(
        student_name=student_name,
        score=score,
        total=total,
        percentage=percentage,
        login_at=session.get("login_at", ""),
        submitted_at=submitted_at,
        time_used=format_time(time_used),
        submission_type=submission_type
    )

    # ----------------------------------------
    # STORE RESULT IN SESSION
    # ----------------------------------------

    session["result"] = {

        "score":
            score,

        "total":
            total,

        "percentage":
            percentage,

        "time_used":
            format_time(time_used),

        "submitted_at":
            submitted_at,

        "login_at":
            session.get("login_at", ""),

        "auto_submit":
            auto_submit
    }


    # Remove exam start time so the exam
    # cannot be submitted again.

    session.pop(
        "started_at",
        None
    )


    return redirect(
        url_for("result")
    )


# ============================================================
# RESULT
# ============================================================

@app.route("/result")
def result():

    if (
        "student_name"
        not in session
        or
        "result"
        not in session
    ):

        return redirect(
            url_for("login")
        )


    result_data = session["result"]


    return render_template_string(

        RESULT_HTML,

        css=CSS,

        student_name=
            session["student_name"],

        **result_data
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return "CBT is running successfully."


# ============================================================
# START APPLICATION
# ============================================================

# Initialize the database when Gunicorn imports this module on Render.
create_database()


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.environ.get("FLASK_DEBUG", "0") == "1"
    )
