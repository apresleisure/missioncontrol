#!/usr/bin/env python3
"""
ARM modular migration — atomic file writer + git commit/push.
Run from the root of your apres-ARM checkout:  python migrate_arm.py
"""
import os
import subprocess
import sys

FILES = {}

# ---------------------------------------------------------------------------
FILES["app/__init__.py"] = '''\
"""ARM application factory. Assembles Flask app, blueprints, and scheduler."""
import os
from flask import Flask, jsonify


def create_app():
    app = Flask(__name__)

    from app.routes.core_terminal import core_bp
    from app.routes.integrations import integrations_bp
    from app.routes.lore import lore_bp
    app.register_blueprint(core_bp)
    app.register_blueprint(integrations_bp)
    app.register_blueprint(lore_bp)

    try:
        from app.tasks.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:  # noqa: BLE001
        print(f"[ARM] scheduler not started: {e}")

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"service": "apres-arm", "status": "alive"})

    return app
'''

# ---------------------------------------------------------------------------
FILES["app/routes/__init__.py"] = ""
FILES["app/services/__init__.py"] = ""
FILES["app/tasks/__init__.py"] = ""

# ---------------------------------------------------------------------------
FILES["app/services/airtable_ops.py"] = '''\
"""Airtable data layer: table access, ledger logging, dynamic prompt fetch, compliance."""
import os
from pyairtable import Table

AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "appMriWKZylklqFDe")
CREATORS_ID = os.environ.get("CREATORS_TABLE_ID", "tblRX9Qn6XCV75Hsz")
MASTER_LEDGER_ID = os.environ.get("LEDGER_TABLE_ID", "tblNQNzevDnI1VgMO")
LEGEND_TRACKER_ID = os.environ.get("LEGEND_TRACKER_ID", "tblyqXwhVwq8PiPTF")
SYSTEM_CONFIG_ID = os.environ.get("SYSTEM_CONFIG_TABLE_ID", "")

GLOBAL_BRAND_FOOTER = (
    "1% of profits support mental health (current cycle), "
    "environmental and rotating initiatives."
)
FORBIDDEN_COPY = ["NAMI PLEDGE", "LeisureOS", "Lore_Score", "Apres Avatar", "Apr\\u00e8s"]

BASELINE_SYSTEM_PROMPT = (
    "You are the Apres Leisure ARM terminal assistant operating within the Leisurverse. "
    "Focus on all-terrain performance and celebration. Use the term 'Apres Alter Ego' "
    "for character branding. Be concise, accurate, and operationally focused. "
    "Never reference deprecated brand terms."
)


def get_table(table_id):
    api_key = os.environ.get("AIRTABLE_API_KEY") or os.environ.get("AIRTABLE_PAT", "")
    return Table(api_key, AIRTABLE_BASE_ID, table_id)


def compliance_check(text):
    """Return (ok, violations). Flags forbidden legacy terms in any outbound text."""
    if not text:
        return True, []
    lowered = text.lower()
    violations = [term for term in FORBIDDEN_COPY if term.lower() in lowered]
    return len(violations) == 0, violations


def log_to_ledger(action, details, status="Success"):
    """Write a structured audit entry to the Master Action Ledger."""
    ok, violations = compliance_check(details)
    if not ok:
        details = f"[COMPLIANCE_FLAG:{','.join(violations)}] " + details
    tbl = get_table(MASTER_LEDGER_ID)
    return tbl.create({
        "Friction Item": f"{action} [{status}]",
        "Notes": details,
    })


def get_active_system_prompt():
    """Fetch the latest System_Config prompt from Airtable; fall back to baseline."""
    if not SYSTEM_CONFIG_ID:
        return BASELINE_SYSTEM_PROMPT
    try:
        tbl = get_table(SYSTEM_CONFIG_ID)
        records = tbl.all(max_records=1, sort=["-Created"])
        if records:
            prompt = records[0]["fields"].get("System_Prompt", "").strip()
            if prompt:
                return prompt
    except Exception as e:  # noqa: BLE001
        print(f"[ARM] system prompt fetch failed, using baseline: {e}")
    return BASELINE_SYSTEM_PROMPT


def ping_airtable():
    """Lightweight connectivity probe for /status. Returns (connected, detail)."""
    try:
        get_table(CREATORS_ID).all(max_records=1)
        return True, "Airtable reachable"
    except Exception as e:  # noqa: BLE001
        return False, f"Airtable unreachable: {e}"
'''

