import os
import unittest
import pandas as pd
import sqlite3
import io
from web_app import app, load_dataframe


class TestUIColumnExclusion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.db_path = os.path.join(cls.base_dir, "data_pipeline.sqlite")
        cls.exclude_cols = ["row_hash", "ingest_timestamp", "source_file", "ExportSource", "ExportTimestamp", "ExportUser"]
        
        # Ensure we have some dummy data in DB for testing
        if os.path.exists(cls.db_path):
            conn = sqlite3.connect(cls.db_path)
            # Check if records_current exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records_current'")
            if cursor.fetchone():
                # Add a dummy record if empty
                df_check = pd.read_sql_query("SELECT * FROM records_current LIMIT 1", conn)
                if df_check.empty:
                    # Minimal columns for sync engine
                    conn.execute("""
                        INSERT INTO records_current (NOP, PROGRAM, row_hash, ingest_timestamp, source_file)
                        VALUES ('TEST-999', 'TEST-PROG', 'hash123', '2023-01-01', 'test.xlsx')
                    """)
                    conn.commit()
            conn.close()

    def setUp(self):
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["username"] = "admin"

    def test_load_dataframe_excludes_internal_cols(self):
        """Verify load_dataframe helper itself excludes the columns."""
        df = load_dataframe()
        if not df.empty:
            for col in self.exclude_cols:
                self.assertNotIn(col, df.columns, f"Column {col} should be excluded from load_dataframe")

    def test_api_data_excludes_internal_cols(self):
        """Verify /api/data response excludes the columns."""
        resp = self.client.get("/api/data")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        
        # Check columns list
        for col in self.exclude_cols:
            self.assertNotIn(col, data["columns"], f"Column {col} should be excluded from api_data columns list")
            
        # Check rows data
        if data["rows"]:
            for col in self.exclude_cols:
                self.assertNotIn(col, data["rows"][0], f"Column {col} should be excluded from api_data row data")

    def test_excel_export_excludes_internal_cols(self):
        """Verify Excel export files exclude the columns."""
        endpoints = ["/export", "/api/export-excel", "/export-to-excel"]
        
        for ep in endpoints:
            resp = self.client.get(ep)
            if resp.status_code == 404: # No data, skip
                continue
                
            self.assertEqual(resp.status_code, 200, f"Endpoint {ep} failed")
            
            # Read excel from response data
            df_exported = pd.read_excel(io.BytesIO(resp.data))
            
            for col in self.exclude_cols:
                self.assertNotIn(col, df_exported.columns, f"Column {col} should be excluded from export at {ep}")


if __name__ == "__main__":
    unittest.main()
