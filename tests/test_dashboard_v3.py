import unittest
import os
import sqlite3
import pandas as pd
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from web_app import app, load_dataframe

class TestDashboardFunctionality(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.config['TESTING'] = True
        app.secret_key = 'test_key'
        
        # Setup dummy data in SQLite
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, "data_pipeline.sqlite")
        
        # Check if table has row_hash, if so we need to provide it
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("INSERT OR REPLACE INTO records_current (NOP, PROGRAM, row_hash, ingest_timestamp, source_file) VALUES ('TEST001', 'PROG1', 'hash1', 'ts1', 'file1')")
        except sqlite3.OperationalError:
            # Table might not have all these columns in a clean state, create minimal
            conn.execute("CREATE TABLE IF NOT EXISTS records_current (NOP TEXT PRIMARY KEY, PROGRAM TEXT, row_hash TEXT, ingest_timestamp TEXT, source_file TEXT)")
            conn.execute("INSERT OR REPLACE INTO records_current (NOP, PROGRAM, row_hash, ingest_timestamp, source_file) VALUES ('TEST001', 'PROG1', 'hash1', 'ts1', 'file1')")
        conn.commit()
        conn.close()

    def test_reset_data_api(self):
        with self.app.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'admin'
            
        response = self.app.post('/api/data/reset')
        self.assertEqual(response.status_code, 200)
        
        # Verify SQLite is empty
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT COUNT(*) FROM records_current")
        count = cur.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)

    def test_load_dataframe_column_renaming(self):
        # Create a temp excel with old column names and 'REVENUE (ACTUAL)'
        temp_excel = os.path.join(os.getcwd(), "temp_test_load.xlsx")
        df = pd.DataFrame({
            "NOP": ["1"], 
            "REVENUE INCREMENTAL 1": ["val1"],
            "REVENUE (ACTUAL)": ["old_actual"]
        })
        df.to_excel(temp_excel, index=False)
        
        # Mock get_data_file to return this temp file
        import web_app
        original_get_file = web_app.get_data_file
        web_app.get_data_file = lambda: temp_excel
        
        # Clear DB and Merged Snapshot first to force excel load from our temp file
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM records_current")
        conn.commit()
        conn.close()
        
        merged_path = os.path.join(os.path.dirname(self.db_path), "merged_current.xlsx")
        merged_bak = merged_path + ".testbak"
        if os.path.exists(merged_path):
            os.rename(merged_path, merged_bak)
        
        try:
            loaded_df = load_dataframe()
            
            # Check display issue fix: REVENUE INCREMENTAL 1 -> INCREMENTAL 1
            self.assertIn("INCREMENTAL 1", loaded_df.columns)
            self.assertNotIn("REVENUE INCREMENTAL 1", loaded_df.columns)
            self.assertEqual(str(loaded_df["INCREMENTAL 1"].iloc[0]), "val1")
            
            # Check removal: REVENUE (ACTUAL) should be gone
            self.assertNotIn("REVENUE (ACTUAL)", loaded_df.columns)
        finally:
            # Cleanup
            if os.path.exists(temp_excel):
                os.remove(temp_excel)
            if os.path.exists(merged_bak):
                if os.path.exists(merged_path): os.remove(merged_path)
                os.rename(merged_bak, merged_path)
            web_app.get_data_file = original_get_file

if __name__ == '__main__':
    unittest.main()
