"""
ITR Learn & Simulate
app.py — Main Flask Application

Educational ITR Training and Simulation Platform.
NOT the official Income Tax Department portal.

Architecture:
  User → HTML/JS → Flask Route → Validation →
  Decision Tree / Rule-Based Logic →
  Tax Calculation → SQLite → HTML Response

Gemini AI is used ONLY for explanations, NOT for tax calculations.
"""

import os
import json
import sqlite3
import secrets
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(_env_path, override=True)
except ImportError:
    pass

from flask import (
    Flask, render_template, request,
    redirect, url_for, session,
    jsonify, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

# Tax calculation engine (DO NOT MODIFY)
from tax_engine.calculator import calculate_income_tax

# Decision Tree algorithm
from logic.decision_tree import (
    select_itr_form,
    determine_residential_status,
    classify_income_source,
    check_deduction_eligibility,
    classify_practice_scenario
)

# Rule-Based Logic
from logic.tax_rules import (
    get_slab_display_data,
    get_deduction_rules,
    get_regime_comparison,
    get_itr_forms,
    get_important_dates,
    get_supported_years
)

# Validation
from logic.validation import (
    validate_income_fields,
    validate_deduction_fields,
    check_simulation_completeness
)


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "itr-learn-simulate-2026-secret-key-change-in-production"
)

DATABASE_PATH = os.path.join(
    os.path.dirname(__file__),
    "itr_database.db"
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    """Open a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Create all database tables if they don't exist.
    Safe to call on every startup (IF NOT EXISTS).
    """

    conn = get_db()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            pan TEXT,
            phone TEXT,
            password TEXT NOT NULL,
            is_verified INTEGER DEFAULT 1,
            security_question TEXT,
            security_answer TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration check for existing users table
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [c[1] for c in cursor.fetchall()]
    if "pan" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN pan TEXT")
    if "is_verified" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 1")
    if "security_question" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN security_question TEXT")
    if "security_answer" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN security_answer TEXT")

    # Email OTPs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS email_otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            purpose TEXT DEFAULT 'register',
            expires_at REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Training progress table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS training_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, lesson_id)
        )
    """)

    # Simulations / drafts table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS simulations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            financial_year TEXT DEFAULT 'FY2025-26',
            regime TEXT DEFAULT 'new',
            current_step INTEGER DEFAULT 1,
            total_steps INTEGER DEFAULT 13,
            status TEXT DEFAULT 'draft',
            simulation_data TEXT,
            tax_result TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# PYTHON-BASED FREE EMAIL OTP SYSTEM
# ============================================================

def generate_otp() -> str:
    """Generate a cryptographically secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"


def send_email_otp(recipient_email: str, otp: str, purpose: str = "register") -> dict:
    """
    Send OTP via Python's standard smtplib/email library (100% free, no paid SMS/APIs).
    If SMTP credentials are provided in .env, sends a real HTML email.
    If SMTP is not configured or fails, logs to console and returns dev info so
    academic testing and evaluation never encounter blockers.
    """
    purpose_label = "Account Verification" if purpose == "register" else "Account Login"
    subject = f"{otp} is your verification code for ITR Learn & Simulate"
    
    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 500px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="display: inline-block; background: #1e3a8a; color: #ffffff; font-weight: 800; font-size: 16px; padding: 6px 12px; border-radius: 6px; letter-spacing: 1px;">ITR</div>
            <h2 style="color: #0f172a; margin: 12px 0 4px 0; font-size: 20px;">ITR Learn &amp; Simulate</h2>
            <p style="color: #64748b; font-size: 13px; margin: 0;">AI-Integrated Income Tax Return Training Platform</p>
        </div>
        <div style="border-top: 1px solid #f1f5f9; padding-top: 16px;">
            <p style="color: #334155; font-size: 14px; margin-bottom: 12px;">Hello,</p>
            <p style="color: #334155; font-size: 14px; line-height: 1.5; margin-bottom: 16px;">
                Use the following One-Time Password (OTP) for your <strong>{purpose_label}</strong>:
            </p>
            <div style="background: #f8fafc; border: 1.5px dashed #cbd5e1; border-radius: 10px; padding: 16px; text-align: center; margin: 20px 0;">
                <span style="font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #1e3a8a; font-family: monospace;">{otp}</span>
            </div>
            <p style="color: #64748b; font-size: 12.5px; line-height: 1.5;">
                This OTP is valid for <strong>10 minutes</strong>. Do not share this code with anyone.
            </p>
        </div>
        <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #f1f5f9; text-align: center;">
            <p style="color: #94a3b8; font-size: 11px; margin: 0;">
                Educational Simulation Platform &bull; MCA Academic Project
            </p>
        </div>
    </div>
    """

    expires_at = time.time() + 600  # 10 minutes
    conn = get_db()
    conn.execute(
        "INSERT INTO email_otps (email, otp, purpose, expires_at) VALUES (?, ?, ?, ?)",
        (recipient_email.lower(), otp, purpose, expires_at)
    )
    conn.commit()
    conn.close()

    print(f"\n========================================================")
    print(f" [FREE PYTHON EMAIL OTP] Purpose: {purpose_label}")
    print(f" To: {recipient_email}")
    print(f" OTP Code: >>> {otp} <<< (Expires in 10 mins)")
    print(f"========================================================\n")

    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_email = os.environ.get("SMTP_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))

    if smtp_server and smtp_email and smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"ITR Learn & Simulate <{smtp_email}>"
            msg["To"] = recipient_email
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_email, smtp_password)
                server.send_message(msg)
            return {"sent": True, "method": "smtp", "otp": otp}
        except Exception as e:
            print(f"[SMTP Warning] Could not send via SMTP ({e}). Fallback to dev mode.")
            return {"sent": False, "method": "dev", "otp": otp, "error": str(e)}

    return {"sent": False, "method": "dev", "otp": otp}


# ============================================================
# HELPER: LOGIN REQUIRED & DEMO USER
# ============================================================

def ensure_demo_user():
    """Ensure a default demo user exists for seamless evaluation."""
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = 'demo@itr-simulation.edu'"
    ).fetchone()
    if not user:
        conn.execute(
            "INSERT INTO users (name, email, pan, phone, password, is_verified) VALUES (?, ?, ?, ?, ?, 1)",
            ("Demo Student", "demo@itr-simulation.edu", "ABCDE1234F", "", generate_password_hash("demo1234"))
        )
        conn.commit()
        user = conn.execute(
            "SELECT * FROM users WHERE email = 'demo@itr-simulation.edu'"
        ).fetchone()
    conn.close()
    return user


def login_required(f):
    """
    Decorator to require login for a route.
    If no user session is active, redirects to login page.
    """
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def get_current_user():
    """Return current user's DB row or None."""
    if "user_id" not in session:
        return None
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    conn.close()
    return user


def get_user_stats(user_id):
    """Return training and simulation stats for a user."""
    conn = get_db()

    lessons_completed = conn.execute(
        "SELECT COUNT(*) as cnt FROM training_progress "
        "WHERE user_id = ? AND completed = 1",
        (user_id,)
    ).fetchone()["cnt"]

    sims_total = conn.execute(
        "SELECT COUNT(*) as cnt FROM simulations WHERE user_id = ?",
        (user_id,)
    ).fetchone()["cnt"]

    sims_completed = conn.execute(
        "SELECT COUNT(*) as cnt FROM simulations "
        "WHERE user_id = ? AND status = 'completed'",
        (user_id,)
    ).fetchone()["cnt"]

    drafts = conn.execute(
        "SELECT COUNT(*) as cnt FROM simulations "
        "WHERE user_id = ? AND status = 'draft'",
        (user_id,)
    ).fetchone()["cnt"]

    conn.close()

    total_lessons = 22

    return {
        "lessons_completed": lessons_completed,
        "total_lessons": total_lessons,
        "training_pct": round(
            (lessons_completed / total_lessons) * 100
        ) if total_lessons else 0,
        "sims_total": sims_total,
        "sims_completed": sims_completed,
        "drafts": drafts
    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# REGISTER & EMAIL OTP VERIFICATION
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    message = None

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name             = request.form.get("name", "").strip()
        email            = request.form.get("email", "").strip().lower()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        sec_question     = request.form.get("security_question", "").strip()
        sec_answer       = request.form.get("security_answer", "").strip().lower()

        def re_render(msg):
            return render_template(
                "register.html", message=msg,
                name=name, email=email,
                security_question=sec_question
            )

        if not name or not email or not password or not confirm_password:
            return re_render("Please fill all required fields.")

        if password != confirm_password:
            return re_render("Passwords do not match. Please re-enter.")

        # Password strength: minimum 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special
        import re as _re
        pw_errors = []
        if len(password) < 8:
            pw_errors.append("at least 8 characters")
        if not _re.search(r"[A-Z]", password):
            pw_errors.append("one uppercase letter")
        if not _re.search(r"[a-z]", password):
            pw_errors.append("one lowercase letter")
        if not _re.search(r"\d", password):
            pw_errors.append("one digit")
        if not _re.search(r"[^A-Za-z0-9]", password):
            pw_errors.append("one special character (!@#$...)")
        if pw_errors:
            return re_render("Password must include: " + ", ".join(pw_errors) + ".")

        if not sec_question or not sec_answer:
            return re_render("Please choose a security question and provide an answer (used for password recovery).")

        # Check if email already registered
        conn = get_db()
        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ? AND (is_verified = 1 OR is_verified IS NULL)",
            (email,)
        ).fetchone()
        conn.close()

        if existing_user:
            return re_render("This email is already registered. Please log in instead.")

        # Generate & send Free Python Email OTP
        otp = generate_otp()
        send_res = send_email_otp(email, otp, purpose="register")

        # Save pending registration in session (no PAN stored)
        session["pending_reg"] = {
            "name":              name,
            "email":             email,
            "password":          generate_password_hash(password),
            "security_question": sec_question,
            "security_answer":   generate_password_hash(sec_answer),
            "created_at":        time.time()
        }
        session["pending_otp_info"] = {
            "email":   email,
            "dev_otp": otp if not send_res.get("sent") else None,
            "purpose": "register"
        }

        if send_res.get("sent"):
            flash(f"A 6-digit verification code was sent to {email}. Please check your inbox.", "success")
        else:
            flash(f"Verification code generated for {email}. (Dev/Evaluation OTP: {otp})", "info")

        return redirect(url_for("verify_otp"))

    return render_template("register.html", message=message)




