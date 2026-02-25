from flask import Flask, jsonify, render_template_string, request, redirect, url_for, session, send_file
import pandas as pd
import os
import math
import sqlite3
import io
from datetime import datetime
import shutil

try:
    import process_export
except ImportError:
    process_export = None

app = Flask(__name__)
app.secret_key = os.environ.get("DASHBOARD_SECRET_KEY", "change-this-key")

DATA_FILE_ENV = "EXCEL_DASHBOARD_FILE"


def get_data_file():
    """
    Tentukan lokasi file Excel yang akan dibaca dashboard.
    - Jika EXCEL_DASHBOARD_FILE diset, gunakan itu.
    - Jika tidak, gunakan file default di folder export: dashboard_export.xlsx
    """
    env_path = os.environ.get(DATA_FILE_ENV)
    if env_path:
        return env_path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "export", "dashboard_export.xlsx")


def load_dataframe():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data_pipeline.sqlite")
    merged_path = os.path.join(base_dir, "merged_current.xlsx")
    
    df = pd.DataFrame()
    
    if os.path.exists(db_path):
        try:
            print(f"[web_app] Loading from SQLite: {db_path}", flush=True)
            conn = sqlite3.connect(db_path)
            # Get all columns but filter out internal ones in the query if possible, 
            # but pandas read_sql_query is easier with * and we filter later in this function.
            # To strictly follow "hide from query", we can fetch columns first.
            cursor = conn.execute("SELECT * FROM records_current LIMIT 0")
            all_cols = [description[0] for description in cursor.description]
            exclude_cols = ["row_hash", "ingest_timestamp", "source_file", "ExportSource", "ExportTimestamp", "ExportUser"]
            select_cols = [f'"{c}"' for c in all_cols if c not in exclude_cols]
            query = f"SELECT {', '.join(select_cols)} FROM records_current"
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            if not df.empty:
                print(f"[web_app] Loaded dataframe from DB with shape: {df.shape}", flush=True)
                # Success from DB
            else:
                # DB exists but empty, try excel
                raise ValueError("DB empty")
        except Exception as e:
            print(f"[web_app] DB loading skipped/failed: {e}", flush=True)
            df = pd.DataFrame()
            
    if df.empty and os.path.exists(merged_path):
        try:
            print(f"[web_app] Loading merged snapshot: {merged_path}", flush=True)
            excel_obj = pd.read_excel(merged_path, sheet_name=None)
            if isinstance(excel_obj, dict):
                df = excel_obj.get("Data", next(iter(excel_obj.values())))
            else:
                df = excel_obj
            print(f"[web_app] Loaded dataframe from merged snapshot with shape: {df.shape}", flush=True)
        except Exception as e:
            print(f"[web_app] Error reading merged snapshot: {e}", flush=True)
            
    if df.empty:
        path = get_data_file()
        print(f"[web_app] Fallback loading from: {path}", flush=True)
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if os.path.exists(path):
            try:
                excel_obj = pd.read_excel(path, sheet_name=None)
                if isinstance(excel_obj, dict):
                    df = excel_obj.get("Data", next(iter(excel_obj.values())))
                else:
                    df = excel_obj
                print(f"[web_app] Loaded dataframe with shape: {df.shape}", flush=True)
            except Exception as e:
                print(f"[web_app] Error reading Excel file: {e}", flush=True)

    if not df.empty:
        # 1. Clean up "REVENUE (ACTUAL)" column - REMOVE PERMANENTLY
        if "REVENUE (ACTUAL)" in df.columns:
            print("[web_app] Removing 'REVENUE (ACTUAL)' column from dataframe", flush=True)
            df = df.drop(columns=["REVENUE (ACTUAL)"])

        # 2. Rename column "REVENUE INCREMENTAL 1" to "INCREMENTAL 1" if exists
        if "REVENUE INCREMENTAL 1" in df.columns:
            print("[web_app] Found 'REVENUE INCREMENTAL 1', renaming to 'INCREMENTAL 1'", flush=True)
            if "INCREMENTAL 1" in df.columns:
                df["INCREMENTAL 1"] = df["INCREMENTAL 1"].fillna(df["REVENUE INCREMENTAL 1"])
                df = df.drop(columns=["REVENUE INCREMENTAL 1"])
            else:
                df = df.rename(columns={"REVENUE INCREMENTAL 1": "INCREMENTAL 1"})
        
        # 3. Reorder and Filter Columns
        desired_order = [
            "NOP", "PROGRAM", "KATEGORI", "JUSTIFIKASI", "PROPOSAL", "BUDGET", 
            "REVENUE", "COST", "PROFIT", "INCREMENTAL 1", "INCREMENTAL 2", 
            "INCREMENTAL 3", "STATUS", "PILOT", "DRIVEN PROGRAM", "ASSIGN BY", 
            "APPROVED BY"
        ]
        
        # Internal columns to hide from UI and Exports
        exclude_cols = ["row_hash", "ingest_timestamp", "source_file", "ExportSource", "ExportTimestamp", "ExportUser"]
        
        cols_to_use = [c for c in desired_order if c in df.columns]
        # Any other columns that are not internal
        other_cols = [c for c in df.columns if c not in cols_to_use and c not in exclude_cols]
        df = df[cols_to_use + other_cols]
        
    return df


