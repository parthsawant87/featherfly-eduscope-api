# eduscope_monitor.py — EduScope Quality Monitor (Adapted SPC)

import argparse, time, json
from datetime import datetime, date, timedelta
from pathlib import Path
import eduscope_config as cfg
from db_logger import get_recent

ALERT_LOG_PATH = Path(cfg.LOG_DIR) / "eduscope_alerts.json"

LOW_CONF_THRESHOLD = 0.75
ALERT_THRESHOLD    = 0.40   # if >40% predictions are low confidence → alert
MIN_SAMPLES        = 5


# ─────────────────────────────────────────────

def get_recent_stats(n=50):
    data = get_recent(n, module="eduscope")

    if not data:
        return None

    total = len(data)
    low_conf = sum(1 for r in data if r.get("confidence", 1.0) < LOW_CONF_THRESHOLD)

    return {
        "total": total,
        "low_conf": low_conf,
        "low_conf_rate": round(low_conf / total, 4) if total > 0 else 0
    }


# ─────────────────────────────────────────────

def log_alert(alert: dict):
    ALERT_LOG_PATH.parent.mkdir(exist_ok=True)

    alerts = []
    if ALERT_LOG_PATH.exists():
        with open(ALERT_LOG_PATH) as f:
            try:
                alerts = json.load(f)
            except:
                alerts = []

    alerts.append(alert)
    alerts = alerts[-100:]

    with open(ALERT_LOG_PATH, "w") as f:
        json.dump(alerts, f, indent=2)


# ─────────────────────────────────────────────

def check_system():
    stats = get_recent_stats()

    if not stats or stats["total"] < MIN_SAMPLES:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": "Not enough EduScope predictions yet"
        }

    rate = stats["low_conf_rate"]

    status = "STABLE"
    alert  = False
    message = ""

    if rate > ALERT_THRESHOLD:
        status = "UNSTABLE"
        alert = True
        message = (
            f"⚠ High uncertainty: {rate*100:.1f}% predictions low confidence. "
            "Model may be unreliable. Check dataset quality."
        )
    else:
        message = (
            f"✓ System stable. Low-confidence rate = {rate*100:.1f}%"
        )

    result = {
        "status": status,
        "alert": alert,
        "low_conf_rate": rate,
        "total_samples": stats["total"],
        "checked_at": datetime.now().isoformat(),
        "message": message
    }

    if alert:
        log_alert(result)

    return result


# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="EduScope Monitor")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=60)

    args = parser.parse_args()

    if args.watch:
        print("[monitor] Watching EduScope system...")
        while True:
            r = check_system()
            print(f"{r['checked_at']} | {r['status']} | {r['message']}")
            time.sleep(args.interval)
    else:
        r = check_system()
        print("\n[monitor] EduScope Status")
        print(f"Status: {r['status']}")
        print(f"Samples: {r.get('total_samples', 0)}")
        print(f"Low conf rate: {r.get('low_conf_rate', 0)}")
        print(f"Message: {r['message']}")


if __name__ == "__main__":
    main()