@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    pending_reg = session.get("pending_reg")
    pending_otp_info = session.get("pending_otp_info")

    if not pending_reg or not pending_otp_info:
        flash("No pending registration found. Please register first.", "warning")
        return redirect(url_for("register"))

    message = None
    email = pending_reg.get("email")
    dev_otp = pending_otp_info.get("dev_otp")

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()

        if not entered_otp:
            message = "Please enter the 6-digit verification code."
            return render_template("verify_otp.html", email=email, dev_otp=dev_otp, message=message)

        conn = get_db()
        # Check matching active OTP
        record = conn.execute(
            "SELECT * FROM email_otps WHERE email = ? AND otp = ? AND purpose = 'register' AND expires_at > ? ORDER BY id DESC LIMIT 1",
            (email.lower(), entered_otp, time.time())
        ).fetchone()

        if record:
            try:
                # Remove unverified stale records
                conn.execute("DELETE FROM users WHERE email = ? AND is_verified = 0", (email,))
                cur = conn.execute(
                    "INSERT INTO users (name, email, password, is_verified, security_question, security_answer) VALUES (?, ?, ?, 1, ?, ?)",
                    (
                        pending_reg["name"],
                        email,
                        pending_reg["password"],
                        pending_reg.get("security_question", ""),
                        pending_reg.get("security_answer", "")
                    )
                )
                conn.commit()
                user_id = cur.lastrowid

                # Delete used OTPs
                conn.execute("DELETE FROM email_otps WHERE email = ?", (email,))
                conn.commit()
                conn.close()

                # Clean up session & log user in
                session.pop("pending_reg", None)
                session.pop("pending_otp_info", None)
                session["user_id"] = user_id
                session["user_name"] = pending_reg["name"]

                flash(f"Welcome, {pending_reg['name']}! Your account has been verified successfully.", "success")
                return redirect(url_for("dashboard"))

            except sqlite3.IntegrityError:
                conn.close()
                flash("An account with this email is already verified. Please login.", "warning")
                return redirect(url_for("login"))
        else:
            conn.close()
            message = "Invalid or expired verification code. Please check and try again."

    return render_template("verify_otp.html", email=email, dev_otp=dev_otp, message=message)


@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    pending_reg = session.get("pending_reg")
    if not pending_reg:
        flash("No active registration session found. Please register.", "warning")
        return redirect(url_for("register"))

    email = pending_reg["email"]
    otp = generate_otp()
    send_res = send_email_otp(email, otp, purpose="register")

    session["pending_otp_info"] = {
        "email": email,
        "dev_otp": otp if not send_res.get("sent") else None,
        "purpose": "register"
    }

    if send_res.get("sent"):
        flash(f"A new verification code was sent to {email}.", "success")
    else:
        flash(f"New verification code generated for {email}. (Dev/Evaluation OTP: {otp})", "info")

    return redirect(url_for("verify_otp"))


# ============================================================
# LOGIN & OTP LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    message = None

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))

        message = "Invalid email or password. Please try again."

    return render_template("login.html", message=message)


@app.route("/login-otp", methods=["GET", "POST"])
def login_otp():
    message = None
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            message = "Please enter your registered email address."
            return render_template("login_otp.html", message=message)

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if not user:
            message = "No account found with this email. Please register first."
            return render_template("login_otp.html", message=message)

        otp = generate_otp()
        send_res = send_email_otp(email, otp, purpose="login")
        session["login_otp_email"] = email
        session["login_otp_dev"] = otp if not send_res.get("sent") else None

        if send_res.get("sent"):
            flash(f"Login code sent to {email}.", "success")
        else:
            flash(f"Login code generated for {email}. (Dev OTP: {otp})", "info")

        return redirect(url_for("verify_login_otp"))

    return render_template("login_otp.html", message=message)


@app.route("/verify-login-otp", methods=["GET", "POST"])
def verify_login_otp():
    email = session.get("login_otp_email")
    dev_otp = session.get("login_otp_dev")
    if not email:
        flash("Please enter your email to receive a login code.", "warning")
        return redirect(url_for("login_otp"))

    message = None
    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()
        conn = get_db()
        record = conn.execute(
            "SELECT * FROM email_otps WHERE email = ? AND otp = ? AND purpose = 'login' AND expires_at > ? ORDER BY id DESC LIMIT 1",
            (email.lower(), entered_otp, time.time())
        ).fetchone()

        if record:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            conn.execute("DELETE FROM email_otps WHERE email = ? AND purpose = 'login'", (email,))
            conn.commit()
            conn.close()

            session.pop("login_otp_email", None)
            session.pop("login_otp_dev", None)
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            conn.close()
            message = "Invalid or expired login code. Please try again."

    return render_template("verify_login_otp.html", email=email, dev_otp=dev_otp, message=message)


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# ============================================================
# FORGOT PASSWORD — SECURITY QUESTION FLOW
# ============================================================

SECURITY_QUESTIONS = [
    "What was the name of your first pet?",
    "What is your mother's maiden name?",
    "What city were you born in?",
    "What was the name of your primary school?",
    "What is your oldest sibling's middle name?",
    "What street did you grow up on?",
    "What was the make of your first car?",
    "What is the name of your favourite childhood friend?",
]


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Step 1 — verify email exists, then ask security question."""
    import re as _re
    message = None
    step = request.args.get("step", "email")

    if request.method == "POST":
        action = request.form.get("action", "lookup")

        # ── STEP 1: find account by email ──
        if action == "lookup":
            email = request.form.get("email", "").strip().lower()
            if not email:
                message = "Please enter your registered email address."
                return render_template("forgot_password.html", step="email", message=message)

            conn = get_db()
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            conn.close()

            if not user or not user["security_question"]:
                message = "No account found with this email, or no security question was set up."
                return render_template("forgot_password.html", step="email", message=message)

            session["fp_email"] = email
            session["fp_question"] = user["security_question"]
            return render_template(
                "forgot_password.html",
                step="question",
                email=email,
                security_question=user["security_question"]
            )

        # ── STEP 2: verify security answer ──
        elif action == "verify_answer":
            email = session.get("fp_email")
            if not email:
                flash("Session expired. Please start over.", "warning")
                return redirect(url_for("forgot_password"))

            entered_answer = request.form.get("security_answer", "").strip().lower()
            conn = get_db()
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            conn.close()

            if not user or not check_password_hash(user["security_answer"] or "", entered_answer):
                message = "Incorrect answer. Please try again."
                return render_template(
                    "forgot_password.html",
                    step="question",
                    email=email,
                    security_question=session.get("fp_question", ""),
                    message=message
                )

            session["fp_verified"] = True
            return render_template("forgot_password.html", step="reset", email=email)

        # ── STEP 3: set new password ──
        elif action == "reset_password":
            email = session.get("fp_email")
            verified = session.get("fp_verified")

            if not email or not verified:
                flash("Session expired. Please start over.", "warning")
                return redirect(url_for("forgot_password"))

            new_password     = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            pw_errors = []
            if len(new_password) < 8:
                pw_errors.append("at least 8 characters")
            if not _re.search(r"[A-Z]", new_password):
                pw_errors.append("one uppercase letter")
            if not _re.search(r"[a-z]", new_password):
                pw_errors.append("one lowercase letter")
            if not _re.search(r"\d", new_password):
                pw_errors.append("one digit")
            if not _re.search(r"[^A-Za-z0-9]", new_password):
                pw_errors.append("one special character")
            if pw_errors:
                message = "Password must include: " + ", ".join(pw_errors) + "."
                return render_template("forgot_password.html", step="reset", email=email, message=message)

            if new_password != confirm_password:
                message = "Passwords do not match."
                return render_template("forgot_password.html", step="reset", email=email, message=message)

            conn = get_db()
            conn.execute(
                "UPDATE users SET password = ? WHERE email = ?",
                (generate_password_hash(new_password), email)
            )
            conn.commit()
            conn.close()

            session.pop("fp_email", None)
            session.pop("fp_question", None)
            session.pop("fp_verified", None)

            flash("Password reset successfully! You can now log in with your new password.", "success")
            return redirect(url_for("login"))

    return render_template("forgot_password.html", step="email", message=message,
                           security_questions=SECURITY_QUESTIONS)



# ============================================================
# DEMO LOGIN (1-CLICK INSTANT ACCESS)
# ============================================================

@app.route("/demo-login")
def demo_login():
    """1-click instant access for demo and evaluation."""
    demo_user = ensure_demo_user()
    session["user_id"] = demo_user["id"]
    session["user_name"] = demo_user["name"]
    flash("Welcome! You are browsing in Demo Mode (Demo Student).", "success")
    next_url = request.args.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect(url_for("simulation"))


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    stats = get_user_stats(session["user_id"])

    # Recent drafts
    conn = get_db()
    recent_drafts = conn.execute(
        "SELECT * FROM simulations WHERE user_id = ? "
        "ORDER BY updated_at DESC LIMIT 3",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        stats=stats,
        recent_drafts=recent_drafts
    )


# ============================================================
# PROFILE
# ============================================================

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    message = None
    success = None

    conn = get_db()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()

        if not name or not email:
            message = "Name and email are required."
        else:
            try:
                conn.execute(
                    "UPDATE users SET name=?, email=?, phone=? WHERE id=?",
                    (name, email, phone, session["user_id"])
                )
                conn.commit()
                session["user_name"] = name
                success = "Profile updated successfully."
            except sqlite3.IntegrityError:
                message = "That email address belongs to another account."

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    stats = get_user_stats(session["user_id"])

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        message=message,
        success=success
    )


# ============================================================
# TAX CALCULATOR
# ============================================================

@app.route("/tax-calculator", methods=["GET", "POST"])
def tax_calculator():
    result = None

    if request.method == "POST":

        try:
            financial_year = request.form.get("financial_year", "FY2025-26")
            age = int(request.form.get("age", 30))
            regime = request.form.get("regime", "new")

            salary = float(request.form.get("salary", 0) or 0)
            pension = float(request.form.get("pension", 0) or 0)
            house_property = float(request.form.get("house_property", 0) or 0)
            other_sources = float(request.form.get("other_sources", 0) or 0)
            capital_gains = float(request.form.get("capital_gains", 0) or 0)
            agricultural_income = float(request.form.get("agricultural_income", 0) or 0)

            deduction_80c = float(request.form.get("deduction_80c", 0) or 0)
            deduction_80ccd = float(request.form.get("deduction_80ccd", 0) or 0)
            deduction_80d = float(request.form.get("deduction_80d", 0) or 0)
            deduction_80e = float(request.form.get("deduction_80e", 0) or 0)
            deduction_80g = float(request.form.get("deduction_80g", 0) or 0)
            deduction_80tta = float(request.form.get("deduction_80tta", 0) or 0)

            tds = float(request.form.get("tds", 0) or 0)
            tcs = float(request.form.get("tcs", 0) or 0)
            advance_tax = float(request.form.get("advance_tax", 0) or 0)
            self_assessment_tax = float(request.form.get("self_assessment_tax", 0) or 0)

            # Rule-Based Tax Calculation (NOT Gemini)
            calculation = calculate_income_tax(
                financial_year=financial_year,
                regime=regime,
                age=age,
                salary=salary,
                pension=pension,
                house_property=house_property,
                other_sources=other_sources,
                capital_gains=capital_gains,
                agricultural_income=agricultural_income,
                deduction_80c=deduction_80c,
                deduction_80ccd=deduction_80ccd,
                deduction_80d=deduction_80d,
                deduction_80e=deduction_80e,
                deduction_80g=deduction_80g,
                deduction_80tta=deduction_80tta,
                tds=tds,
                tcs=tcs,
                advance_tax=advance_tax,
                self_assessment_tax=self_assessment_tax
            )

            calculation["regime_label"] = (
                "New Tax Regime" if regime == "new" else "Old Tax Regime"
            )
            calculation["financial_year_label"] = financial_year.replace(
                "FY", "FY "
            )

            result = calculation

        except ValueError:
            flash("Please enter valid numeric values.", "error")
        except Exception as e:
            app.logger.error(f"Tax calculation error: {e}")
            flash(
                "Unable to calculate tax. Please check the entered values.",
                "error"
            )

    available_years = get_supported_years()

    return render_template(
        "tax_calculator.html",
        result=result,
        available_years=available_years
    )


@app.route("/api/calculate-tax", methods=["POST"])
def api_calculate_tax():
    """API endpoint for reactive, real-time dual regime comparison (Image 4)."""
    data = request.get_json() or {}
    fy = data.get("financial_year", "FY2025-26")
    salary = float(data.get("salary", 0) or 0)
    interest = float(data.get("interest", 0) or 0)
    other = float(data.get("other", 0) or 0)
    d80c = float(data.get("deduction_80c", 0) or 0)
    d80d = float(data.get("deduction_80d", 0) or 0)
    d80ccd = float(data.get("deduction_80ccd", 0) or 0)
    home_loan = float(data.get("home_loan", 0) or 0)
    other_sources = interest + other

    # Limit deductions according to rules
    d80c = min(max(d80c, 0.0), 150000.0)
    d80ccd = min(max(d80ccd, 0.0), 50000.0)
    d80d = min(max(d80d, 0.0), 75000.0)
    home_loan = min(max(home_loan, 0.0), 200000.0)

    try:
        new_calc = calculate_income_tax(
            financial_year=fy,
            regime="new",
            salary=salary,
            other_sources=other_sources,
            house_property=-home_loan if home_loan else 0,
            deduction_80c=0,
            deduction_80ccd=0,
            deduction_80d=0
        )
        old_calc = calculate_income_tax(
            financial_year=fy,
            regime="old",
            salary=salary,
            other_sources=other_sources,
            house_property=-home_loan if home_loan else 0,
            deduction_80c=d80c,
            deduction_80ccd=d80ccd,
            deduction_80d=d80d
        )

        new_tax = float(new_calc.get("total_tax", 0) or 0)
        old_tax = float(old_calc.get("total_tax", 0) or 0)

        if new_tax < old_tax:
            better = "New"
            saving = old_tax - new_tax
            rec_message = f"New Tax Regime is recommended. It saves you ₹{saving:,.0f} in tax."
        elif old_tax < new_tax:
            better = "Old"
            saving = new_tax - old_tax
            rec_message = f"Old Tax Regime is recommended. Your deductions save you ₹{saving:,.0f} in tax."
        else:
            better = "Equal"
            saving = 0
            if new_tax == 0:
                rec_message = "Your total income is within the tax-free limit. Zero tax is payable under both regimes."
            else:
                rec_message = f"Both regimes result in the exact same tax liability of ₹{new_tax:,.0f}."

        return jsonify({
            "success": True,
            "new": new_calc,
            "old": old_calc,
            "better_regime": better,
            "saving": saving,
            "recommendation_message": rec_message
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ============================================================
# TAX SLABS
# ============================================================

@app.route("/tax-slabs")
@login_required
def tax_slabs():
    financial_year = request.args.get("fy", "FY2025-26")
    available_years = get_supported_years()

    slab_data = get_slab_display_data(financial_year)
    regime_info = get_regime_comparison()
    itr_forms = get_itr_forms()
    deduction_rules = get_deduction_rules()
    important_dates = get_important_dates(financial_year)

    return render_template(
        "slabs.html",
        slab_data=slab_data,
        regime_info=regime_info,
        itr_forms=itr_forms,
        deduction_rules=deduction_rules,
        important_dates=important_dates,
        selected_year=financial_year,
        available_years=available_years
    )


# ============================================================
# ITR TRAINING
# ============================================================

TRAINING_LESSONS = [
    {
        "id": "intro_income_tax",
        "order": 1,
        "title": "Introduction to Income Tax",
        "category": "Basics",
        "duration": "5 min",
        "content": """
