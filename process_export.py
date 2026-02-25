import os
import sys
import sqlite3
import logging
import hashlib
from datetime import datetime
from typing import List, Tuple, Dict

import pandas as pd


DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pipeline.sqlite")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pipeline.log")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def normalize_column_name(name: str) -> str:
    return " ".join(str(name).strip().upper().split())


def read_export_file(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    else:
        df = pd.read_excel(path, dtype=str, engine="openpyxl")
    df.columns = [normalize_column_name(c) for c in df.columns]
    df = df.applymap(lambda x: None if pd.isna(x) or (isinstance(x, str) and x.strip() == "") else x)
    df = handle_duplicate_columns(df)
    return df


def handle_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    seen: Dict[str, int] = {}
    new_cols: List[str] = []
    for c in df.columns:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
            logging.warning(f"Duplicate column detected and renamed: {c} -> {c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols
    return df


def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    required = [
        "NOP",
        "PROGRAM",
        "KATEGORI",
        "JUSTIFIKASI",
        "PROPOSAL",
        "BUDGET",
        "REVENUE",
        "COST",
        "PROFIT",
        "INCREMENTAL 1",
        "INCREMENTAL 2",
        "INCREMENTAL 3",
        "STATUS",
        "PILOT",
        "DRIVEN PROGRAM",
        "ASSIGN BY",
        "APPROVED BY",
    ]
    
    # PERMANENT REMOVAL: Check and remove "REVENUE (ACTUAL)" if it exists during ingestion
    if "REVENUE (ACTUAL)" in df.columns:
        logging.info("Schema validation: Permanently removing 'REVENUE (ACTUAL)' from input")
        df.drop(columns=["REVENUE (ACTUAL)"], inplace=True)

    missing = [c for c in required if c not in df.columns]
    return (len(missing) == 0, missing)


def compute_row_hash(row: pd.Series) -> str:
    payload = []
    for k, v in row.items():
        payload.append(f"{k}={'' if v is None else str(v)}")
    raw = "|".join(sorted(payload))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    return conn


def ensure_schema(conn: sqlite3.Connection, columns: List[str]):
    col_defs = ", ".join([f'"{c}" TEXT' for c in columns])
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS records_current (
            {col_defs},
            row_hash TEXT NOT NULL,
            ingest_timestamp TEXT NOT NULL,
            source_file TEXT NOT NULL,
            PRIMARY KEY ("NOP")
        )
        """
    )
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS records_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {col_defs},
            row_hash TEXT NOT NULL,
            changed_timestamp TEXT NOT NULL,
            source_file TEXT NOT NULL,
            change_type TEXT NOT NULL
        )
        """
    )
    conn.commit()
    migrate_schema(conn, "records_current", columns + ["row_hash", "ingest_timestamp", "source_file"])
    migrate_schema(conn, "records_history", columns + ["row_hash", "changed_timestamp", "source_file", "change_type"])


def get_table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.execute(f'PRAGMA table_info("{table}")')
    return [row[1] for row in cur.fetchall()]


def migrate_schema(conn: sqlite3.Connection, table: str, desired_columns: List[str]):
    existing = set(get_table_columns(conn, table))
    added = []
    for col in desired_columns:
        if col not in existing:
            conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{col}" TEXT')
            added.append(col)
    if added:
        logging.info(f"Schema migration on {table}: added columns {added}")
        conn.commit()


def load_current(conn: sqlite3.Connection) -> pd.DataFrame:
    try:
        df = pd.read_sql_query("SELECT * FROM records_current", conn)
        df = df.applymap(lambda x: None if pd.isna(x) else x)
        return df
    except Exception:
        return pd.DataFrame()


def detect_and_sync_changes(conn: sqlite3.Connection, df_new: pd.DataFrame, source_file: str) -> Dict:
    """
    Detailed field-level diff detection and synchronization engine.
    Returns a summary of changes detected and synchronized.
    """
    df_current = load_current(conn)
    sync_summary = {
        "new_records": 0,
        "updated_records": 0,
        "unchanged_records": 0,
        "modifications": [],  # List of {nop, field, old, new}
        "errors": []
    }
    
    ts = datetime.utcnow().isoformat()
    df_new = df_new.copy()
    df_new["row_hash"] = df_new.apply(compute_row_hash, axis=1)
    
    cursor = conn.cursor()
    current_cols = set(get_table_columns(conn, "records_current"))
    
    for _, row in df_new.iterrows():
        nop = row.get("NOP")
        if nop is None:
            continue
            
        existing = None
        if not df_current.empty:
            match = df_current[df_current["NOP"] == nop]
            if not match.empty:
                existing = match.iloc[0]
                
        if existing is None:
            # Insert new record (already handled by upsert_records logic, but we integrate it here)
            cols_to_insert = [c for c in df_new.columns if c in current_cols and c != "row_hash"]
            data_cols = ", ".join([f'"{c}"' for c in cols_to_insert] + ["row_hash", "ingest_timestamp", "source_file"])
            placeholders = ", ".join(["?"] * (len(cols_to_insert) + 3))
            values = [row.get(c) for c in cols_to_insert] + [row["row_hash"], ts, source_file]
            
            try:
                cursor.execute(f'INSERT INTO records_current ({data_cols}) VALUES ({placeholders})', values)
                sync_summary["new_records"] += 1
            except Exception as e:
                sync_summary["errors"].append(f"Error inserting {nop}: {e}")
        else:
            # Detect changes
            if existing["row_hash"] == row["row_hash"]:
                sync_summary["unchanged_records"] += 1
                continue
                
            # Field-level comparison
            field_changes = []
            cols_to_compare = [c for c in df_new.columns if c in current_cols and c not in ["row_hash", "ingest_timestamp", "source_file", "NOP"]]
            
            for col in cols_to_compare:
                old_val = existing.get(col)
                new_val = row.get(col)
                
                # Normalize for comparison
                old_norm = "" if pd.isna(old_val) else str(old_val).strip()
                new_norm = "" if pd.isna(new_val) else str(new_val).strip()
                
                if old_norm != new_norm:
                    field_changes.append({
                        "field": col,
                        "old": old_norm,
                        "new": new_norm
                    })
                    sync_summary["modifications"].append({
                        "nop": nop,
                        "field": col,
                        "old": old_norm,
                        "new": new_norm
                    })
            
            if field_changes:
                # Log modification
                for change in field_changes:
                    logging.info(f"SYNC: [{nop}] Field '{change['field']}' changed: '{change['old']}' -> '{change['new']}'")
                
                # Update record
                update_cols = [c for c in df_new.columns if c in current_cols and c != "NOP"]
                set_clause = ", ".join([f'"{c}"=?' for c in update_cols])
                values = [row.get(c) for c in update_cols] + [nop]
                
                try:
                    # Keep history for rollback
                    # Include NOP in history record
                    hist_data_cols = [c for c in df_new.columns if c in current_cols]
                    hist_cols_str = ", ".join([f'"{c}"' for c in hist_data_cols] + ["change_type", "changed_timestamp", "source_file"])
                    hist_placeholders = ", ".join(["?"] * (len(hist_data_cols) + 3))
                    
                    # Store OLD values in history before update
                    old_hist_values = [existing.get(c) for c in hist_data_cols] + ["sync_update_old", ts, source_file]
                    cursor.execute(f'INSERT INTO records_history ({hist_cols_str}) VALUES ({hist_placeholders})', old_hist_values)
                    
                    # Perform update (already has NOP in WHERE clause)
                    update_cols = [c for c in df_new.columns if c in current_cols and c != "NOP"]
                    set_clause = ", ".join([f'"{c}"=?' for c in update_cols])
                    update_values = [row.get(c) for c in update_cols] + [nop]
                    cursor.execute(f'UPDATE records_current SET {set_clause} WHERE "NOP"=?', update_values)
                    sync_summary["updated_records"] += 1
                except Exception as e:
                    sync_summary["errors"].append(f"Error updating {nop}: {e}")
            else:
                sync_summary["unchanged_records"] += 1
                
    conn.commit()
    return sync_summary

def rollback_record(conn: sqlite3.Connection, nop: str) -> bool:
    """
    Rolls back a record to its previous state using records_history.
    """
    cursor = conn.cursor()
    # Find last 'sync_update_old' for this NOP
    cursor.execute('SELECT * FROM records_history WHERE "NOP"=? AND change_type="sync_update_old" ORDER BY id DESC LIMIT 1', (nop,))
    row = cursor.fetchone()
    
    if not row:
        logging.warning(f"No rollback data found for NOP: {nop}")
        return False
        
    # Get column names for records_history
    cursor.execute('PRAGMA table_info(records_history)')
    hist_cols = [c[1] for c in cursor.fetchall()]
    
    # Map row values to columns
    record_data = dict(zip(hist_cols, row))
    
    # Columns to restore in records_current
    current_cols = set(get_table_columns(conn, "records_current"))
    restore_cols = [c for c in record_data.keys() if c in current_cols and c not in ["id", "change_type", "changed_timestamp"]]
    
    set_clause = ", ".join([f'"{c}"=?' for c in restore_cols])
    values = [record_data[c] for c in restore_cols] + [nop]
    
    try:
        cursor.execute(f'UPDATE records_current SET {set_clause} WHERE "NOP"=?', values)
        # Log rollback
        logging.info(f"ROLLBACK: [{nop}] Restored to previous state.")
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Rollback failed for {nop}: {e}")
        conn.rollback()
        return False

def upsert_records(conn: sqlite3.Connection, df_new: pd.DataFrame, source_file: str) -> Tuple[int, int, int]:
    # Reuse detect_and_sync_changes for consistency
    summary = detect_and_sync_changes(conn, df_new, source_file)
    return summary["new_records"], summary["updated_records"], summary["unchanged_records"]



def export_merged_snapshot(conn: sqlite3.Connection, out_path: str):
    df = pd.read_sql_query("SELECT * FROM records_current", conn)
    
    # Rename column "REVENUE INCREMENTAL 1" to "INCREMENTAL 1" if exists
    if "REVENUE INCREMENTAL 1" in df.columns:
        df = df.rename(columns={"REVENUE INCREMENTAL 1": "INCREMENTAL 1"})
    
    # Reorder columns
    desired_order = [
        "NOP",
        "PROGRAM",
        "KATEGORI",
        "JUSTIFIKASI",
        "PROPOSAL",
        "BUDGET",
        "REVENUE",
        "COST",
        "PROFIT",
        "INCREMENTAL 1",
        "INCREMENTAL 2",
        "INCREMENTAL 3",
        "STATUS",
        "PILOT",
        "DRIVEN PROGRAM",
        "ASSIGN BY",
        "APPROVED BY",
    ]
    
    # Filter only columns that exist in df
    cols_to_use = [c for c in desired_order if c in df.columns]
    
    # Exclude internal/metadata columns from the Excel snapshot
    exclude_cols = ["row_hash", "ingest_timestamp", "source_file", "ExportSource", "ExportTimestamp", "ExportUser"]
    
    # Only keep visible columns
    df = df[cols_to_use]
    
    df.to_excel(out_path, index=False, engine="openpyxl")
    logging.info(f"Merged snapshot exported: {out_path} (rows={len(df)})")


def process(path: str):
    setup_logging()
    logging.info(f"Starting ingestion for file: {path}")
    df = read_export_file(path)
    ok, missing = validate_schema(df)
    if not ok:
        logging.error(f"Missing required columns: {missing}")
        raise ValueError(f"Missing required columns: {missing}")
    conn = connect_db()
    ensure_schema(conn, list(df.columns))
    new_count, updated_count, unchanged_count = upsert_records(conn, df, source_file=os.path.abspath(path))
    logging.info(f"Ingestion summary: new={new_count}, updated={updated_count}, unchanged={unchanged_count}")
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merged_current.xlsx")
    export_merged_snapshot(conn, out_file)
    logging.info("Processing finished successfully")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_export.py <path_to_export_file.xlsx|.csv>")
        sys.exit(1)
    process(sys.argv[1])
