import unittest
import os
import sqlite3
import pandas as pd
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

import process_export

class TestSyncEngine(unittest.TestCase):
    def setUp(self):
        # Use a test database
        self.db_path = "test_sync.sqlite"
        process_export.DB_FILE = self.db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
    def test_sync_and_rollback(self):
        conn = process_export.connect_db()
        try:
            cols = ["NOP", "PROGRAM", "KATEGORI"]
            process_export.ensure_schema(conn, cols)
            
            # 1. Initial Insert
            df1 = pd.DataFrame([
                {"NOP": "nop-001", "PROGRAM": "Prog A", "KATEGORI": "Cat 1"}
            ])
            summary1 = process_export.detect_and_sync_changes(conn, df1, "file1.xlsx")
            self.assertEqual(summary1["new_records"], 1)
            
            # Verify initial state
            df_curr = process_export.load_current(conn)
            self.assertEqual(df_curr.iloc[0]["KATEGORI"], "Cat 1")
            
            # 2. Update with change
            df2 = pd.DataFrame([
                {"NOP": "nop-001", "PROGRAM": "Prog A", "KATEGORI": "Cat 2"} # Category changed
            ])
            summary2 = process_export.detect_and_sync_changes(conn, df2, "file2.xlsx")
            self.assertEqual(summary2["updated_records"], 1)
            self.assertEqual(len(summary2["modifications"]), 1)
            self.assertEqual(summary2["modifications"][0]["field"], "KATEGORI")
            self.assertEqual(summary2["modifications"][0]["old"], "Cat 1")
            self.assertEqual(summary2["modifications"][0]["new"], "Cat 2")
            
            # Verify updated state
            df_curr = process_export.load_current(conn)
            self.assertEqual(df_curr.iloc[0]["KATEGORI"], "Cat 2")
            
            # 3. Rollback
            success = process_export.rollback_record(conn, "nop-001")
            self.assertTrue(success)
            
            # Verify rolled back state
            df_curr = process_export.load_current(conn)
            self.assertEqual(df_curr.iloc[0]["KATEGORI"], "Cat 1")
        finally:
            conn.close()

if __name__ == "__main__":
    unittest.main()