<h3>What is Income Tax?</h3>
<p>Income Tax is a direct tax levied by the Government of India on the income earned by individuals, businesses, and other entities during a financial year.</p>

<h3>Why is Income Tax Important?</h3>
<ul>
<li>It funds government expenditure — roads, hospitals, defence, education.</li>
<li>Every earning individual above the basic exemption limit is required to file a return.</li>
<li>Filing ITR helps establish financial credibility for loans, visas, etc.</li>
</ul>

<h3>Financial Year vs Assessment Year</h3>
<p><strong>Financial Year (FY)</strong>: The year in which you earn income. Runs from April 1 to March 31.</p>
<p><strong>Assessment Year (AY)</strong>: The year <em>after</em> the financial year — the year in which income is assessed and tax is paid.</p>
<p><strong>Example:</strong> Income earned April 2025 – March 2026 → FY 2025-26 → AY 2026-27.</p>

<div class="lesson-tip"><strong>💡 Key Point:</strong> When you file your ITR in July 2026, you are filing for FY 2025-26 (AY 2026-27).</div>
"""
    },
    {
        "id": "why_file_itr",
        "order": 2,
        "title": "Why File an ITR?",
        "category": "Basics",
        "duration": "4 min",
        "content": """
<h3>Who Must File an ITR?</h3>
<ul>
<li>Individuals with total income above the basic exemption limit.</li>
<li>Individuals with income from capital gains, foreign sources, or assets abroad.</li>
<li>Individuals who want to claim a tax refund on excess TDS deducted.</li>
</ul>

<h3>Benefits of Filing ITR</h3>
<ul>
<li><strong>Claim refund</strong> if excess tax was deducted at source (TDS).</li>
<li><strong>Carry forward losses</strong> from capital gains or business to future years.</li>
<li><strong>Loan applications</strong> — banks often require ITR copies.</li>
<li><strong>Visa applications</strong> — embassies may require ITR as proof of income.</li>
<li><strong>Avoid penalties</strong> — late filing or non-filing attracts penalties under Section 234F.</li>
</ul>

<div class="lesson-tip"><strong>💡 Key Point:</strong> Even if your income is below the taxable limit, filing ITR is beneficial for maintaining a financial record.</div>
"""
    },
    {
        "id": "itr_forms_overview",
        "order": 3,
        "title": "Types of ITR Forms",
        "category": "ITR Forms",
        "duration": "6 min",
        "content": """
<h3>ITR Form Types</h3>
<p>The Income Tax Department has different ITR forms for different types of taxpayers.</p>

<table class="lesson-table">
<tr><th>Form</th><th>For</th><th>Key Condition</th></tr>
<tr><td><strong>ITR-1 (Sahaj)</strong></td><td>Resident individuals</td><td>Salary + one house + other sources; income ≤ ₹50 lakh</td></tr>
<tr><td><strong>ITR-2</strong></td><td>Individuals &amp; HUF</td><td>No business income; capital gains OK; foreign income OK</td></tr>
<tr><td><strong>ITR-3</strong></td><td>Individuals &amp; HUF</td><td>Business/professional income (regular books)</td></tr>
<tr><td><strong>ITR-4 (Sugam)</strong></td><td>Individuals/HUF/Firms</td><td>Presumptive taxation (Sec 44AD/44ADA)</td></tr>
</table>

<div class="lesson-tip"><strong>💡 Decision Tree:</strong> This application uses a Decision Tree algorithm to help you identify the correct ITR form based on your income sources.</div>
"""
    },
    {
        "id": "income_sources",
        "order": 4,
        "title": "Heads of Income",
        "category": "Income",
        "duration": "7 min",
        "content": """
<h3>Five Heads of Income (Section 14)</h3>
<p>All income in India is classified under five heads:</p>

<ol>
<li><strong>Salaries</strong> — Basic salary, HRA, allowances, perquisites, bonus from employer.</li>
<li><strong>Income from House Property</strong> — Rent received or deemed rent from property.</li>
<li><strong>Profits and Gains from Business or Profession</strong> — Business income, professional fees.</li>
<li><strong>Capital Gains</strong> — Gains from sale of assets like shares, property, mutual funds.</li>
<li><strong>Income from Other Sources</strong> — Interest income, dividends, lottery, etc.</li>
</ol>

<h3>Why Does Classification Matter?</h3>
<p>Each head has specific rules for deductions, exemptions, and tax treatment. The correct classification affects your tax liability.</p>

<div class="lesson-tip"><strong>💡 Rule-Based Logic:</strong> This application uses Rule-Based Logic to classify your income into the correct head automatically.</div>
"""
    },
    {
        "id": "residential_status",
        "order": 5,
        "title": "Residential Status",
        "category": "Basics",
        "duration": "6 min",
        "content": """
<h3>Why Does Residential Status Matter?</h3>
<p>Residential status determines which income is taxable in India.</p>

<table class="lesson-table">
<tr><th>Status</th><th>Taxable Income</th></tr>
<tr><td>Resident &amp; Ordinarily Resident (ROR)</td><td>Global income (India + abroad)</td></tr>
<tr><td>Resident but Not Ordinarily Resident (RNOR)</td><td>Income received/accrued in India + business income controlled in India</td></tr>
<tr><td>Non-Resident (NR)</td><td>Income received or accrued in India only</td></tr>
</table>

<h3>How is Status Determined? (Section 6)</h3>
<p>Basic condition: If you stay in India for <strong>182 days or more</strong> during the financial year, you are a basic resident.</p>
<p>Ordinary residence requires additional conditions about stay in the previous years.</p>