# ---------------------------------------------------------------------------
FILES["app/services/anthropic_ai.py"] = '''\
"""Claude API layer. Compiles the active dynamic system prompt on every call."""
import os
import anthropic

from app.services.airtable_ops import get_active_system_prompt

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
MAX_TOKENS = int(os.environ.get("ANTHROPIC_MAX_TOKENS", "1024"))


def _client():
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def run_claude(user_text):
    """Send user_text to Claude using the dynamically fetched system prompt."""
    system_prompt = get_active_system_prompt()
    message = _client().messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_text}],
    )
    return message.content[0].text if message.content else "No response."
'''

# ---------------------------------------------------------------------------
FILES["app/routes/core_terminal.py"] = '''\
"""Core terminal: WhatsApp reply webhook and admin command router."""
import os
from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator

from app.services.airtable_ops import ping_airtable, get_active_system_prompt
from app.services.anthropic_ai import run_claude

core_bp = Blueprint("core", __name__)

AUTHORISED_NUMBERS = [
    n.strip() for n in os.environ.get("AUTHORISED_WA_NUMBERS", "").split(",") if n.strip()
]


def validate_twilio_request(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        validator = RequestValidator(os.environ.get("TWILIO_AUTH_TOKEN", ""))
        signature = request.headers.get("X-Twilio-Signature", "")
        if not validator.validate(request.url, request.form.to_dict(), signature):
            return jsonify({"error": "Invalid Twilio signature"}), 403
        return f(*args, **kwargs)
    return decorated


def _is_authorised(number):
    return bool(AUTHORISED_NUMBERS) and number in AUTHORISED_NUMBERS


@core_bp.route("/whatsapp/reply", methods=["POST"])
@validate_twilio_request
def whatsapp_reply():
    from_number = request.form.get("From", "")
    body = request.form.get("Body", "").strip()
    resp = MessagingResponse()

    if AUTHORISED_NUMBERS and not _is_authorised(from_number):
        resp.message("Unauthorized.")
        return str(resp), 200, {"Content-Type": "text/xml"}

    if body.lower().startswith("/status"):
        connected, detail = ping_airtable()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        summary = (
            f"ARM STATUS\\n"
            f"Service: online\\n"
            f"Airtable: {'OK' if connected else 'SEVERED'} ({detail})\\n"
            f"Time: {now}"
        )
        resp.message(summary)
        return str(resp), 200, {"Content-Type": "text/xml"}

    if body.lower().startswith("/test-prompt"):
        try:
            reply = run_claude(
                "Reply with a one-line confirmation that the ARM prompt route is live."
            )
            resp.message(reply[:200])
        except Exception as e:  # noqa: BLE001
            resp.message(f"test-prompt error: {e}")
        return str(resp), 200, {"Content-Type": "text/xml"}

    if not os.environ.get("ANTHROPIC_API_KEY", ""):
        resp.message("ARM terminal offline \\u2014 ANTHROPIC_API_KEY not set.")
        return str(resp), 200, {"Content-Type": "text/xml"}
    try:
        resp.message(run_claude(body))
    except Exception as e:  # noqa: BLE001
        resp.message(f"ARM Claude error: {e}")
    return str(resp), 200, {"Content-Type": "text/xml"}


@core_bp.route("/whatsapp/command", methods=["POST"])
def whatsapp_command_parser():
    payload = request.get_json(force=True) or {}
    command = payload.get("command", "").strip().lower()
    from_number = payload.get("from", "")

    if AUTHORISED_NUMBERS and not _is_authorised(from_number):
        return jsonify({"error": "Unauthorized"}), 403

    if command == "status":
        connected, detail = ping_airtable()
        return jsonify({
            "status": "ARM online",
            "airtable_connected": connected,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    if command.startswith("lore "):
        from app.services.airtable_ops import get_table, CREATORS_ID
        creator_id = command.split(" ", 1)[1].strip()
        try:
            record = get_table(CREATORS_ID).get(creator_id)
            return jsonify({
                "creator_id": creator_id,
                "Ledger_Standing": record["fields"].get("Ledger_Standing", 0),
            })
        except Exception as e:  # noqa: BLE001
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Unknown command", "command": command}), 400
'''