def merge_to_dashboard_excel_web(df_new, user_id: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    export_dir = os.path.join(base_dir, "export")
    backup_dir = os.path.join(export_dir, "backup")
    
    # Ensure target directories exist
    os.makedirs(backup_dir, exist_ok=True)
    
    dashboard_path = os.path.join(export_dir, "dashboard_export.xlsx")
    
    if df_new is None or df_new.empty:
        print("[web_app] merge_to_dashboard_excel_web: no data to merge", flush=True)
        return dashboard_path, None
        
    df_new = df_new.copy()
    ts = datetime.utcnow().isoformat()
    
    # SYNC ENGINE INTEGRATION
    sync_results = None
    if process_export is not None:
        try:
            conn = process_export.connect_db()
            # Ensure schema is up to date
            process_export.ensure_schema(conn, list(df_new.columns))
            
            # Perform field-level synchronization
            sync_results = process_export.detect_and_sync_changes(conn, df_new, source_file=f"web_export_{user_id}")
            conn.close()
            
            if sync_results["modifications"]:
                print(f"[web_app] SYNC: {len(sync_results['modifications'])} modifications detected.", flush=True)
        except Exception as e:
            print(f"[web_app] Sync Engine failed: {e}", flush=True)

    # Update the physical Excel file for dashboard fallback
    if os.path.exists(dashboard_path):
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"dashboard_export_backup_{timestamp}.xlsx"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        try:
            shutil.copy2(dashboard_path, backup_path)
            print(f"[web_app] Backup created: {backup_path}", flush=True)
        except Exception as e:
            print(f"[web_app] Error creating backup: {e}", flush=True)
            
        try:
            # Load latest data from DB if sync was successful, otherwise fallback to Excel merge
            if sync_results:
                conn = process_export.connect_db()
                combined = process_export.load_current(conn)
                conn.close()
            else:
                excel_obj = pd.read_excel(dashboard_path, sheet_name=None)
                df_old = excel_obj.get("Data", next(iter(excel_obj.values()))) if isinstance(excel_obj, dict) else excel_obj
                combined = pd.concat([df_old, df_new], ignore_index=True).drop_duplicates(subset=["NOP"], keep="last")
        except Exception as e:
            print(f"[web_app] Error reading existing file: {e}", flush=True)
            combined = df_new
    else:
        combined = df_new
        
    try:
        # Hide internal columns from the physical file on disk too
        exclude_cols = ["row_hash", "ingest_timestamp", "source_file", "ExportSource", "ExportTimestamp", "ExportUser"]
        df_disk = combined.drop(columns=[c for c in exclude_cols if c in combined.columns])
        
        with pd.ExcelWriter(dashboard_path, engine="openpyxl") as writer:
            df_disk.to_excel(writer, index=False, sheet_name="Data")
        
        print(f"[web_app] Dashboard export updated: {dashboard_path}", flush=True)
    except Exception as e:
        print(f"[web_app] Error saving file: {e}", flush=True)
        
    return dashboard_path, sync_results


def login_required(view):
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    wrapped.__name__ = view.__name__
    return wrapped


def can_export():
    user = session.get("username")
    allowed = os.environ.get("EXPORT_ALLOWED_USERS", "admin")
    allowed_list = [x.strip() for x in allowed.split(",") if x.strip()]
    return user in allowed_list


@app.route("/api/sync/rollback", methods=["POST"])
@login_required
def rollback_sync():
    if not can_export():
        return jsonify({"error": "Not allowed"}), 403
        
    data = request.json
    nop = data.get("nop")
    if not nop:
        return jsonify({"error": "NOP is required"}), 400
        
    if process_export is None:
        return jsonify({"error": "Sync engine not available"}), 500
        
    try:
        conn = process_export.connect_db()
        success = process_export.rollback_record(conn, str(nop))
        conn.close()
        
        if success:
            # Also update the merged Excel snapshot
            conn = process_export.connect_db()
            out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export", "dashboard_export.xlsx")
            process_export.export_merged_snapshot(conn, out_file)
            conn.close()
            return jsonify({"message": f"Rollback successful for NOP: {nop}"}), 200
        else:
            return jsonify({"error": f"No rollback data found for NOP: {nop}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def dataframe_to_json_rows(df: pd.DataFrame):
    # Columns to exclude from JSON output
    exclude_cols = ["row_hash", "ingest_timestamp", "source_file", "ExportSource", "ExportTimestamp", "ExportUser"]
    
    records = []
    for rec in df.to_dict(orient="records"):
        new_rec = {}
        for key, value in rec.items():
            if key in exclude_cols:
                continue
            if value is None:
                new_rec[key] = None
            elif isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                new_rec[key] = None
            else:
                new_rec[key] = value
        records.append(new_rec)
    return records


LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Dashboard Login</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: radial-gradient(circle at top, #1f2937 0, #020617 55%, #000 100%);
            color: #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .card {
            background: rgba(15,23,42,0.96);
            border-radius: 18px;
            box-shadow: 0 18px 45px rgba(0,0,0,0.6);
            padding: 32px 28px;
            width: 100%;
            max-width: 380px;
            backdrop-filter: blur(18px);
            border: 1px solid rgba(148,163,184,0.35);
        }
        .title {
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 4px;
            letter-spacing: 0.04em;
        }
        .subtitle {
            font-size: 0.9rem;
            color: #9ca3af;
            margin-bottom: 24px;
        }
        label {
            font-size: 0.82rem;
            color: #9ca3af;
            display: block;
            margin-bottom: 6px;
        }
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 10px 12px;
            border-radius: 10px;
            border: 1px solid rgba(55,65,81,0.9);
            background: rgba(15,23,42,0.9);
            color: #e5e7eb;
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.12s ease;
        }
        input[type="text"]:focus,
        input[type="password"]:focus {
            border-color: #38bdf8;
            box-shadow: 0 0 0 1px rgba(56,189,248,0.45);
            transform: translateY(-1px);
        }
        .field {
            margin-bottom: 16px;
        }
        .btn {
            width: 100%;
            padding: 10px 14px;
            border-radius: 999px;
            border: none;
            background: linear-gradient(135deg, #0ea5e9, #6366f1);
            color: #f9fafb;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            letter-spacing: 0.03em;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
        }
        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 30px rgba(56,189,248,0.45);
            filter: brightness(1.05);
        }
        .btn:active {
            transform: translateY(0);
            box-shadow: none;
        }
        .error {
            color: #f97373;
            font-size: 0.8rem;
            margin-bottom: 10px;
            min-height: 1em;
        }
        .hint {
            font-size: 0.78rem;
            color: #6b7280;
            margin-top: 12px;
        }
        @media (max-width: 480px) {
            .card {
                margin: 0 16px;
                padding: 24px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="title">Masuk ke Dashboard</div>
        <div class="subtitle">Gunakan akun yang diizinkan untuk mengakses data visualisasi.</div>
        <form method="post">
            <div class="error">{{ error }}</div>
            <div class="field">
                <label for="username">Username</label>
                <input id="username" name="username" type="text" autocomplete="username" required>
            </div>
            <div class="field">
                <label for="password">Password</label>
                <input id="password" name="password" type="password" autocomplete="current-password" required>
            </div>
            <button class="btn" type="submit">
                <span>Masuk</span>
            </button>
        </form>
        <div class="hint">
            Default: admin / admin123. Ubah melalui variabel lingkungan DASHBOARD_USER dan DASHBOARD_PASSWORD.
        </div>
    </div>
</body>
</html>
"""


DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Excel Data Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #020617;
            --bg-elevated: #020617;
            --accent: #0ea5e9;
            --accent-soft: rgba(56,189,248,0.18);
            --accent-strong: #38bdf8;
            --accent-secondary: #6366f1;
            --text: #e5e7eb;
            --muted: #9ca3af;
            --border-subtle: rgba(148,163,184,0.35);
            --danger: #f97373;
            --card-radius: 18px;
            --transition-fast: 0.16s ease;
        }
        * {
            box-sizing: border-box;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: radial-gradient(circle at top, #1f2937 0, #020617 55%, #000 100%);
            color: var(--text);
            min-height: 100vh;
        }
        .shell {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .navbar {
            position: sticky;
            top: 0;
            z-index: 40;
            backdrop-filter: blur(18px);
            background: linear-gradient(to bottom, rgba(15,23,42,0.9), rgba(15,23,42,0.82), rgba(15,23,42,0.2));
            border-bottom: 1px solid rgba(30,64,175,0.55);
        }
        .nav-inner {
            max-width: 1200px;
            margin: 0 auto;
            padding: 10px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .brand-logo {
            width: 30px;
            height: 30px;
            border-radius: 999px;
            background: radial-gradient(circle at 30% 30%, #e5e7eb 0, #38bdf8 30%, #6366f1 70%, #020617 100%);
            box-shadow: 0 0 0 1px rgba(148,163,184,0.35), 0 12px 30px rgba(15,23,42,0.8);
        }
        .brand-text {
            display: flex;
            flex-direction: column;
        }
        .brand-title {
            font-size: 0.95rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .brand-subtitle {
            font-size: 0.75rem;
            color: var(--muted);
        }
        .nav-links {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .nav-link {
            font-size: 0.85rem;
            color: var(--muted);
            text-decoration: none;
            padding: 6px 10px;
            border-radius: 999px;
            transition: color var(--transition-fast), background var(--transition-fast), transform var(--transition-fast);
        }
        .nav-link.active {
            color: var(--text);
            background: rgba(15,23,42,0.9);
            box-shadow: 0 0 0 1px rgba(55,65,81,0.9);
        }
        .nav-link:hover {
            color: var(--accent-strong);
            transform: translateY(-1px);
        }
        .nav-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .pill {
            font-size: 0.75rem;
            padding: 4px 9px;
            border-radius: 999px;
            border: 1px solid rgba(148,163,184,0.38);
            color: var(--muted);
        }
        .nav-toggle {
            display: none;
            background: transparent;
            border: none;
            color: var(--text);
            cursor: pointer;
            padding: 4px;
        }
        .nav-toggle span {
            display: block;
            width: 18px;
            height: 2px;
            background: var(--text);
            margin: 3px 0;
            border-radius: 999px;
            transition: transform var(--transition-fast), opacity var(--transition-fast);
        }
        .nav-mobile-menu {
            display: none;
            flex-direction: column;
            padding: 8px 18px 14px;
            gap: 6px;
            border-top: 1px solid rgba(31,41,55,0.9);
        }
        .nav-mobile-menu a {
            font-size: 0.87rem;
            color: var(--muted);
            text-decoration: none;
            padding: 8px 10px;
            border-radius: 10px;
            background: rgba(15,23,42,0.95);
        }
        .nav-mobile-menu a.active {
            color: var(--text);
            background: rgba(30,64,175,0.9);
        }
        .nav-mobile-menu a:hover {
            color: var(--accent-strong);
        }
        .main {
            flex: 1;
        }
        .page {
            max-width: 1200px;
            margin: 0 auto;
            padding: 18px;
        }
        .layout {
            display: grid;
            grid-template-columns: 2.1fr 1.6fr;
            gap: 18px;
            align-items: flex-start;
        }
        .card {
            background: radial-gradient(circle at top left, rgba(56,189,248,0.18) 0, rgba(15,23,42,0.98) 45%, rgba(15,23,42,0.98) 100%);
            border-radius: var(--card-radius);
            border: 1px solid var(--border-subtle);
            box-shadow: 0 16px 40px rgba(15,23,42,0.86);
            padding: 18px 18px 16px;
            position: relative;
            overflow: hidden;
        }
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .card-title {
            font-size: 0.95rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .card-subtitle {
            font-size: 0.8rem;
            color: var(--muted);
        }
        .badge {
            font-size: 0.75rem;
            padding: 4px 8px;
            border-radius: 999px;
            background: rgba(15,23,42,0.9);
            border: 1px solid rgba(148,163,184,0.55);
        }
        .controls-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 10px;
        }
        .control-group {
            flex: 1 1 140px;
            min-width: 0;
        }
        .control-label {
            font-size: 0.78rem;
            color: var(--muted);
            margin-bottom: 4px;
        }
        select,
        input[type="text"] {
            width: 100%;
            padding: 6px 8px;
            border-radius: 999px;
            border: 1px solid rgba(55,65,81,0.9);
            background: rgba(15,23,42,0.9);
            color: var(--text);
            font-size: 0.81rem;
            outline: none;
            transition: border-color var(--transition-fast), box-shadow var(--transition-fast), transform var(--transition-fast);
        }
        select:focus,
        input[type="text"]:focus {
            border-color: var(--accent-strong);
            box-shadow: 0 0 0 1px rgba(56,189,248,0.45);
            transform: translateY(-1px);
        }
        .btn {
            border-radius: 999px;
            border: none;
            cursor: pointer;
            padding: 8px 12px;
            font-size: 0.78rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            letter-spacing: 0.03em;
            transition: transform var(--transition-fast), box-shadow var(--transition-fast), filter var(--transition-fast), background var(--transition-fast);
        }
        .btn-primary {
            background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
            color: #f9fafb;
        }
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 30px rgba(56,189,248,0.45);
            filter: brightness(1.06);
        }
        .btn-ghost {
            background: rgba(15,23,42,0.95);
            color: var(--muted);
            border: 1px solid rgba(55,65,81,0.9);
        }
        .btn-ghost:hover {
            color: var(--accent-strong);
            border-color: rgba(56,189,248,0.6);
            background: rgba(15,23,42,0.98);
        }
        .btn-outline {
            background: transparent;
            color: var(--accent-strong);
            border: 1px solid rgba(56,189,248,0.7);
        }
        .btn-outline:hover {
            background: rgba(15,23,42,0.98);
        }
        .btn-danger {
            background: var(--danger);
            color: white;
            padding: 6px 10px;
            font-size: 0.75rem;
        }
        .btn-danger:hover:not(:disabled) {
            filter: brightness(1.1);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(249, 115, 115, 0.4);
        }
        .btn-danger:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            filter: grayscale(1);
        }
        .clear-sort-btn {
            background: #4b5563;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 2px 6px;
            font-size: 0.7rem;
            cursor: pointer;
            margin-left: 6px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
            vertical-align: middle;
        }
        .clear-sort-btn:hover {
            background: #374151;
        }
        .btn-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .table-wrapper {
            margin-top: 8px;
            border-radius: 14px;
            border: 1px solid rgba(31,41,55,0.95);
            overflow: hidden;
            background: radial-gradient(circle at top left, rgba(15,23,42,1) 0, rgba(15,23,42,0.98) 45%, rgba(15,23,42,0.96) 100%);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.78rem;
        }
        thead {
            background: radial-gradient(circle at top, rgba(15,23,42,1) 0, rgba(15,23,42,0.98) 30%, rgba(15,23,42,0.96) 100%);
        }
        th,
        td {
            padding: 7px 9px;
            text-align: left;
            white-space: nowrap;
        }
        th {
            position: sticky;
            top: 0;
            z-index: 5;
            font-weight: 500;
            color: var(--muted);
            cursor: pointer;
            border-bottom: 1px solid rgba(31,41,55,0.9);
            user-select: none;
        }
        th.sort-asc::after {
            content: "▲";
            font-size: 0.6rem;
            margin-left: 4px;
            color: var(--accent-strong);
        }
        th.sort-desc::after {
            content: "▼";
            font-size: 0.6rem;
            margin-left: 4px;
            color: var(--accent-strong);
        }
        tbody tr:nth-child(even) {
            background: rgba(15,23,42,0.96);
        }
        tbody tr:nth-child(odd) {
            background: rgba(15,23,42,0.92);
        }
        tbody tr:hover {
            background: rgba(15,23,42,1);
        }
        .table-scroll {
            max-height: 350px;
            overflow: auto;
        }
        .status-bar {
            font-size: 0.75rem;
            color: var(--muted);
            padding-top: 8px;
            display: flex;
            justify-content: space-between;
            gap: 10px;
        }
        .status-badge {
            color: var(--accent-strong);
        }
        .chart-container {
            position: relative;
            width: 100%;
            height: 320px;
        }
        .footer {
            max-width: 1200px;
            margin: 0 auto;
            padding: 10px 18px 16px;
            font-size: 0.74rem;
            color: var(--muted);
            display: flex;
            justify-content: space-between;
            gap: 12px;
        }
        .footer span {
            opacity: 0.8;
        }
        .toast {
            position: fixed;
            right: 20px;
            bottom: 20px;
            background: rgba(15,23,42,0.96);
            border-radius: 999px;
            padding: 8px 14px;
            font-size: 0.78rem;
            border: 1px solid rgba(56,189,248,0.7);
            color: #e5e7eb;
            opacity: 0;
            pointer-events: none;
            transform: translateY(10px);
            transition: opacity var(--transition-fast), transform var(--transition-fast);
            z-index: 50;
        }
        .toast.visible {
            opacity: 1;
            transform: translateY(0);
        }
        .toast.error {
            border-color: #f97373;
            color: #fecaca;
        }

        /* Modal Styles */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
        }
        .modal-overlay.open {
            opacity: 1;
            pointer-events: auto;
        }
        .modal {
            background: #0f172a;
            border: 1px solid var(--border-subtle);
            border-radius: 18px;
            padding: 24px;
            max-width: 400px;
            width: 90%;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            transform: scale(0.95);
            transition: transform 0.2s ease;
        }
        .modal-overlay.open .modal {
            transform: scale(1);
        }
        .modal-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 12px;
            color: var(--text);
        }
        .modal-body {
            font-size: 0.9rem;
            color: var(--muted);
            margin-bottom: 24px;
            line-height: 1.5;
        }
        .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
        }
        .btn-loading {
            position: relative;
            color: transparent !important;
            pointer-events: none;
        }
        .btn-loading::after {
            content: "";
            position: absolute;
            width: 16px;
            height: 16px;
            top: 50%;
            left: 50%;
            margin-top: -8px;
            margin-left: -8px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 0.6s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @media (max-width: 1023px) {
            .layout {
                grid-template-columns: 1fr;
            }
        }
        @media (max-width: 767px) {
            .nav-links {
                display: none;
            }
            .nav-actions {
                display: none;
            }
            .nav-toggle {
                display: block;
            }
            .nav-mobile-menu.open {
                display: flex;
            }
            .page {
                padding: 14px 12px 18px;
            }
            .card {
                padding: 14px 12px 12px;
            }
            .controls-row {
                flex-direction: column;
            }
            .table-scroll {
                max-height: 260px;
            }
        }
        @media (max-width: 480px) {
            .brand-subtitle {
                display: none;
            }
            .card-title {
                font-size: 0.9rem;
            }
            .card-subtitle {
                font-size: 0.78rem;
            }
            th,
            td {
                padding: 6px 8px;
            }
            .chart-container {
                height: 260px;
            }
        }
    </style>
</head>
<body>
    <div class="shell">
        <header class="navbar">
            <div class="nav-inner">
                <div class="brand">
                    <div class="brand-logo"></div>
                    <div class="brand-text">
                        <div class="brand-title">Excel Data Studio</div>
                        <div class="brand-subtitle">Interactive tables and analytics</div>
                    </div>
                </div>
                <div class="nav-actions">
                    <div class="pill">Local Secure Session</div>
                </div>
                <!-- Navbar simplified: remove unused links -->
            </div>
        </header>
        <main class="main">
            <div class="page">
                <div class="layout">
                    <section class="card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">Tabel Data</div>
                                <div class="card-subtitle">Sorting dan filtering interaktif</div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <button class="btn btn-danger" id="resetDataBtn" title="Hapus semua data">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                                    Reset Data
                                </button>
                                <div class="badge" id="rowCountBadge">0 baris</div>
                            </div>
                        </div>
                        <div class="controls-row">
                            <div class="control-group">
                                <div class="control-label">Pencarian global</div>
                                <input type="text" id="globalSearch" placeholder="Cari di semua kolom">
                            </div>
                            <div class="control-group">
                                <div class="control-label">Kolom prioritas</div>
                                <select id="primaryColumnSelect"></select>
                            </div>
                            <div class="control-group">
                                <div class="control-label">Batas baris ditampilkan</div>
                                <select id="rowLimit">
                                    <option value="50">50</option>
                                    <option value="100">100</option>
                                    <option value="250">250</option>
                                    <option value="0">Semua</option>
                                </select>
                            </div>
                        </div>
                        <div class="table-wrapper">
                            <div class="table-scroll">
                                <table id="dataTable">
                                    <thead></thead>
                                    <tbody></tbody>
                                </table>
                            </div>
                        </div>
                        <div class="status-bar">
                            <div id="statusText">Menunggu data...</div>
                            <div class="status-badge" id="sortStatusContainer">
                                <span id="sortStatus"></span>
                                <button class="clear-sort-btn" id="clearSortBtn" style="display: none;" title="Clear sorting">X</button>
                            </div>
                        </div>
                        <div class="btn-row" style="margin-top: 8px; justify-content: flex-end;">
                            <button class="btn btn-outline" id="exportExcelBtn">Export Data</button>
                        </div>
                    </section>
                    <section class="card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">Visualisasi Grafik</div>
                                <div class="card-subtitle">Pilih kolom dan tipe grafik</div>
                            </div>
                            <div class="badge">Interactive chart</div>
                        </div>
                        <div class="controls-row">
                            <div class="control-group">
                                <div class="control-label">Tipe grafik</div>
                                <select id="chartType">
                                    <option value="bar">Bar</option>
                                    <option value="line">Line</option>
                                    <option value="pie">Pie</option>
                                </select>
                            </div>
                            <div class="control-group">
                                <div class="control-label">Kolom kategori (X)</div>
                                <select id="xColumn"></select>
                            </div>
                            <div class="control-group">
                                <div class="control-label">Kolom nilai (Y)</div>
                                <select id="yColumn"></select>
                            </div>
                        </div>
                        <div class="chart-container" id="chartContainer">
                            <canvas id="chartCanvas"></canvas>
                        </div>
                        <div class="btn-row">
                            <button class="btn btn-primary" id="downloadPdfBtn">Unduh sebagai PDF</button>
                            <button class="btn btn-ghost" id="resetViewBtn">Reset tampilan</button>
                        </div>
                    </section>
                </div>
            </div>
        </main>
        <footer class="footer">
            <span>Excel Data Studio · Local analytics workspace</span>
            <span id="footerInfo"></span>
        </footer>
    </div>

    <!-- Confirmation Modal -->
    <div id="confirmModal" class="modal-overlay">
        <div class="modal">
            <div class="modal-title">Konfirmasi Reset Data</div>
            <div class="modal-body">Apakah anda yakin untuk mereset data ini?</div>
            <div class="modal-actions">
                <button class="btn btn-ghost" id="cancelResetBtn">Tidak</button>
                <button class="btn btn-danger" id="confirmResetBtn">Ya</button>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script>
        let originalData = [];
        let filteredData = [];
        let columns = [];
        let currentSortColumn = null;
        let currentSortDirection = "asc";
        let chartInstance = null;

        const navToggle = document.getElementById("navToggle");
        const navMobileMenu = document.getElementById("navMobileMenu");
        if (navToggle && navMobileMenu) {
            navToggle.addEventListener("click", function () {
                navMobileMenu.classList.toggle("open");
            });
        }

        function fetchData() {
            const statusText = document.getElementById("statusText");
            const resetBtn = document.getElementById("resetDataBtn");
            statusText.textContent = "Memuat data dari server...";
            fetch("/api/data")
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("HTTP status " + response.status);
                    }
                    return response.json();
                })
                .then(function (data) {
                    columns = data.columns || [];
                    originalData = data.rows || [];
                    filteredData = originalData.slice();
                    
                    // Update reset button state
                    if (resetBtn) {
                        resetBtn.disabled = originalData.length === 0;
                    }
                    
                    buildTable();
                    initControls();
                    updateFooter();
                })
                .catch(function (error) {
                    console.error("Gagal memuat data untuk dashboard:", error);
                    statusText.textContent = "Gagal memuat data dari server. Periksa log server Flask.";
                    const badge = document.getElementById("rowCountBadge");
                    badge.textContent = "0 baris (error)";
                    if (resetBtn) resetBtn.disabled = true;
                });
        }

        function buildTable() {
            const thead = document.querySelector("#dataTable thead");
            const tbody = document.querySelector("#dataTable tbody");
            thead.innerHTML = "";
            tbody.innerHTML = "";
            const headerRow = document.createElement("tr");
            columns.forEach(function (col) {
                const th = document.createElement("th");
                th.textContent = col;
                th.dataset.column = col;
                th.addEventListener("click", function () {
                    onHeaderClick(col, th);
                });
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            renderRows();
        }

        function renderRows() {
            const tbody = document.querySelector("#dataTable tbody");
            tbody.innerHTML = "";
            const limitSelect = document.getElementById("rowLimit");
            const limitValue = parseInt(limitSelect.value, 10);
            const rows = limitValue > 0 ? filteredData.slice(0, limitValue) : filteredData;
            rows.forEach(function (row) {
                const tr = document.createElement("tr");
                columns.forEach(function (col) {
                    const td = document.createElement("td");
                    const value = row[col];
                    td.textContent = value === null || value === undefined ? "" : value;
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
            const rowCountBadge = document.getElementById("rowCountBadge");
            rowCountBadge.textContent = filteredData.length + " baris";
            const statusText = document.getElementById("statusText");
            statusText.textContent = "Menampilkan " + rows.length + " dari " + filteredData.length + " baris.";
        }

        function onHeaderClick(column, thElement) {
            if (currentSortColumn === column) {
                currentSortDirection = currentSortDirection === "asc" ? "desc" : "asc";
            } else {
                currentSortColumn = column;
                currentSortDirection = "asc";
            }
            filteredData.sort(function (a, b) {
                const va = a[column];
                const vb = b[column];
                if (va === vb) return 0;
                if (va === null || va === undefined) return 1;
                if (vb === null || vb === undefined) return -1;
                if (typeof va === "number" && typeof vb === "number") {
                    return currentSortDirection === "asc" ? va - vb : vb - va;
                }
                const sa = String(va).toLowerCase();
                const sb = String(vb).toLowerCase();
                if (sa < sb) return currentSortDirection === "asc" ? -1 : 1;
                if (sa > sb) return currentSortDirection === "asc" ? 1 : -1;
                return 0;
            });
            document.querySelectorAll("#dataTable th").forEach(function (th) {
                th.classList.remove("sort-asc");
                th.classList.remove("sort-desc");
            });
            thElement.classList.add(currentSortDirection === "asc" ? "sort-asc" : "sort-desc");
            const sortStatus = document.getElementById("sortStatus");
            const clearSortBtn = document.getElementById("clearSortBtn");
            sortStatus.textContent = "Sort: " + column + " (" + currentSortDirection + ")";
            if (clearSortBtn) clearSortBtn.style.display = "inline-flex";
            renderRows();
            renderChart();
        }

        function clearSort() {
            currentSortColumn = null;
            currentSortDirection = "asc";
            document.querySelectorAll("#dataTable th").forEach(function (th) {
                th.classList.remove("sort-asc");
                th.classList.remove("sort-desc");
            });
            const sortStatus = document.getElementById("sortStatus");
            const clearSortBtn = document.getElementById("clearSortBtn");
            if (sortStatus) sortStatus.textContent = "";
            if (clearSortBtn) clearSortBtn.style.display = "none";
            
            // Re-apply filter to restore original order
            applyGlobalFilter();
        }

        function openModal() {
            document.getElementById("confirmModal").classList.add("open");
        }

        function closeModal() {
            document.getElementById("confirmModal").classList.remove("open");
        }

        async function resetData() {
            const confirmBtn = document.getElementById("confirmResetBtn");
            const cancelBtn = document.getElementById("cancelResetBtn");
            const resetBtn = document.getElementById("resetDataBtn");
            
            // Start loading state
            confirmBtn.classList.add("btn-loading");
            cancelBtn.disabled = true;
            
            try {
                const response = await fetch("/api/data/reset", { method: "POST" });
                if (!response.ok) throw new Error("Gagal mereset data");
                
                closeModal();
                showToast("Data berhasil direset", false);
                fetchData(); // Refresh UI
            } catch (error) {
                console.error("Reset error:", error);
                showToast("Gagal mereset data: " + error.message, true);
            } finally {
                // End loading state
                confirmBtn.classList.remove("btn-loading");
                cancelBtn.disabled = false;
            }
        }

        function initControls() {
            const globalSearch = document.getElementById("globalSearch");
            globalSearch.addEventListener("input", function () {
                applyGlobalFilter();
            });
            document.getElementById("rowLimit").addEventListener("change", function () {
                renderRows();
            });
            const primarySelect = document.getElementById("primaryColumnSelect");
            primarySelect.innerHTML = "";
            columns.forEach(function (col, idx) {
                const option = document.createElement("option");
                option.value = col;
                option.textContent = col;
                if (idx === 0) option.selected = true;
                primarySelect.appendChild(option);
            });
            primarySelect.addEventListener("change", function () {
                focusPrimaryColumn(primarySelect.value);
            });
            focusPrimaryColumn(primarySelect.value);
            const xSelect = document.getElementById("xColumn");
            const ySelect = document.getElementById("yColumn");
            xSelect.innerHTML = "";
            ySelect.innerHTML = "";
            columns.forEach(function (col, idx) {
                const xOpt = document.createElement("option");
                xOpt.value = col;
                xOpt.textContent = col;
                if (idx === 0) xOpt.selected = true;
                xSelect.appendChild(xOpt);
                const yOpt = document.createElement("option");
                yOpt.value = col;
                yOpt.textContent = col;
                ySelect.appendChild(yOpt);
            });
            if (columns.length > 1) {
                ySelect.selectedIndex = 1;
            }
            document.getElementById("chartType").addEventListener("change", renderChart);
            xSelect.addEventListener("change", renderChart);
            ySelect.addEventListener("change", renderChart);
            document.getElementById("downloadPdfBtn").addEventListener("click", downloadPdf);
            document.getElementById("resetViewBtn").addEventListener("click", resetView);
            const resetDataBtn = document.getElementById("resetDataBtn");
            if (resetDataBtn) {
                resetDataBtn.addEventListener("click", openModal);
            }
            const confirmResetBtn = document.getElementById("confirmResetBtn");
            if (confirmResetBtn) {
                confirmResetBtn.addEventListener("click", resetData);
            }
            const cancelResetBtn = document.getElementById("cancelResetBtn");
            if (cancelResetBtn) {
                cancelResetBtn.addEventListener("click", closeModal);
            }
            const clearSortBtn = document.getElementById("clearSortBtn");
            if (clearSortBtn) {
                clearSortBtn.addEventListener("click", clearSort);
            }
            const exportBtn = document.getElementById("exportExcelBtn");
            if (exportBtn) {
                exportBtn.addEventListener("click", exportExcel);
            }
            renderChart();
        }

        function applyGlobalFilter() {
            const term = document.getElementById("globalSearch").value.toLowerCase();
            if (!term) {
                filteredData = originalData.slice();
            } else {
                filteredData = originalData.filter(function (row) {
                    return columns.some(function (col) {
                        const value = row[col];
                        if (value === null || value === undefined) return false;
                        return String(value).toLowerCase().includes(term);
                    });
                });
            }
            
            // Re-apply sort if active, otherwise clear sort indicators
            if (currentSortColumn) {
                const th = document.querySelector(`th[data-column="${currentSortColumn}"]`);
                if (th) {
                    // Temporarily reset sort column to force re-sort in same direction
                    const savedCol = currentSortColumn;
                    const savedDir = currentSortDirection;
                    currentSortColumn = null; 
                    currentSortDirection = savedDir === "asc" ? "desc" : "asc"; // toggle logic in onHeaderClick
                    onHeaderClick(savedCol, th);
                }
            } else {
                document.getElementById("sortStatus").textContent = "";
                const clearSortBtn = document.getElementById("clearSortBtn");
                if (clearSortBtn) clearSortBtn.style.display = "none";
            }
            renderRows();
            renderChart();
        }

        function focusPrimaryColumn(column) {
            const index = columns.indexOf(column);
            if (index === -1) return;
            const tableScroll = document.querySelector(".table-scroll");
            const headerCell = document.querySelectorAll("#dataTable th")[index];
            if (headerCell) {
                const rect = headerCell.getBoundingClientRect();
                const scrollLeft = tableScroll.scrollLeft + rect.left - tableScroll.getBoundingClientRect().left - 40;
                tableScroll.scrollTo({ left: scrollLeft, behavior: "smooth" });
            }
        }

        function renderChart() {
            if (!columns.length || !filteredData.length) return;
            const type = document.getElementById("chartType").value;
            const xCol = document.getElementById("xColumn").value;
            const yCol = document.getElementById("yColumn").value;
            const grouped = {};
            filteredData.forEach(function (row) {
                const key = row[xCol];
                const rawVal = row[yCol];
                const num = typeof rawVal === "number" ? rawVal : parseFloat(rawVal);
                const value = isNaN(num) ? 0 : num;
                if (!grouped[key]) grouped[key] = 0;
                grouped[key] += value;
            });
            const labels = Object.keys(grouped);
            const dataValues = labels.map(function (k) { return grouped[k]; });
            const ctx = document.getElementById("chartCanvas").getContext("2d");
            if (chartInstance) {
                chartInstance.destroy();
            }
            const palette = ["#38bdf8", "#6366f1", "#22c55e", "#f97316", "#ec4899", "#a855f7", "#eab308", "#0ea5e9"];
            const backgroundColors = labels.map(function (_, idx) {
                return palette[idx % palette.length];
            });
            const datasetConfig = {
                label: yCol + " per " + xCol,
                data: dataValues,
                backgroundColor: type === "line" ? "#38bdf8" : backgroundColors,
                borderColor: "#38bdf8",
                borderWidth: 2,
                tension: 0.35,
                fill: type === "line"
            };
            const config = {
                type: type,
                data: {
                    labels: labels,
                    datasets: [datasetConfig]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: type !== "pie",
                            labels: {
                                color: "#e5e7eb",
                                font: { size: 11 }
                            }
                        },
                        tooltip: {
                            backgroundColor: "rgba(15,23,42,0.96)",
                            borderColor: "rgba(55,65,81,0.9)",
                            borderWidth: 1,
                            titleColor: "#e5e7eb",
                            bodyColor: "#e5e7eb",
                            padding: 8,
                            displayColors: false
                        }
                    },
                    scales: type === "pie" ? {} : {
                        x: {
                            ticks: { color: "#9ca3af", maxRotation: 45, minRotation: 0 },
                            grid: { color: "rgba(31,41,55,0.6)" }
                        },
                        y: {
                            ticks: { color: "#9ca3af" },
                            grid: { color: "rgba(31,41,55,0.6)" }
                        }
                    }
                }
            };
            chartInstance = new Chart(ctx, config);
        }

        async function downloadPdf() {
            const container = document.getElementById("chartContainer");
            const { jsPDF } = window.jspdf;
            const pdf = new jsPDF({ orientation: "landscape", unit: "px", format: "a4" });
            const canvas = await html2canvas(container, { backgroundColor: "#020617", scale: 2 });
            const imgData = canvas.toDataURL("image/png");
            const pageWidth = pdf.internal.pageSize.getWidth();
            const pageHeight = pdf.internal.pageSize.getHeight();
            const ratio = Math.min(pageWidth / canvas.width, pageHeight / canvas.height);
            const imgWidth = canvas.width * ratio;
            const imgHeight = canvas.height * ratio;
            const x = (pageWidth - imgWidth) / 2;
            const y = (pageHeight - imgHeight) / 2;
            pdf.setFillColor(2, 6, 23);
            pdf.rect(0, 0, pageWidth, pageHeight, "F");
            pdf.addImage(imgData, "PNG", x, y, imgWidth, imgHeight);
            pdf.save("data-chart.pdf");
        }

        function showToast(message, isError) {
            let toast = document.getElementById("toast");
            if (!toast) {
                toast = document.createElement("div");
                toast.id = "toast";
                toast.className = "toast";
                document.body.appendChild(toast);
            }
            toast.textContent = message;
            if (isError) {
                toast.classList.add("error");
            } else {
                toast.classList.remove("error");
            }
            toast.classList.add("visible");
            setTimeout(function () {
                toast.classList.remove("visible");
            }, 4000);
        }

        async function exportExcel() {
            const btn = document.getElementById("exportExcelBtn");
            if (!btn) return;
            if (!columns.length || !originalData.length) {
                showToast("Tidak ada data untuk diexport.", true);
                return;
            }
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = "Mengekspor...";
            try {
                const params = new URLSearchParams();
                const term = document.getElementById("globalSearch").value;
                if (term) params.append("q", term);
                const response = await fetch("/export-to-excel?" + params.toString(), { method: "GET" });
                if (!response.ok) {
                    throw new Error("HTTP " + response.status);
                }
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "dashboard_export.xlsx";
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                showToast("Export berhasil. File berhasil diunduh.", false);
            } catch (error) {
                console.error("Export error:", error);
                showToast("Export gagal. Periksa log server.", true);
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        }

        function resetView() {
            const globalSearch = document.getElementById("globalSearch");
            if (globalSearch) globalSearch.value = "";

            // Restore data and sorting defaults
            filteredData = originalData.slice();
            currentSortColumn = null;
            currentSortDirection = "asc";

            // Reset selects to defaults
            const primarySelect = document.getElementById("primaryColumnSelect");
            const rowLimit = document.getElementById("rowLimit");
            const chartType = document.getElementById("chartType");
            const xSelect = document.getElementById("xColumn");
            const ySelect = document.getElementById("yColumn");

            if (primarySelect && columns.length) {
                primarySelect.selectedIndex = 0;
                focusPrimaryColumn(primarySelect.value);
            }
            if (rowLimit) rowLimit.value = "50";
            if (chartType) chartType.value = "bar";
            if (xSelect && columns.length) xSelect.selectedIndex = 0;
            if (ySelect && columns.length > 1) ySelect.selectedIndex = 1;

            // Clear sort indicators
            document.querySelectorAll("#dataTable th").forEach(function (th) {
                th.classList.remove("sort-asc");
                th.classList.remove("sort-desc");
            });

            // Reset table scroll position
            const tableScroll = document.querySelector(".table-scroll");
            if (tableScroll) tableScroll.scrollTo({ top: 0, left: 0, behavior: "smooth" });

            // Update status
            document.getElementById("sortStatus").textContent = "";
            renderRows();
            renderChart();
        }

        function shareChart(network) {
            const url = encodeURIComponent(window.location.href);
            const text = encodeURIComponent("Lihat visualisasi data saya di Excel Data Studio");
            let shareUrl = "";
            if (network === "twitter") {
                shareUrl = "https://twitter.com/intent/tweet?url=" + url + "&text=" + text;
            } else if (network === "linkedin") {
                shareUrl = "https://www.linkedin.com/sharing/share-offsite/?url=" + url;
            } else if (network === "facebook") {
                shareUrl = "https://www.facebook.com/sharer/sharer.php?u=" + url;
            }
            if (shareUrl) {
                window.open(shareUrl, "_blank", "noopener,noreferrer");
            }
        }

        function updateFooter() {
            const footerInfo = document.getElementById("footerInfo");
            const now = new Date();
            footerInfo.textContent = "Data dimuat: " + now.toLocaleString();
        }

        document.addEventListener("DOMContentLoaded", fetchData);
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        expected_user = os.environ.get("DASHBOARD_USER", "admin")
        expected_password = os.environ.get("DASHBOARD_PASSWORD", "admin123")
        if username == expected_user and password == expected_password:
            session["logged_in"] = True
            session["username"] = username
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        error = "Username atau password salah."
    return render_template_string(LOGIN_TEMPLATE, error=error)


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE)


@app.route("/api/data")
@login_required
def api_data():
    df = load_dataframe()
    return jsonify(
        {
            "columns": list(df.columns),
            # Gunakan konversi manual agar tidak ada NaN/Infinity di JSON
            "rows": dataframe_to_json_rows(df),
        }
    )


@app.route("/api/export-excel")
@login_required
def export_excel_api():
    df = load_dataframe()
    if df.empty:
        return jsonify({"error": "No data available to export"}), 400
    
    df_export = df
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name='Merged Data', index=False)
        metadata = {
            'Export Information': [
                f'Export Date: {pd.Timestamp.now()}',
                f'Total Rows Exported: {len(df_export)}',
                f'Source: SQLite Database (records_current) or Merged Snapshot'
            ]
        }
        pd.DataFrame(metadata).to_excel(writer, sheet_name='Metadata', index=False)
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'merged_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )


@app.route("/export")
@login_required
def export_excel():
    df = load_dataframe()
    if df.empty:
        return jsonify({"error": "No data to export"}), 404
    
    df_export = df
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Data")
    output.seek(0)
    filename = "dashboard_export_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/export-to-excel", methods=["GET"])
@login_required
def export_to_excel():
    if not can_export():
        return jsonify({"error": "Not allowed to export"}), 403
    df = load_dataframe()
    if df.empty:
        return jsonify({"error": "No data to export"}), 404
    q = request.args.get("q", "").strip()
    if q:
        df = df[df.apply(lambda row: q.lower() in " ".join(row.astype(str)).lower(), axis=1)]
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    if "ExportTimestamp" in df.columns and (date_from or date_to):
        df_ts = pd.to_datetime(df["ExportTimestamp"], errors="coerce")
        if date_from:
            df = df[df_ts >= pd.to_datetime(date_from, errors="coerce")]
        if date_to:
            df = df[df_ts <= pd.to_datetime(date_to, errors="coerce")]
    page_size = int(request.args.get("page_size", "0") or "0")
    page = int(request.args.get("page", "1") or "1")
    if page_size > 0:
        start = (page - 1) * page_size
        end = start + page_size
        df = df.iloc[start:end]
    
    df_export = df
    
    user_id = session.get("username") or "web"
    # merge_to_dashboard_excel_web still needs 'df' with NOP for synchronization logic
    dashboard_path, sync_results = merge_to_dashboard_excel_web(df, user_id)
    
    # Generate direct download from df_export (without metadata)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Data")
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name="dashboard_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/api/data/reset", methods=["POST"])
@login_required
def reset_data():
    conn = None
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "data_pipeline.sqlite")
        export_path = os.path.join(base_dir, "export", "dashboard_export.xlsx")
        merged_path = os.path.join(base_dir, "merged_current.xlsx")
        
        print(f"[web_app] Starting robust reset process", flush=True)
        
        # 1. Reset SQLite within a transaction
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.execute("BEGIN TRANSACTION")
            try:
                # Get table list to ensure we clean everything
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall() if row[0] != "sqlite_sequence"]
                
                for table in tables:
                    print(f"[web_app] Clearing table: {table}", flush=True)
                    conn.execute(f"DELETE FROM {table}")
                
                conn.commit()
                print("[web_app] SQLite data cleared successfully", flush=True)
            except Exception as db_e:
                conn.rollback()
                raise db_e
            finally:
                conn.close()
            
        # 2. Reset Excel Files (Move to backup instead of delete for safety, or just delete as requested)
        for path in [export_path, merged_path]:
            if os.path.exists(path):
                try:
                    # Optional: backup before delete
                    backup_path = path + ".bak"
                    shutil.copy2(path, backup_path)
                    os.remove(path)
                    print(f"[web_app] Removed file: {path}", flush=True)
                except Exception as file_e:
                    print(f"[web_app] Warning: Could not remove {path}: {file_e}", flush=True)
            
        return jsonify({"message": "Data berhasil direset secara menyeluruh"}), 200
    except Exception as e:
        print(f"[web_app] Reset error: {e}", flush=True)
        return jsonify({"error": f"Gagal mereset data: {str(e)}"}), 500


def main():
    port = int(os.environ.get("DASHBOARD_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