<div class="lesson-tip"><strong>💡 Decision Tree:</strong> Use the Residential Status Decision Tree in the simulation to determine your exact status.</div>
"""
    },
    {
        "id": "old_vs_new_regime",
        "order": 6,
        "title": "Old vs New Tax Regime",
        "category": "Tax Regimes",
        "duration": "8 min",
        "content": """
<h3>Two Tax Regimes for Individuals</h3>
<p>Since FY 2020-21, individual taxpayers can choose between the Old Regime and the New Regime.</p>

<h3>New Tax Regime (Default from FY 2023-24 onwards)</h3>
<ul>
<li>Lower, simplified tax slab rates.</li>
<li>Standard deduction of ₹75,000 on salary/pension (FY 2025-26).</li>
<li>Section 87A rebate up to ₹60,000 (income ≤ ₹12 lakh).</li>
<li>Most Chapter VI-A deductions (80C, 80D, etc.) NOT available.</li>
<li>No HRA, LTA exemptions.</li>
</ul>

<h3>Old Tax Regime</h3>
<ul>
<li>Higher slab rates but many deductions and exemptions available.</li>
<li>Standard deduction of ₹50,000 on salary.</li>
<li>Section 80C up to ₹1.5 lakh, 80D, 80E, HRA, and more.</li>
<li>Section 87A rebate up to ₹12,500 (income ≤ ₹5 lakh).</li>
</ul>

<div class="lesson-tip"><strong>💡 Which is better?</strong> Use the Tax Calculator in this application to compare both regimes with your actual income and deductions.</div>
"""
    },
    {
        "id": "deductions_overview",
        "order": 7,
        "title": "Deductions and Exemptions",
        "category": "Deductions",
        "duration": "9 min",
        "content": """
<h3>What are Deductions?</h3>
<p>Deductions reduce your taxable income. They are allowed under Chapter VI-A of the Income Tax Act (Sections 80A–80U).</p>

<h3>Key Deductions (Old Regime)</h3>
<ul>
<li><strong>Section 80C</strong> — LIC, PPF, ELSS, EPF, home loan principal — up to ₹1,50,000.</li>
<li><strong>Section 80CCD(1B)</strong> — Additional NPS contribution — up to ₹50,000.</li>
<li><strong>Section 80D</strong> — Health insurance premium — up to ₹25,000 (₹50,000 for senior citizens).</li>
<li><strong>Section 80E</strong> — Education loan interest — no limit, for 8 years.</li>
<li><strong>Section 80G</strong> — Donations to approved funds — 50% or 100%.</li>
<li><strong>Section 80TTA</strong> — Savings account interest — up to ₹10,000.</li>
<li><strong>Section 24(b)</strong> — Home loan interest on self-occupied property — up to ₹2,00,000.</li>
</ul>

<div class="lesson-tip"><strong>💡 Decision Tree:</strong> The Deduction Eligibility Decision Tree in this application helps you understand if a particular deduction is applicable to your situation.</div>
"""
    },
    {
        "id": "tax_calculation_basics",
        "order": 8,
        "title": "How Tax is Calculated",
        "category": "Calculation",
        "duration": "7 min",
        "content": """
<h3>Step-by-Step Tax Calculation</h3>
<ol>
<li><strong>Gross Total Income</strong> = Sum of all income heads.</li>
<li><strong>Less: Standard Deduction</strong> = Deduct standard deduction on salary.</li>
<li><strong>Less: Chapter VI-A Deductions</strong> = 80C, 80D, 80E, etc. (old regime only).</li>
<li><strong>Taxable Income</strong> = Gross Income − All Deductions.</li>
<li><strong>Apply Tax Slabs</strong> = Progressive tax rates on taxable income.</li>
<li><strong>Less: Section 87A Rebate</strong> = If eligible.</li>
<li><strong>Add: Health &amp; Education Cess</strong> = 4% on tax after rebate.</li>
<li><strong>Less: TDS / Advance Tax</strong> = Already paid taxes.</li>
<li><strong>Net Tax Payable / Refundable</strong>.</li>
</ol>

<div class="lesson-tip"><strong>💡 Rule-Based Logic:</strong> This application uses deterministic rule-based logic to perform all tax calculations. The AI assistant explains the results — it does not calculate tax.</div>
"""
    },
    {
        "id": "form_16_26as",
        "order": 9,
        "title": "Form 16 and Form 26AS",
        "category": "Documents",
        "duration": "6 min",
        "content": """
<h3>Form 16 — TDS Certificate from Employer</h3>
<p>Form 16 is issued by your employer and contains:</p>
<ul>
<li>Part A: TDS deducted and deposited to the government.</li>
<li>Part B: Salary breakup, deductions claimed, and tax computation.</li>
</ul>
<p><strong>When is it issued?</strong> Before June 15 each year for the previous financial year.</p>

<h3>Form 26AS — Tax Credit Statement</h3>
<p>Form 26AS is a consolidated annual tax statement issued by the Income Tax Department. It shows:</p>
<ul>
<li>TDS deducted by all employers and deductors.</li>
<li>Advance tax paid.</li>
<li>Self-assessment tax paid.</li>
<li>TCS collected.</li>
</ul>
<p><strong>Why is it important?</strong> It helps verify that the TDS shown in Form 16 matches what is actually recorded with the government.</p>

<div class="lesson-tip"><strong>⚠️ Disclaimer:</strong> This application simulates Form 16 data for educational purposes only. It does not access actual government tax records.</div>
"""
    }
]


@app.route("/training")
@login_required
def training():
    user_id = session["user_id"]
    conn = get_db()

    # Get completed lessons
    completed = conn.execute(
        "SELECT lesson_id FROM training_progress "
        "WHERE user_id = ? AND completed = 1",
        (user_id,)
    ).fetchall()
    conn.close()

    completed_ids = {row["lesson_id"] for row in completed}

    lessons_with_status = []
    for lesson in TRAINING_LESSONS:
        lesson_copy = dict(lesson)
        lesson_copy["completed"] = lesson["id"] in completed_ids
        lessons_with_status.append(lesson_copy)

    total = len(TRAINING_LESSONS)
    done = len(completed_ids)

    return render_template(
        "training.html",
        lessons=lessons_with_status,
        total_lessons=total,
        completed_count=done,
        progress_pct=round((done / total) * 100) if total else 0
    )


@app.route("/training/lesson/<lesson_id>")
@login_required
def training_lesson(lesson_id):
    lesson = next(
        (l for l in TRAINING_LESSONS if l["id"] == lesson_id),
        None
    )
    if not lesson:
        flash("Lesson not found.", "error")
        return redirect(url_for("training"))

    lesson_index = next(
        (i for i, l in enumerate(TRAINING_LESSONS) if l["id"] == lesson_id),
        0
    )

    prev_lesson = (
        TRAINING_LESSONS[lesson_index - 1]
        if lesson_index > 0 else None
    )
    next_lesson = (
        TRAINING_LESSONS[lesson_index + 1]
        if lesson_index < len(TRAINING_LESSONS) - 1 else None
    )

    return render_template(
        "lesson.html",
        lesson=lesson,
        prev_lesson=prev_lesson,
        next_lesson=next_lesson,
        total_lessons=len(TRAINING_LESSONS),
        lesson_number=lesson_index + 1
    )


@app.route("/training/complete/<lesson_id>", methods=["POST"])
@login_required
def complete_lesson(lesson_id):
    """Mark a lesson as completed."""
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO training_progress
           (user_id, lesson_id, completed, completed_at)
           VALUES (?, ?, 1, ?)""",
        (session["user_id"], lesson_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    flash("Lesson marked as completed! 🎉", "success")
    return redirect(url_for("training"))


# ============================================================
# ITR SIMULATION
# ============================================================

SIMULATION_STEPS = [
    {"step": 1,  "code": "Part A",        "title": "Filing Setup & Demographics", "schedule": "Part A — Demographics & Filing Section", "icon_tag": "GEN", "icon": "👤"},
    {"step": 2,  "code": "Section 6",     "title": "Residential Status Assessment", "schedule": "Section 6 (ROR / RNOR / NR)",      "icon_tag": "RES", "icon": "🌐"},
    {"step": 3,  "code": "ITR Selection", "title": "ITR Form & Selection Wizard", "schedule": "Rule 12 Form Selection & Wizard",    "icon_tag": "ITR", "icon": "🌳"},
    {"step": 4,  "code": "Schedules",     "title": "Select Applicable Schedules", "schedule": "Schedules for Chosen ITR",         "icon_tag": "SCH", "icon": "📋"},
    {"step": 5,  "code": "Schedule S",    "title": "Salary Income (Form 16)",     "schedule": "Section 17 & Standard Deduction",    "icon_tag": "SAL", "icon": "💼"},
    {"step": 6,  "code": "Schedule HP",   "title": "House Property Income",       "schedule": "Section 22–24 (NAV & Interest)",     "icon_tag": "HP",  "icon": "🏠"},
    {"step": 7,  "code": "Schedule OS/CG","title": "Other Sources & Capital Gains","schedule": "Section 56 & Capital Gains (CG)",   "icon_tag": "OS",  "icon": "📈"},
    {"step": 8,  "code": "Schedule VIA",  "title": "Deductions & Exemptions",     "schedule": "Chapter VI-A (80C, 80D, 80CCD)",     "icon_tag": "DED", "icon": "➖"},
    {"step": 9,  "code": "Taxes Paid",    "title": "Taxes Paid & Tax Credits",    "schedule": "TDS (16/26AS/AIS) & Advance Tax",    "icon_tag": "TAX", "icon": "💳"},
    {"step": 10, "code": "Regime / TTI",  "title": "Tax Liability & Regime Choice", "schedule": "Section 115BAC vs Old Regime",     "icon_tag": "REG", "icon": "⚖️"},
    {"step": 11, "code": "Validation",    "title": "Computation Review & Preview", "schedule": "Error Check & Return Preview",     "icon_tag": "VAL", "icon": "🔍"},
    {"step": 12, "code": "E-Verification","title": "Declaration & E-Verification", "schedule": "Rule 12 Declaration & E-Verify",    "icon_tag": "VER", "icon": "✍️"},
    {"step": 13, "code": "CPC Intimation","title": "Department Processing u/s 143", "schedule": "Simulated CPC Processing & Outcome", "icon_tag": "REP", "icon": "🏛️"},
]

TOTAL_STEPS = len(SIMULATION_STEPS)


@app.route("/simulation")
@login_required
def simulation():
    """Show all simulations / start new."""
    conn = get_db()
    all_sims = conn.execute(
        "SELECT * FROM simulations WHERE user_id = ? "
        "ORDER BY updated_at DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template(
        "simulation.html",
        simulations=all_sims,
        steps=SIMULATION_STEPS
    )


@app.route("/simulation/new", methods=["GET", "POST"])
@login_required
def simulation_new():
    """Create a new simulation draft."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        fy = request.form.get("financial_year", "FY2025-26")
    else:
        title = request.args.get("title", "").strip()
        fy = request.args.get("financial_year", "FY2025-26")

    if not title:
        title = f"ITR Simulation — {datetime.now().strftime('%d %b %Y')}"

    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO simulations
           (user_id, title, financial_year, current_step, status, simulation_data)
           VALUES (?, ?, ?, 1, 'draft', ?)""",
        (session["user_id"], title, fy, json.dumps({}))
    )
    sim_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return redirect(url_for("simulation_step", sim_id=sim_id, step=1))


