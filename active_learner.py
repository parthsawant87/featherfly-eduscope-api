# active_learner.py — EduScope + Sentinel Active Learning Queue
# Works for BOTH systems (handles specimen + predicted_class)

import sqlite3, json, csv, argparse, time
from datetime import datetime, date
from pathlib import Path
from typing import List
import eduscope_config as cfg
from db_logger import _get_conn

# 🔥 Tuned for EduScope (slightly higher threshold)
UNCERTAINTY_THRESHOLD = 0.75
MARGIN_THRESHOLD      = 0.15
MAX_QUEUE_SIZE        = 500

# ── SCHEMA ─────────────────────────────────────────────
AL_SCHEMA = """
CREATE TABLE IF NOT EXISTS review_queue (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        REAL    NOT NULL,
    filename         TEXT    NOT NULL,
    predicted_class  TEXT    NOT NULL,
    confidence       REAL    NOT NULL,
    probabilities    TEXT,
    uncertainty_type TEXT,
    status           TEXT DEFAULT 'pending',
    true_label       TEXT,
    reviewed_at      TEXT,
    notes            TEXT
);
CREATE INDEX IF NOT EXISTS idx_rq_status ON review_queue(status);
CREATE INDEX IF NOT EXISTS idx_rq_conf   ON review_queue(confidence);
"""

def _init_al_db():
    with _get_conn() as conn:
        conn.executescript(AL_SCHEMA)

_init_al_db()

# ──────────────────────────────────────────────────────
# 🔥 CORE FUNCTION (THIS IS THE IMPORTANT PART)
# ──────────────────────────────────────────────────────

def flag_if_uncertain(result: dict) -> bool:
    """
    Works for BOTH:
    - Sentinel → predicted_class
    - EduScope → specimen
    """

    conf  = result.get("confidence", 1.0)
    probs = result.get("probabilities") or {}
    fname = result.get("filename", "")

    # 🔥 SUPPORT BOTH SYSTEMS
    cls = result.get("predicted_class") or result.get("specimen", "UNKNOWN")

    uncertainty_type = None

    # ── Rule 1: Low confidence ──
    if conf < UNCERTAINTY_THRESHOLD:
        uncertainty_type = "low_confidence"

    # ── Rule 2: Close competition (Sentinel only usually) ──
    elif isinstance(probs, dict) and len(probs) >= 2:
        sorted_probs = sorted(probs.values(), reverse=True)
        margin = sorted_probs[0] - sorted_probs[1]
        if margin < MARGIN_THRESHOLD:
            uncertainty_type = "low_margin"

    # ── Rule 3 (NEW - EduScope): ambiguous text ──
    diagnosis = str(result.get("diagnosis", "")).lower()
    if any(word in diagnosis for word in ["uncertain", "possible", "likely"]):
        uncertainty_type = "ambiguous_text"

    if not uncertainty_type:
        return False

    try:
        with _get_conn() as conn:

            # Queue limit check
            count = conn.execute(
                "SELECT COUNT(*) FROM review_queue WHERE status='pending'"
            ).fetchone()[0]

            if count >= MAX_QUEUE_SIZE:
                return False

            # Duplicate check
            dup = conn.execute(
                "SELECT id FROM review_queue WHERE filename=? AND status='pending'",
                (fname,)
            ).fetchone()

            if dup:
                return False

            # Insert into queue
            conn.execute(
                """INSERT INTO review_queue
                   (timestamp, filename, predicted_class, confidence,
                    probabilities, uncertainty_type)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    time.time(),
                    fname,
                    cls,
                    conf,
                    json.dumps(probs),
                    uncertainty_type,
                )
            )

        return True

    except Exception as e:
        print(f"[al] flag_if_uncertain error: {e}")
        return False

# ──────────────────────────────────────────────────────

def get_review_queue(status: str = "pending", limit: int = 50) -> List[dict]:
    try:
        with _get_conn() as conn:
            if status == "all":
                rows = conn.execute(
                    "SELECT * FROM review_queue ORDER BY confidence ASC LIMIT ?",
                    (limit,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM review_queue WHERE status=? ORDER BY confidence ASC LIMIT ?",
                    (status, limit)
                ).fetchall()
            return [dict(r) for r in rows]
    except:
        return []

# ──────────────────────────────────────────────────────

def mark_reviewed(item_id: int, true_label: str, notes: str = ""):
    try:
        with _get_conn() as conn:
            conn.execute(
                """UPDATE review_queue
                   SET status='reviewed', true_label=?, reviewed_at=?, notes=?
                   WHERE id=?""",
                (true_label, datetime.now().isoformat(), notes, item_id)
            )
    except Exception as e:
        print(f"[al] mark_reviewed error: {e}")

# ──────────────────────────────────────────────────────

def get_queue_stats() -> dict:
    try:
        with _get_conn() as conn:
            total    = conn.execute("SELECT COUNT(*) FROM review_queue").fetchone()[0]
            pending  = conn.execute("SELECT COUNT(*) FROM review_queue WHERE status='pending'").fetchone()[0]
            reviewed = conn.execute("SELECT COUNT(*) FROM review_queue WHERE status='reviewed'").fetchone()[0]
            lc_count = conn.execute(
                "SELECT COUNT(*) FROM review_queue WHERE uncertainty_type='low_confidence' AND status='pending'"
            ).fetchone()[0]
            lm_count = conn.execute(
                "SELECT COUNT(*) FROM review_queue WHERE uncertainty_type='low_margin' AND status='pending'"
            ).fetchone()[0]

            return {
                "total": total,
                "pending": pending,
                "reviewed": reviewed,
                "low_confidence": lc_count,
                "low_margin": lm_count,
                "queue_pct_full": round(pending / MAX_QUEUE_SIZE * 100),
            }
    except:
        return {}

# ──────────────────────────────────────────────────────

def export_queue_csv(out_path: str = None):
    out = out_path or str(Path(cfg.RESULTS_DIR) / f"review_queue_{date.today()}.csv")
    items = get_review_queue("pending", limit=500)

    if not items:
        print("[al] Queue empty")
        return

    fields = ["id", "filename", "predicted_class", "confidence",
              "uncertainty_type", "true_label", "notes"]

    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(items)

    print(f"[al] ✓ Exported {len(items)} items → {out}")

# ──────────────────────────────────────────────────────

def import_reviewed_csv(csv_path: str):
    import shutil
    updated = 0

    with open(csv_path) as f:
        for row in csv.DictReader(f):

            if not row.get("true_label"):
                continue

            true_label = row["true_label"].strip().upper()

            if true_label not in cfg.CLASS_NAMES:
                continue

            mark_reviewed(int(row["id"]), true_label, row.get("notes", ""))

            src = Path(row["filename"])
            if src.exists():
                dst_dir = Path(cfg.DATASET_RAW) / true_label
                dst_dir.mkdir(exist_ok=True)
                shutil.copy2(src, dst_dir / src.name)

            updated += 1

    print(f"[al] ✓ Imported {updated} labels")

# ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Active Learner")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--import", dest="import_csv")

    args = parser.parse_args()

    if args.export:
        export_queue_csv()

    elif args.import_csv:
        import_reviewed_csv(args.import_csv)

    else:
        stats = get_queue_stats()
        print("\n[al] ACTIVE LEARNING")
        print(f"Pending: {stats.get('pending', 0)}")
        print(f"Reviewed: {stats.get('reviewed', 0)}")
        print(f"Low conf: {stats.get('low_confidence', 0)}")
        print(f"Queue %: {stats.get('queue_pct_full', 0)}%")

# ──────────────────────────────────────────────────────

if __name__ == "__main__":
    main()