# ---------------------------------------------------------------------------
FILES["app/routes/integrations.py"] = '''\
"""Integrations: QR Tiger scans, margin compute, Apify ingest, Replit deprecation."""
import os
import json
import urllib.request as urlreq

from flask import Blueprint, request, jsonify

from app.services.airtable_ops import (
    get_table,
    log_to_ledger,
    CREATORS_ID,
    LEGEND_TRACKER_ID,
)

integrations_bp = Blueprint("integrations", __name__)

REVERSE_LOGISTICS_FEE = 7.00
MARGIN_FLOOR = 5.00
POINTS_PER_DOLLAR = 10
VANGUARD_MULTIPLIER = 1.5
STATE_COMPUTED = "Computed"
STATE_FLAGGED = "Flagged for Review"


@integrations_bp.route("/api/ops/qr-scan", methods=["POST"])
def qr_scan():
    payload = request.get_json(force=True) or {}
    creator_id = payload.get("creator_id", "")
    scan_data = payload.get("scan_data", {})
    if not creator_id:
        return jsonify({"error": "creator_id required"}), 400

    points_reward = int(os.environ.get("QR_SCAN_POINTS", "50"))
    vanguard_wh = os.environ.get("MAKE_VANGUARD_WEBHOOK_URL", "")

    try:
        creators_tbl = get_table(CREATORS_ID)
        record = creators_tbl.get(creator_id)
        current = int(record["fields"].get("Ledger_Standing", 0))
        new_score = current + points_reward
        creators_tbl.update(creator_id, {"Ledger_Standing": new_score})
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"Airtable update failed: {e}"}), 500

    klaviyo_result = None
    if vanguard_wh:
        try:
            data = json.dumps({
                "creator_id": creator_id,
                "event": "qr_scan",
                "points_awarded": points_reward,
                "new_score": new_score,
                "scan_data": scan_data,
            }).encode("utf-8")
            req = urlreq.Request(
                vanguard_wh,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlreq.urlopen(req, timeout=5) as r:
                klaviyo_result = r.read().decode("utf-8")
        except Exception as e:  # noqa: BLE001
            klaviyo_result = f"webhook_error: {e}"

    try:
        log_to_ledger(
            action="qr_scan",
            details=f"creator={creator_id} +{points_reward}pts new_total={new_score} klaviyo={klaviyo_result}",
            status="Success",
        )
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "creator_id": creator_id,
        "points_awarded": points_reward,
        "new_score": new_score,
        "klaviyo": klaviyo_result,
    })


@integrations_bp.route("/compute/margin", methods=["POST"])
def compute_margin():
    data = request.get_json(force=True) or {}
    cost = float(data.get("cost", 0))
    price = float(data.get("price", 0))
    returns_count = int(data.get("returns_count", 0))

    gross_margin = price - cost
    returns_cost = returns_count * REVERSE_LOGISTICS_FEE
    net_margin = gross_margin - returns_cost
    margin_pct = (net_margin / price * 100) if price else 0
    flag = net_margin < MARGIN_FLOOR

    record = {
        "cost": cost,
        "price": price,
        "gross_margin": round(gross_margin, 2),
        "returns_cost": round(returns_cost, 2),
        "net_margin": round(net_margin, 2),
        "margin_pct": round(margin_pct, 2),
        "state": STATE_FLAGGED if flag else STATE_COMPUTED,
    }

    try:
        get_table(LEGEND_TRACKER_ID).create(record)
    except Exception as e:  # noqa: BLE001
        record["airtable_error"] = str(e)

    return jsonify(record)


@integrations_bp.route("/api/ops/apify-scrape", methods=["POST"])
def apify_scrape():
    data = request.get_json(force=True) or {}
    try:
        log_to_ledger(
            action="apify_scrape_ingest",
            details=json.dumps(data)[:500],
            status="Received",
        )
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True, "received": len(data)})


@integrations_bp.route("/api/ops/deprecate-repls", methods=["POST"])
def deprecate_repls():
    legacy_engines = [
        {"name": "Catalog-Forge", "repl_id": "catalog-forge", "status": "decommissioned"},
        {"name": "LeisureOS-Core", "repl_id": "leisureos-core", "status": "decommissioned"},
        {"name": "Vanguard-Processor", "repl_id": "vanguard-processor", "status": "decommissioned"},
    ]
    results = []
    for engine in legacy_engines:
        try:
            log_to_ledger(
                action="replit_deprecation",
                details=f"engine={engine['name']} repl_id={engine['repl_id']} status=decommissioned",
                status="Decommissioned",
            )
            results.append({"engine": engine["name"], "ok": True})
        except Exception as e:  # noqa: BLE001
            results.append({"engine": engine["name"], "ok": False, "error": str(e)})

    return jsonify({
        "ok": all(r["ok"] for r in results),
        "engines": results,
        "message": "Legacy Replit engines flagged as decommissioned in Master Action Ledger.",
    })
'''