@app.route("/simulation/<int:sim_id>/step/<int:step>", methods=["GET", "POST"])
@login_required
def simulation_step(sim_id, step):
    """Handle a single simulation step."""
    conn = get_db()
    sim = conn.execute(
        "SELECT * FROM simulations WHERE id = ? AND user_id = ?",
        (sim_id, session["user_id"])
    ).fetchone()

    if not sim:
        conn.close()
        flash("Simulation not found.", "error")
        return redirect(url_for("simulation"))

    sim_data = json.loads(sim["simulation_data"] or "{}")
    errors = []
    warnings = []

    if request.method == "POST":
        action = request.form.get("action", "next")

        if action == "save":
            # Just save without advancing
            _save_step_data(conn, sim_id, step, request.form, sim_data)
            conn.commit()
            conn.close()
            flash("Progress saved.", "success")
            return redirect(url_for("simulation_step", sim_id=sim_id, step=step))

        elif action == "back" and step > 1:
            _save_step_data(conn, sim_id, step, request.form, sim_data)
            conn.commit()
            conn.close()
            return redirect(url_for("simulation_step", sim_id=sim_id, step=step - 1))

        elif action == "next":
            _save_step_data(conn, sim_id, step, request.form, sim_data)

            if step == TOTAL_STEPS:
                # Mark complete and go to report
                _finalize_simulation(conn, sim_id, sim_data, sim["financial_year"])
                conn.commit()
                conn.close()
                return redirect(url_for("report_view", sim_id=sim_id))

            conn.execute(
                "UPDATE simulations SET current_step=?, updated_at=? WHERE id=?",
                (step + 1, datetime.now().isoformat(), sim_id)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("simulation_step", sim_id=sim_id, step=step + 1))

    conn.close()

    # Decision Tree and computation helpers for relevant steps
    dt_result = None
    live_tax_calc = None
    validation_report = None

    if step == 2:
        dt_result = _run_residential_dt(sim_data)
    elif step == 3:
        dt_result = _run_itr_form_dt(sim_data)
    elif step == 10:
        # Precompute live comparison for New vs Old regime
        live_tax_calc = _compute_live_tax_comparison(sim_data, sim["financial_year"])
    elif step == 11:
        # Compute validation report & summary
        validation_report = _run_return_validation(sim_data, sim["financial_year"])
    elif step == 13:
        # Pre-compute intimation details
        live_tax_calc = _compute_live_tax_comparison(sim_data, sim["financial_year"])

    return render_template(
        "simulation_step.html",
        sim=sim,
        sim_data=sim_data,
        step=step,
        steps=SIMULATION_STEPS,
        total_steps=TOTAL_STEPS,
        current_step_info=SIMULATION_STEPS[step - 1],
        errors=errors,
        warnings=warnings,
        dt_result=dt_result,
        live_tax_calc=live_tax_calc,
        validation_report=validation_report,
        progress_pct=round((step / TOTAL_STEPS) * 100)
    )


def _safe_float(val, default=0.0):
    """Safely parse float values, returning default if None or empty string."""
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _save_step_data(conn, sim_id, step, form_data, sim_data):
    """Save form data for a simulation step into the JSON blob."""
    step_key = f"step_{step}"
    step_dict = {k: v for k, v in form_data.items()
                 if k not in ("action", "csrf_token")}

    # Handle checkbox lists (income sources, selected schedules, etc.)
    checkboxes = form_data.getlist("income_sources")
    if checkboxes:
        step_dict["income_sources"] = checkboxes
    schedules = form_data.getlist("selected_schedules")
    if schedules:
        step_dict["selected_schedules"] = schedules

    # If Step 2, immediately calculate and persist deterministic Section 6 status
    if step == 2:
        res_choice = step_dict.get("residential_status_choice") or step_dict.get("residential_status") or ""
        if "Non-Resident" in res_choice or res_choice == "NR":
            step_dict["residential_status"] = "Non-Resident (NR)"
            step_dict["residential_code"] = "NR"
            step_dict["is_resident"] = False
            step_dict["itr_1_eligible"] = False
        elif "Not Ordinarily Resident" in res_choice or res_choice == "RNOR":
            step_dict["residential_status"] = "Resident but Not Ordinarily Resident (RNOR)"
            step_dict["residential_code"] = "RNOR"
            step_dict["is_resident"] = True
            step_dict["itr_1_eligible"] = False
        elif "Ordinarily Resident" in res_choice or res_choice == "ROR":
            step_dict["residential_status"] = "Resident and Ordinarily Resident (ROR)"
            step_dict["residential_code"] = "ROR"
            step_dict["is_resident"] = True
            step_dict["itr_1_eligible"] = True
        else:
            try:
                days_curr = int(step_dict.get("days_in_india", 182) or 0)
            except (ValueError, TypeError):
                days_curr = 0
            try:
                days_4yr = int(step_dict.get("days_last_4_years", 365) or 0)
            except (ValueError, TypeError):
                days_4yr = 0
            try:
                days_7yr = int(step_dict.get("days_last_7_years", 730) or 0)
            except (ValueError, TypeError):
                days_7yr = 0

            res_raw = step_dict.get("resident_9_of_10") or step_dict.get("resident_2_of_10") or "yes"
            res_2_10 = (str(res_raw).lower() in ("yes", "true", "1"))

            res_eval = determine_residential_status(
                days_in_india_current_year=days_curr,
                days_in_india_last_4_years=days_4yr,
                days_in_india_last_7_years=days_7yr,
                resident_in_at_least_2_of_10_years=res_2_10
            )
            step_dict["residential_status"] = res_eval["status"]
            step_dict["residential_code"] = res_eval["status_code"]
            step_dict["is_resident"] = res_eval["is_resident"]
            step_dict["itr_1_eligible"] = res_eval["itr_1_eligible"]

    sim_data[step_key] = step_dict

    # Keep Step 3 form recommendation in sync with residential status and wizard answers
    if step in (2, 3):
        form_eval = _run_itr_form_dt(sim_data)
        if "step_3" not in sim_data:
            sim_data["step_3"] = {}
        sim_data["step_3"]["recommended_itr_form"] = form_eval.get("form_code", "ITR-1")
        sim_data["step_3"]["dt_reason"] = form_eval.get("reason", "")
        # If user did not manually pick a form via radio or know_itr is 'no', sync to recommended form
        if sim_dict_know := sim_data["step_3"].get("know_itr"):
            if sim_dict_know == "no" or not sim_data["step_3"].get("selected_itr_form"):
                sim_data["step_3"]["selected_itr_form"] = form_eval.get("form_code", "ITR-1")

    conn.execute(
        "UPDATE simulations SET simulation_data=?, updated_at=? WHERE id=?",
        (json.dumps(sim_data), datetime.now().isoformat(), sim_id)
    )


def _run_residential_dt(sim_data):
    """Run Residential Status Decision Tree from simulation data."""
    step2 = sim_data.get("step_2", {})
    if not step2:
        return {
            "status": "Resident and Ordinarily Resident (ROR)",
            "status_code": "ROR",
            "is_resident": True,
            "is_ordinarily_resident": True,
            "itr_1_eligible": True,
            "itr_eligible": True,
            "taxability": "Global income taxable in India under Section 5.",
            "reasons": ["Default residential status: Resident and Ordinarily Resident (ROR)."]
        }

    res_choice = step2.get("residential_status_choice") or step2.get("residential_status") or step2.get("residential_code") or ""
    if "Non-Resident" in res_choice or res_choice == "NR":
        return {
            "status": "Non-Resident (NR)",
            "status_code": "NR",
            "is_resident": False,
            "is_ordinarily_resident": False,
            "itr_1_eligible": False,
            "itr_eligible": False,
            "taxability": "Indian-sourced income only.",
            "reasons": ["Taxpayer classified as Non-Resident (NR) under Section 6."]
        }
    elif "Not Ordinarily" in res_choice or res_choice == "RNOR":
        return {
            "status": "Resident but Not Ordinarily Resident (RNOR)",
            "status_code": "RNOR",
            "is_resident": True,
            "is_ordinarily_resident": False,
            "itr_1_eligible": False,
            "itr_eligible": False,
            "taxability": "Indian-sourced income and income derived from business controlled in India.",
            "reasons": ["Taxpayer classified as Resident but Not Ordinarily Resident (RNOR) under Section 6(6)."]
        }
    elif "Ordinarily" in res_choice or res_choice == "ROR":
        return {
            "status": "Resident and Ordinarily Resident (ROR)",
            "status_code": "ROR",
            "is_resident": True,
            "is_ordinarily_resident": True,
            "itr_1_eligible": True,
            "itr_eligible": True,
            "taxability": "Global income taxable in India under Section 5.",
            "reasons": ["Taxpayer classified as Resident and Ordinarily Resident (ROR) under Section 6."]
        }

    try:
        days_curr = int(step2.get("days_in_india", 182) or 0)
    except (ValueError, TypeError):
        days_curr = 182
    try:
        days_4yr = int(step2.get("days_last_4_years", 365) or 0)
    except (ValueError, TypeError):
        days_4yr = 365
    try:
        days_7yr = int(step2.get("days_last_7_years", 730) or 0)
    except (ValueError, TypeError):
        days_7yr = 730

    res_raw = step2.get("resident_9_of_10") or step2.get("resident_2_of_10") or "yes"
    res_2_10 = (str(res_raw).lower() in ("yes", "true", "1"))

    res = determine_residential_status(
        days_in_india_current_year=days_curr,
        days_in_india_last_4_years=days_4yr,
        days_in_india_last_7_years=days_7yr,
        resident_in_at_least_2_of_10_years=res_2_10
    )
    res["itr_eligible"] = res.get("itr_1_eligible", res.get("is_resident", True))
    return res


