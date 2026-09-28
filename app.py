"""
Jev AI Control Center - Flask application entry point.
"""
import logging

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from config.settings import (
    FLASK_SECRET_KEY, MONTHLY_AI_BUDGET,
    is_jev_configured, is_openai_configured, is_anthropic_configured,
)
from database import db
from services.jev import get_jev_decision
from services.router import resolve_model
from services.openai_provider import call_openai
from services.anthropic_provider import call_anthropic
from services.cost_calculator import calculate_cost

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("jev_app")

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

db.init_db()


def _budget_status():
    budget_row = db.get_company_budget()
    monthly_budget = budget_row["monthly_budget"] if budget_row else MONTHLY_AI_BUDGET
    summary = db.get_dashboard_summary()
    used = summary["total_cost"]
    remaining = monthly_budget - used
    pct_used = (used / monthly_budget * 100) if monthly_budget > 0 else 0

    if pct_used >= 100:
        level = "exceeded"
    elif pct_used >= 90:
        level = "critical"
    elif pct_used >= 70:
        level = "warning"
    else:
        level = "normal"

    return {
        "monthly_budget": monthly_budget,
        "used": used,
        "remaining": remaining,
        "pct_used": round(pct_used, 1),
        "level": level,
    }


@app.context_processor
def inject_globals():
    return {
        "jev_configured": is_jev_configured(),
        "openai_configured": is_openai_configured(),
        "anthropic_configured": is_anthropic_configured(),
    }


@app.route("/")
def dashboard():
    summary = db.get_dashboard_summary()
    providers = db.get_provider_overview()
    departments = db.get_department_usage()
    projects = db.get_project_usage()
    budget = _budget_status()
    recent = db.get_recent_activity(limit=10)

    return render_template(
        "dashboard.html",
        summary=summary,
        providers=providers,
        departments=departments,
        projects=projects,
        budget=budget,
        recent=recent,
    )


@app.route("/request", methods=["GET", "POST"])
def new_request():
    departments = db.get_departments()
    projects = db.get_projects()
    result = None

    if request.method == "POST":
        department = request.form.get("department", "").strip()
        project = request.form.get("project", "").strip()
        provider = request.form.get("provider", "openai").strip().lower()
        prompt = request.form.get("prompt", "").strip()

        if not prompt:
            flash("Please enter a prompt.", "danger")
            return redirect(url_for("new_request"))

        # 1. Jev decision layer analyses the task
        decision = get_jev_decision(prompt)

        # 2. Resolve model for the chosen provider + tier
        model = resolve_model(provider, decision["tier"])

        # 3. Call the provider (real or demo fallback)
        if provider == "anthropic":
            ai_result = call_anthropic(model, prompt)
        else:
            ai_result = call_openai(model, prompt)

        # 4. Calculate estimated cost
        cost = calculate_cost(
            provider, decision["tier"],
            ai_result["input_tokens"], ai_result["output_tokens"],
        )

        # 5. Persist everything to SQLite
        request_id = db.create_ai_request(
            department=department,
            project=project,
            provider=provider,
            model=model,
            prompt=prompt,
            response=ai_result["response"],
            complexity=decision["complexity"],
            route=decision["route"],
            human_review=decision["human_review"],
            status="completed",
            response_time=ai_result["response_time"],
        )
        db.add_token_usage(
            request_id,
            ai_result["input_tokens"],
            ai_result["output_tokens"],
            ai_result["total_tokens"],
        )
        db.add_cost_usage(request_id, cost)
        db.add_jev_decision(
            request_id,
            decision["complexity"],
            decision["route"],
            decision["confidence"],
            decision["decision_source"],
        )

        result = {
            "decision": decision,
            "provider": provider,
            "model": model,
            "ai_result": ai_result,
            "cost": cost,
            "department": department,
            "project": project,
            "prompt": prompt,
        }

    return render_template(
        "request.html",
        departments=departments,
        projects=projects,
        result=result,
    )


@app.route("/projects/add", methods=["POST"])
def add_project():
    name = request.form.get("name", "").strip()
    department = request.form.get("department", "").strip()
    if name:
        db.add_project(name, department)
        flash(f"Project '{name}' added.", "success")
    return redirect(request.referrer or url_for("new_request"))


@app.route("/history")
def history():
    filters = {
        "department": request.args.get("department") or None,
        "project": request.args.get("project") or None,
        "provider": request.args.get("provider") or None,
        "model": request.args.get("model") or None,
        "complexity": request.args.get("complexity") or None,
        "date": request.args.get("date") or None,
    }
    activity = db.get_recent_activity(filters=filters, limit=500)

    filter_options = {
        "departments": db.get_distinct_values("department"),
        "projects": db.get_distinct_values("project"),
        "providers": db.get_distinct_values("provider"),
        "models": db.get_distinct_values("model"),
        "complexities": db.get_distinct_values("complexity"),
    }

    return render_template(
        "history.html",
        activity=activity,
        filters=filters,
        filter_options=filter_options,
    )


@app.route("/departments")
def departments_page():
    departments = db.get_department_usage()
    return render_template("departments.html", departments=departments)


@app.route("/projects")
def projects_page():
    projects = db.get_project_usage()
    all_projects = db.get_projects()
    all_departments = db.get_departments()
    return render_template(
        "projects.html",
        projects=projects,
        all_projects=all_projects,
        all_departments=all_departments,
    )


@app.route("/cost-analytics")
def cost_analytics():
    providers = db.get_provider_overview()
    departments = db.get_department_usage()
    projects = db.get_project_usage()
    budget = _budget_status()
    return render_template(
        "cost_analytics.html",
        providers=providers,
        departments=departments,
        projects=projects,
        budget=budget,
    )


@app.route("/budget/update", methods=["POST"])
def update_budget():
    try:
        amount = float(request.form.get("monthly_budget", MONTHLY_AI_BUDGET))
        db.set_company_budget(amount)
        flash(f"Monthly budget updated to ${amount:,.2f}.", "success")
    except ValueError:
        flash("Invalid budget amount.", "danger")
    return redirect(url_for("dashboard"))


@app.route("/jev-decisions")
def jev_decisions_page():
    decisions = db.get_jev_decisions(limit=200)
    return render_template("jev_decisions.html", decisions=decisions)


@app.route("/settings")
def settings_page():
    return render_template("settings.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=True)