# ---------------------------------------------------------------------------
FILES["app/routes/lore.py"] = '''\
"""Lore award route. Gamification framework \\u2014 preserved through migration."""
from flask import Blueprint, request, jsonify

from app.services.airtable_ops import get_table, log_to_ledger, CREATORS_ID

lore_bp = Blueprint("lore", __name__)

POINTS_PER_DOLLAR = 10
VANGUARD_MULTIPLIER = 1.5


@lore_bp.route("/api/lore/award", methods=["POST"])
def lore_award():
    data = request.get_json(force=True) or {}
    creator_id = data.get("creator_id", "")
    purchase = float(data.get("purchase_amount", 0))
    is_vanguard = bool(data.get("is_vanguard", False))

    if not creator_id:
        return jsonify({"error": "creator_id required"}), 400

    base_points = int(purchase * POINTS_PER_DOLLAR)
    points = int(base_points * VANGUARD_MULTIPLIER) if is_vanguard else base_points

    try:
        tbl = get_table(CREATORS_ID)
        record = tbl.get(creator_id)
        current = int(record["fields"].get("Ledger_Standing", 0))
        new_score = current + points
        tbl.update(creator_id, {"Ledger_Standing": new_score})
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500

    try:
        log_to_ledger(
            action="lore_award",
            details=f"creator={creator_id} purchase=${purchase} +{points}pts new_total={new_score}",
            status="Success",
        )
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "creator_id": creator_id,
        "points": points,
        "new_score": new_score,
    })
'''

# ---------------------------------------------------------------------------
FILES["app/tasks/scheduler.py"] = '''\
"""APScheduler background loop: macro status heartbeat every 4 hours."""
import os

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.airtable_ops import log_to_ledger

_scheduler = None


def _status_heartbeat():
    try:
        log_to_ledger(
            action="status_heartbeat",
            details="ARM service heartbeat \\u2014 all systems nominal.",
            status="Heartbeat",
        )
    except Exception:
        pass


def start_scheduler():
    """Boot the heartbeat cron once. Guarded so multi-worker setups don't duplicate it."""
    global _scheduler

    if os.environ.get("ARM_SCHEDULER_BOOTED") == "1":
        return None
    os.environ["ARM_SCHEDULER_BOOTED"] = "1"

    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_status_heartbeat, "interval", minutes=240)
    _scheduler.start()
    return _scheduler
'''

# ---------------------------------------------------------------------------
FILES["main.py"] = '''\
"""ARM entry point. Thin bootstrap over the modular app package."""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
'''

# ---------------------------------------------------------------------------
FILES_TO_DELETE = ["api/ops.py", "api/lore.py"]

COMMIT_MSG = "Refactor: migrate monolith main.py to modular app/ package; retire api/ops.py & api/lore.py"


def run(cmd):
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main():
    if not os.path.isdir(".git"):
        sys.exit("ERROR: run this from the root of your apres-ARM git checkout (.git not found).")

    # 1. Write all files
    for path, content in FILES.items():
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        with open(path, "w", encoding="utf-8", newline="\\n") as f:
            f.write(content)
        print(f"  wrote {path} ({len(content)} bytes)")

    # 2. Local syntax gate — compile everything before we commit
    py_files = [p for p in FILES if p.endswith(".py")] + ["main.py"]
    print("\\nRunning py_compile syntax gate...")
    import py_compile
    for p in set(py_files):
        try:
            py_compile.compile(p, doraise=True)
            print(f"  OK  {p}")
        except py_compile.PyCompileError as e:
            sys.exit(f"SYNTAX ERROR in {p}:\\n{e}")

    # 3. Remove retired files
    for path in FILES_TO_DELETE:
        if os.path.exists(path):
            run(["git", "rm", path])
        else:
            print(f"  (skip) {path} not present")

    # 4. Stage, commit, push
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", COMMIT_MSG])
    run(["git", "push", "origin", "main"])
    print("\\nDone. Render should auto-deploy on this push.")


if __name__ == "__main__":
    main()
    