def _run_itr_form_dt(sim_data):
    """Run ITR Form Selection Decision Tree & Eligibility Engine from simulation data."""
    res_status = _run_residential_dt(sim_data)
    is_res = res_status.get("is_resident", True)
    status_code = res_status.get("status_code", "ROR")
    status_label = res_status.get("status", "Resident and Ordinarily Resident (ROR)")

    step3 = sim_data.get("step_3", {})

    has_salary = (step3.get("salary_income") == "yes")
    mult_hp = (step3.get("multiple_house_property") == "yes")
    has_business = (step3.get("business_income") == "yes")
    has_cg = (step3.get("capital_gains") == "yes")
    has_foreign_inc = (step3.get("foreign_income") == "yes")
    income_high = (step3.get("income_above_50l") == "yes")
    presumptive = (step3.get("presumptive_taxation") == "yes")

    # Also inspect actual income schedules if already populated
    s4 = sim_data.get("step_4", {})
    s5 = sim_data.get("step_5", {})
    s6 = sim_data.get("step_6", {})
    s7 = sim_data.get("step_7", {})
    if _safe_float(s5.get("gross_salary") or s4.get("gross_salary")) > 0:
        has_salary = True
    if _safe_float(s6.get("house_property_income")) != 0:
        one_hp = not mult_hp
    else:
        one_hp = not mult_hp
    if _safe_float(s7.get("capital_gains_amount")) > 0 or _safe_float(s7.get("stcg_111a") or s4.get("stcg_111a")) > 0 or _safe_float(s7.get("ltcg_112a")) > 0:
        has_cg = True
    if _safe_float(s7.get("presumptive_income")) > 0 or _safe_float(s7.get("turnover_44ad")) > 0:
        presumptive = True

    # Baseline defaults if nothing entered yet
    if not (has_salary or mult_hp or has_business or has_cg or has_foreign_inc or presumptive):
        has_salary = True
        one_hp = True

    tot_inc = 6000000 if income_high else 850000

    dt_res = select_itr_form(
        salary_income=has_salary,
        pension_income=False,
        one_house_property=one_hp and not mult_hp,
        multiple_house_property=mult_hp,
        business_income=has_business,
        professional_income=False,
        presumptive_taxation=presumptive,
        capital_gains=has_cg,
        foreign_income=has_foreign_inc,
        foreign_assets=has_foreign_inc,
        agriculture_income=0,
        director_in_company=False,
        unlisted_shares=False,
        total_income=tot_inc,
        is_resident=is_res,
        residential_status=status_label,
        status_code=status_code
    )

    dt_res["reasons"] = [dt_res.get("reason", "")]
    return dt_res


def _compute_live_tax_comparison(sim_data, financial_year):
    """Helper to compute live comparison between New and Old regimes."""
    step1 = sim_data.get("step_1", {})
    step4 = sim_data.get("step_4", {})
    step5 = sim_data.get("step_5", {})
    step6 = sim_data.get("step_6", {})
    step7 = sim_data.get("step_7", {})
    step8 = sim_data.get("step_8", {})
    step9 = sim_data.get("step_9", {})

    res_status = _run_residential_dt(sim_data)
    is_res = res_status.get("is_resident", True)

    try:
        age = int(step1.get("age", 30) or 30)
    except (ValueError, TypeError):
        age = 30

    salary_val = _safe_float(step5.get("gross_salary") if "gross_salary" in step5 else step4.get("gross_salary", 0.0))
    pension_val = _safe_float(step7.get("family_pension", 0.0))
    house_prop_val = _safe_float(step6.get("house_property_income", 0.0))

    if "other_sources_income" in step7 and step7.get("other_sources_income") != "":
        other_src_val = _safe_float(step7.get("other_sources_income", 0.0))
    else:
        other_src_val = (
            _safe_float(step7.get("savings_interest", step4.get("savings_interest", 0.0))) +
            _safe_float(step7.get("fd_interest", step4.get("fd_interest", 0.0))) +
            _safe_float(step7.get("dividend_income", step4.get("dividend_income", 0.0)))
        )

    if "capital_gains_amount" in step7 and step7.get("capital_gains_amount") != "":
        cap_gains_val = _safe_float(step7.get("capital_gains_amount", 0.0))
    else:
        cap_gains_val = (
            _safe_float(step7.get("stcg_111a", step4.get("stcg_111a", 0.0))) +
            _safe_float(step7.get("ltcg_112a", 0.0)) +
            _safe_float(step7.get("ltcg_112", 0.0))
        )

    d_80c = _safe_float(step8.get("deduction_80c", 0.0))
    d_80ccd = _safe_float(step8.get("deduction_80ccd", 0.0))
    d_80d = _safe_float(step8.get("deduction_80d", 0.0))
    d_80e = _safe_float(step8.get("deduction_80e", 0.0))
    d_80g = _safe_float(step8.get("deduction_80g", 0.0))
    d_80tta = _safe_float(step8.get("deduction_80tta", 0.0))

    tds_val = _safe_float(step9.get("tds_salary", step4.get("tds_salary", 0.0))) + _safe_float(step9.get("tds_other", step4.get("tds_other", 0.0)))
    adv_tax_val = _safe_float(step9.get("advance_tax", step4.get("advance_tax", 0.0)))
    self_tax_val = _safe_float(step9.get("self_assessment_tax", step4.get("self_assessment_tax", 0.0)))
    tcs_val = _safe_float(step9.get("tcs", step4.get("tcs", 0.0)))

    calc_new = calculate_income_tax(
        financial_year=financial_year,
        regime="new",
        age=age,
        is_resident=is_res,
        salary=salary_val,
        pension=pension_val,
        house_property=house_prop_val,
        other_sources=other_src_val,
        capital_gains=cap_gains_val,
        deduction_80c=d_80c,
        deduction_80ccd=d_80ccd,
        deduction_80d=d_80d,
        deduction_80e=d_80e,
        deduction_80g=d_80g,
        deduction_80tta=d_80tta,
        tds=tds_val,
        tcs=tcs_val,
        advance_tax=adv_tax_val,
        self_assessment_tax=self_tax_val
    )

    calc_old = calculate_income_tax(
        financial_year=financial_year,
        regime="old",
        age=age,
        is_resident=is_res,
        salary=salary_val,
        pension=pension_val,
        house_property=house_prop_val,
        other_sources=other_src_val,
        capital_gains=cap_gains_val,
        deduction_80c=d_80c,
        deduction_80ccd=d_80ccd,
        deduction_80d=d_80d,
        deduction_80e=d_80e,
        deduction_80g=d_80g,
        deduction_80tta=d_80tta,
        tds=tds_val,
        tcs=tcs_val,
        advance_tax=adv_tax_val,
        self_assessment_tax=self_tax_val
    )

    return {
        "new": calc_new,
        "old": calc_old,
        "tax_diff": abs(calc_new.get("total_tax", 0) - calc_old.get("total_tax", 0)),
        "better_regime": "new" if calc_new.get("total_tax", 0) <= calc_old.get("total_tax", 0) else "old"
    }


def _run_return_validation(sim_data, financial_year):
    """Run comprehensive pre-filing validation checks u/s 139(9)."""
    step1 = sim_data.get("step_1", {})
    step2 = sim_data.get("step_2", {})
    step3 = sim_data.get("step_3", {})
    step8 = sim_data.get("step_8", {})

    errors = []
    warnings = []
    checks = []

    # 1. PAN Check
    pan = step1.get("pan", "").strip().upper()
    import re
    if not pan:
        errors.append("PAN is required for tax return filing under Section 139A.")
        checks.append({"name": "PAN Verification", "passed": False, "detail": "Missing PAN"})
    elif not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan):
        errors.append(f"Invalid PAN format: '{pan}'. Expected format is 5 letters, 4 digits, 1 letter.")
        checks.append({"name": "PAN Verification", "passed": False, "detail": "Invalid structure"})
    else:
        checks.append({"name": "PAN Verification", "passed": True, "detail": f"Valid PAN format ({pan})"})

    # 2. Bank Details for Refund
    bank_acc = step1.get("bank_account_no", "").strip()
    ifsc = step1.get("ifsc_code", "").strip().upper()
    if not bank_acc:
        warnings.append("Bank Account Number is not specified. Direct refund credit may be delayed.")
        checks.append({"name": "Bank Account Details", "passed": False, "detail": "Account number missing"})
    else:
        checks.append({"name": "Bank Account Details", "passed": True, "detail": f"Account entered ({ifsc or 'IFSC verified'})"})

    # 3. Residential Status Verification
    res_status = _run_residential_dt(sim_data)
    is_res = res_status.get("is_resident", True)
    status_str = res_status.get("status", "Resident and Ordinarily Resident (ROR)")
    checks.append({"name": "Section 6 Residency Verification", "passed": True, "detail": status_str})

    # 4. Form Eligibility Check u/s Rule 12
    chosen_form = step3.get("selected_itr_form") or "ITR-1"
    dt_res = _run_itr_form_dt(sim_data)
    rec_code = dt_res.get("form_code", "ITR-1")

    if chosen_form == "ITR-1" and not is_res:
        errors.append("Defective Return u/s 139(9): Non-Residents cannot file ITR-1 (Sahaj). You must file ITR-2 or ITR-3.")
        checks.append({"name": "Rule 12 Form Consistency", "passed": False, "detail": "Non-Resident ineligible for ITR-1"})
    elif chosen_form == "ITR-1" and rec_code in ("ITR-2", "ITR-3"):
        disquals = dt_res.get("disqualifications", [])
        disq_summary = "; ".join(disquals[:2]) if disquals else "Statutory conditions for ITR-1 violated."
        errors.append(f"Defective Return u/s 139(9): ITR-1 is not permitted based on your disclosures. {disq_summary} Recommended: {rec_code}.")
        checks.append({"name": "Rule 12 Form Consistency", "passed": False, "detail": f"Ineligible for ITR-1 ({rec_code} required)"})
    elif chosen_form == "ITR-4" and not is_res:
        errors.append("Defective Return u/s 139(9): Non-Residents cannot file ITR-4 (Sugam).")
        checks.append({"name": "Rule 12 Form Consistency", "passed": False, "detail": "Non-Resident ineligible for ITR-4"})
    elif chosen_form == "ITR-2" and dt_res.get("form_code") == "ITR-3":
        errors.append("Defective Return u/s 139(9): Taxpayers with business or professional income cannot file ITR-2. Must file ITR-3.")
        checks.append({"name": "Rule 12 Form Consistency", "passed": False, "detail": "ITR-2 invalid with business income"})
    else:
        checks.append({"name": "Rule 12 Form Consistency", "passed": True, "detail": f"{chosen_form} validated for filing"})

    # 5. Deduction Limits Check
    c_80c = _safe_float(step8.get("deduction_80c", 0))
    if c_80c > 150000:
        warnings.append(f"Section 80C deduction claimed (₹{c_80c:,.0f}) exceeds statutory cap of ₹1,50,000. Capped automatically.")
        checks.append({"name": "Chapter VI-A Statutory Caps", "passed": True, "detail": "Auto-capped at ₹1.5L"})
    else:
        checks.append({"name": "Chapter VI-A Statutory Caps", "passed": True, "detail": "Within statutory limits"})

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "checks": checks
    }


def _finalize_simulation(conn, sim_id, sim_data, financial_year):
    """Run final tax calculation, CPC processing, and mark simulation as completed."""
    step1 = sim_data.get("step_1", {})
    step4 = sim_data.get("step_4", {})
    step5 = sim_data.get("step_5", {})
    step6 = sim_data.get("step_6", {})
    step7 = sim_data.get("step_7", {})
    step8 = sim_data.get("step_8", {})
    step9 = sim_data.get("step_9", {})
    step10 = sim_data.get("step_10", {})

    res_status = _run_residential_dt(sim_data)
    is_res = res_status.get("is_resident", True)

    regime = step10.get("regime") or sim_data.get("step_9", {}).get("regime", "new")
    try:
        age = int(step1.get("age", 30) or 30)
    except (ValueError, TypeError):
        age = 30

    salary_val = _safe_float(step5.get("gross_salary") if "gross_salary" in step5 else step4.get("gross_salary", 0.0))
    pension_val = _safe_float(step7.get("family_pension", 0.0))
    house_prop_val = _safe_float(step6.get("house_property_income", 0.0))

    if "other_sources_income" in step7 and step7.get("other_sources_income") != "":
        other_src_val = _safe_float(step7.get("other_sources_income", 0.0))
    else:
        other_src_val = (
            _safe_float(step7.get("savings_interest", step4.get("savings_interest", 0.0))) +
            _safe_float(step7.get("fd_interest", step4.get("fd_interest", 0.0))) +
            _safe_float(step7.get("dividend_income", step4.get("dividend_income", 0.0)))
        )

    if "capital_gains_amount" in step7 and step7.get("capital_gains_amount") != "":
        cap_gains_val = _safe_float(step7.get("capital_gains_amount", 0.0))
    else:
        cap_gains_val = (
            _safe_float(step7.get("stcg_111a", step4.get("stcg_111a", 0.0))) +
            _safe_float(step7.get("ltcg_112a", 0.0)) +
            _safe_float(step7.get("ltcg_112", 0.0))
        )

    d_80c = _safe_float(step8.get("deduction_80c", 0.0))
    d_80ccd = _safe_float(step8.get("deduction_80ccd", 0.0))
    d_80d = _safe_float(step8.get("deduction_80d", 0.0))
    d_80e = _safe_float(step8.get("deduction_80e", 0.0))
    d_80g = _safe_float(step8.get("deduction_80g", 0.0))
    d_80tta = _safe_float(step8.get("deduction_80tta", 0.0))

    tds_val = _safe_float(step9.get("tds_salary", step4.get("tds_salary", 0.0))) + _safe_float(step9.get("tds_other", step4.get("tds_other", 0.0)))
    adv_tax_val = _safe_float(step9.get("advance_tax", step4.get("advance_tax", 0.0)))
    self_tax_val = _safe_float(step9.get("self_assessment_tax", step4.get("self_assessment_tax", 0.0)))
    tcs_val = _safe_float(step9.get("tcs", step4.get("tcs", 0.0)))

    try:
        tax_result = calculate_income_tax(
            financial_year=financial_year,
            regime=regime,
            age=age,
            is_resident=is_res,
            salary=salary_val,
            pension=pension_val,
            house_property=house_prop_val,
            other_sources=other_src_val,
            capital_gains=cap_gains_val,
            deduction_80c=d_80c,
            deduction_80ccd=d_80ccd,
            deduction_80d=d_80d,
            deduction_80e=d_80e,
            deduction_80g=d_80g,
            deduction_80tta=d_80tta,
            tds=tds_val,
            tcs=tcs_val,
            advance_tax=adv_tax_val,
            self_assessment_tax=self_tax_val
        )

        refund_amt = tax_result.get("refund", 0)
        tax_payable = tax_result.get("tax_payable", 0)

        if refund_amt > 0:
            cpc_outcome = "refund"
            int_244a = round(refund_amt * 0.015)
            tax_result["interest_244a"] = int_244a
            tax_result["total_refund_with_interest"] = refund_amt + int_244a
        elif tax_payable > 0:
            cpc_outcome = "payable"
        else:
            cpc_outcome = "nil"

        tax_result["cpc_outcome"] = cpc_outcome
        tax_result["cpc_intimation_date"] = datetime.now().strftime("%d %b %Y")
        tax_result["din_number"] = f"CPC/AY2627/{secrets.randbelow(899999)+100000}/{sim_id:04d}"

        conn.execute(
            "UPDATE simulations SET status='completed', tax_result=?, "
            "current_step=13, updated_at=? WHERE id=?",
            (
                json.dumps(tax_result),
                datetime.now().isoformat(),
                sim_id
            )
        )

    except Exception as e:
        app.logger.error(f"Finalize simulation error: {e}")
        conn.execute(
            "UPDATE simulations SET status='completed', updated_at=? WHERE id=?",
            (datetime.now().isoformat(), sim_id)
        )


@app.route("/simulation/<int:sim_id>/delete", methods=["POST"])
@login_required
def simulation_delete(sim_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM simulations WHERE id=? AND user_id=?",
        (sim_id, session["user_id"])
    )
    conn.commit()
    conn.close()
    flash("Simulation deleted.", "info")
    return redirect(url_for("simulation"))


# ============================================================
# DRAFTS
# ============================================================

@app.route("/drafts")
@login_required
def drafts():
    conn = get_db()
    all_drafts = conn.execute(
        "SELECT * FROM simulations WHERE user_id = ? AND status = 'draft' "
        "ORDER BY updated_at DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template("drafts.html", drafts=all_drafts, steps=SIMULATION_STEPS)


# ============================================================
# REPORTS
# ============================================================

@app.route("/reports")
@login_required
def reports():
    conn = get_db()
    all_reports = conn.execute(
        "SELECT * FROM simulations WHERE user_id = ? AND status = 'completed' "
        "ORDER BY updated_at DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template("reports.html", reports=all_reports)


@app.route("/report/<int:sim_id>")
@app.route("/simulation/<int:sim_id>/report")
@login_required
def report_view(sim_id):
    conn = get_db()
    sim = conn.execute(
        "SELECT * FROM simulations WHERE id = ? AND user_id = ?",
        (sim_id, session["user_id"])
    ).fetchone()
    user = get_current_user()
    conn.close()

    if not sim:
        flash("Report not found.", "error")
        return redirect(url_for("reports"))

    sim_data = json.loads(sim["simulation_data"] or "{}")
    tax_result = json.loads(sim["tax_result"] or "{}") if sim["tax_result"] else {}
    itr_form_result = _run_itr_form_dt(sim_data)

    return render_template(
        "report.html",
        sim=sim,
        sim_data=sim_data,
        tax_result=tax_result,
        itr_form_result=itr_form_result,
        user=user
    )


@app.route("/report/<int:sim_id>/download")
@app.route("/simulation/<int:sim_id>/report/pdf")
@login_required
def report_download(sim_id):
    """Generate and download PDF report using reportlab."""
    conn = get_db()
    sim = conn.execute(
        "SELECT * FROM simulations WHERE id = ? AND user_id = ?",
        (sim_id, session["user_id"])
    ).fetchone()
    user = get_current_user()
    conn.close()

    if not sim:
        flash("Report not found.", "error")
        return redirect(url_for("reports"))

    sim_data = json.loads(sim["simulation_data"] or "{}")
    tax_result = json.loads(sim["tax_result"] or "{}") if sim["tax_result"] else {}
    itr_form_result = _run_itr_form_dt(sim_data)

    try:
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            Table, TableStyle, HRFlowable
        )
        from flask import make_response

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm
        )

        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        title_style = ParagraphStyle(
            "title_style",
            parent=styles["Title"],
            fontSize=18,
            textColor=colors.HexColor("#123b68"),
            spaceAfter=6
        )
        heading_style = ParagraphStyle(
            "heading_style",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#123b68"),
            spaceBefore=12,
            spaceAfter=4
        )
        normal_style = styles["Normal"]
        small_style = ParagraphStyle(
            "small_style",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey
        )
        disclaimer_style = ParagraphStyle(
            "disclaimer_style",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#5c4a16"),
            backColor=colors.HexColor("#fff8e5"),
            borderPadding=6,
            leading=12
        )

        # ---- HEADER ----
        story.append(Paragraph("ITR Learn &amp; Simulate", title_style))
        story.append(Paragraph(
            "AI-Integrated Income Tax Return Training &amp; Simulation Platform",
            small_style
        ))
        story.append(Spacer(1, 0.3 * cm))
        story.append(HRFlowable(width="100%", thickness=2,
                                color=colors.HexColor("#123b68")))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            "<b>ITR PRACTICE REPORT</b> — Educational Simulation",
            heading_style
        ))
        story.append(Spacer(1, 0.2 * cm))

        # ---- REPORT META ----
        step1 = sim_data.get("step_1", {})
        step2 = sim_data.get("step_2", {})
        step3 = sim_data.get("step_3", {})
        step12 = sim_data.get("step_12", {})
        step13 = sim_data.get("step_13", {})

        meta_data = [
            ["Report Date", datetime.now().strftime("%d %B %Y")],
            ["Simulation Title", sim["title"]],
            ["Financial Year", sim["financial_year"]],
            ["Assessment Year", "AY 2026-27" if "2025" in sim["financial_year"] else "AY 2027-28"],
            ["Filing Section", step1.get("filing_section", "139(1) (On or before due date)")],
            ["Taxpayer Name", step1.get("name", user["name"]) if user else "—"],
            ["PAN", step1.get("pan", "ABCDE1234F")],
            ["Residential Status", step2.get("residential_status", "Resident & Ordinarily Resident (ROR)")],
            ["ITR Form", step3.get("selected_itr_form") or itr_form_result.get("form_code", "ITR-1")],
            ["E-Verification Status", f"Simulated {step12.get('everify_method', 'Aadhaar OTP')} (Verified)"],
            ["CPC Intimation DIN", tax_result.get("din_number", f"CPC/AY2627/{sim['id']:06d}")],
            ["Report Status", "Educational Simulation Completed — u/s 143(1)"],
        ]
        meta_table = Table(meta_data, colWidths=[5.5 * cm, 11.5 * cm])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf2f8")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e1e8")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1),
             [colors.white, colors.HexColor("#f5f7fa")]),
            ("PADDING", (0, 0), (-1, -1), 4.5),
        ]))
        story.append(meta_table)

        # ---- INCOME DETAILS ----
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("Income Schedules & Gross Total Income", heading_style))

        s5 = sim_data.get("step_5", {})
        s6 = sim_data.get("step_6", {})
        s7 = sim_data.get("step_7", {})
        salary_amt = float(s5.get("gross_salary") or s5.get("net_salary") or sim_data.get("step_4", {}).get("gross_salary") or sim_data.get("step_3", {}).get("salary_amount") or 0)
        pension_amt = float(s7.get("family_pension") or sim_data.get("step_3", {}).get("pension_amount") or 0)
        hp_amt = float(s6.get("house_property_income") or sim_data.get("step_5", {}).get("house_property_income") or sim_data.get("step_3", {}).get("house_property_income") or 0)
        os_amt = float(s7.get("other_sources_income") or sim_data.get("step_6", {}).get("other_sources_income") or sim_data.get("step_3", {}).get("other_sources_income") or 0)
        cg_amt = float(s7.get("capital_gains_amount") or sim_data.get("step_7", {}).get("capital_gains_amount") or 0)

        income_data = [
            ["Income Head / Schedule", "Amount (₹)"],
            ["Schedule S: Income from Salary", f"₹{salary_amt:,.2f}"],
            ["Schedule S/OS: Pension Income", f"₹{pension_amt:,.2f}"],
            ["Schedule HP: Income from House Property", f"₹{hp_amt:,.2f}"],
            ["Schedule OS: Income from Other Sources", f"₹{os_amt:,.2f}"],
            ["Schedule CG: Capital Gains Income", f"₹{cg_amt:,.2f}"],
            ["Gross Total Income (GTI)", f"₹{tax_result.get('gross_income', 0):,.2f}"],
        ]
        inc_table = Table(income_data, colWidths=[9.5 * cm, 7.5 * cm])
        inc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123b68")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#eaf2f8")),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e1e8")),
            ("ROWBACKGROUNDS", (1, 1), (-1, -2),
             [colors.white, colors.HexColor("#f5f7fa")]),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ]))
        story.append(inc_table)

        # ---- TAX CALCULATION ----
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("Part B-TTI: Computation of Tax Liability & Taxes Paid", heading_style))

        regime_choice = sim_data.get("step_10", {}).get("regime") or sim_data.get("step_9", {}).get("regime", "new")
        regime_label = "New Tax Regime (Section 115BAC)" if regime_choice == "new" else "Old Tax Regime (Traditional)"

        refund_val = tax_result.get("refund", 0)
        payable_val = tax_result.get("tax_payable", 0)
        outcome_str = f"REFUND DUE: ₹{refund_val:,.2f} (+ Int u/s 244A: ₹{tax_result.get('interest_244a', 0):,.2f})" if refund_val > 0 else (f"NET TAX PAYABLE: ₹{payable_val:,.2f}" if payable_val > 0 else "NIL DEMAND / NIL REFUND (₹0.00)")

        surcharge_val = tax_result.get("surcharge", 0)
        surch_relief_val = tax_result.get("surcharge_marginal_relief", 0)

        tax_data = [
            ["Tax Computation Parameter", "Amount (₹)"],
            ["Applied Tax Regime", regime_label],
            ["Gross Total Income", f"₹{tax_result.get('gross_income', 0):,.2f}"],
            ["Standard Deduction (u/s 16(ia))", f"₹{tax_result.get('standard_deduction', 0):,.2f}"],
            ["Total Chapter VI-A Deductions", f"₹{tax_result.get('total_deductions', 0):,.2f}"],
            ["Total Taxable Income", f"₹{tax_result.get('taxable_income', 0):,.2f}"],
            ["Tax at Normal Slab Rates", f"₹{tax_result.get('tax_before_rebate', 0):,.2f}"],
            ["Rebate under Section 87A", f"₹{tax_result.get('rebate', 0):,.2f}"],
        ]

        if surcharge_val > 0:
            tax_data.append(["Surcharge (Income > ₹50 Lakh)", f"₹{surcharge_val:,.2f}"])
            if surch_relief_val > 0:
                tax_data.append(["Less: Marginal Relief on Surcharge", f"- ₹{surch_relief_val:,.2f}"])

        tax_data.extend([
            ["Health & Education Cess (4%)", f"₹{tax_result.get('cess', 0):,.2f}"],
            ["Gross Tax Liability (Rounded u/s 288B)", f"₹{tax_result.get('total_tax', 0):,.2f}"],
            ["TDS + Advance Tax Credits Paid", f"₹{(tax_result.get('tds', 0) + tax_result.get('advance_tax', 0) + tax_result.get('self_assessment_tax', 0)):,.2f}"],
            ["FINAL CPC OUTCOME u/s 143(1)", outcome_str],
        ])
        tax_table = Table(tax_data, colWidths=[9.5 * cm, 7.5 * cm])
        tax_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123b68")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d1e7dd") if refund_val > 0 else (colors.HexColor("#f8d7da") if payable_val > 0 else colors.HexColor("#e2e3e5"))),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#0f5132") if refund_val > 0 else (colors.HexColor("#842029") if payable_val > 0 else colors.HexColor("#41464b"))),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e1e8")),
            ("ROWBACKGROUNDS", (1, 1), (-1, -2),
             [colors.white, colors.HexColor("#f5f7fa")]),
            ("PADDING", (0, 0), (-1, -1), 4.5),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ]))
        story.append(tax_table)

        # ---- ITR FORM & RULE 12 VERIFICATION ----
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("ITR Form Verification &amp; Rule 12 Statutory Status", heading_style))
        story.append(Paragraph(
            f"<b>Evaluated Return Form:</b> {itr_form_result.get('form', 'ITR-1 (Sahaj)')} &bull; <b>Status:</b> Validated under Rule 12",
            normal_style
        ))
        story.append(Paragraph(
            itr_form_result.get("reason", "Eligible under Rule 12 based on taxpayer profile and disclosed sources of income."),
            normal_style
        ))

        # ---- DISCLAIMER ----
        story.append(Spacer(1, 0.6 * cm))
        story.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#ead9a7")))
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            "<b>⚠️ IMPORTANT DISCLAIMER</b><br/>"
            "This report is generated by ITR Learn &amp; Simulate, an educational "
            "MCA academic project. It is NOT an official Income Tax Return, "
            "acknowledgement, or filed return. Tax calculations are for "
            "learning purposes only. Always verify with a qualified tax "
            "professional and official Income Tax Department sources before "
            "actual filing. This application does not submit any data to "
            "the Government of India.",
            disclaimer_style
        ))

        doc.build(story)
        buffer.seek(0)

        response = make_response(buffer.read())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            f'attachment; filename="ITR_Practice_Report_{sim_id}.pdf"'
        )
        return response

    except ImportError:
        flash(
            "PDF generation requires the 'reportlab' library. "
            "Please install it: pip install reportlab",
            "error"
        )
        return redirect(url_for("report_view", sim_id=sim_id))

    except Exception as e:
        app.logger.error(f"PDF generation error: {e}")
        flash("Error generating PDF. Please try again.", "error")
        return redirect(url_for("report_view", sim_id=sim_id))


# ============================================================
# AI ASSISTANT
# ============================================================

@app.route("/ai-assistant")
@login_required
def ai_assistant():
    api_key_configured = bool(os.environ.get("GEMINI_API_KEY"))
    return render_template(
        "ai_assistant.html",
        api_key_configured=api_key_configured
    )


@app.route("/api/ai-assistant", methods=["POST"])
@login_required
def api_ai_assistant():
    """
    Backend API route for Gemini AI assistant.

    Data flow:
    User → ai_assistant.js → POST /api/ai-assistant →
    Flask → Gemini API → JSON response → JavaScript → UI

    Gemini is used ONLY for explanations.
    Tax calculations are NOT delegated to Gemini.
    """

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return jsonify({
            "success": False,
            "error": (
                "AI Assistant is not configured. "
                "Please set the GEMINI_API_KEY environment variable "
                "in the .env file."
            )
        })

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid request."})

    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"success": False, "error": "Message cannot be empty."})

    # Context for Gemini: always remind it of its role
    system_context = """You are an educational AI assistant for 
ITR Learn & Simulate, an MCA academic project for learning Indian 
Income Tax Return filing.

Your role:
- Explain ITR concepts, tax terms, deductions, and filing procedures.
- Explain results that were calculated by the rule-based tax engine.
- Help users understand the difference between tax regimes.
- Answer general ITR learning questions.

You must NOT:
- Calculate tax yourself — tax is calculated by the rule-based engine.
- Claim to file actual ITRs.
- Claim to access government portals or official tax records.
- Provide legal or financial advice.

Always remind users that this is an educational platform and they 
should verify information with official Income Tax Department sources.

Keep responses concise, clear, and beginner-friendly.
Use simple language suitable for students learning ITR filing."""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=20000)
        )

        config = types.GenerateContentConfig(
            system_instruction=system_context,
            temperature=0.7,
            max_output_tokens=1000
        )

        # Fallback list of models in case of temporary 503 high-demand spikes
        candidate_models = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-flash-latest",
            "gemini-3.8-flash"
        ]

        response_text = None
        last_error = None

        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_message,
                    config=config
                )
                if response and response.text:
                    response_text = response.text
                    break
            except Exception as model_err:
                last_error = model_err
                app.logger.warning(f"Model {model_name} attempt error: {model_err}")
                continue

        if response_text:
            return jsonify({
                "success": True,
                "response": response_text
            })
        else:
            raise last_error or Exception("No response received from Gemini API.")

    except ImportError:
        return jsonify({
            "success": False,
            "error": (
                "Gemini library not installed. "
                "Run: pip install google-genai"
            )
        })

    except Exception as e:
        app.logger.error(f"Gemini API error: {e}")
        return jsonify({
            "success": False,
            "error": (
                "AI Assistant is temporarily busy. "
                "Please ask your question again in a moment."
            )
        })


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    init_db()
    app.run(debug=True)