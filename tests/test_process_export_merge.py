import os
import unittest
import pandas as pd
import sqlite3
from process_export import process, connect_db


class TestProcessExportMerge(unittest.TestCase):
    def setUp(self):
        base = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(base)
        self.db_path = os.path.join(self.project_dir, "data_pipeline.sqlite")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.out_path = os.path.join(self.project_dir, "merged_current.xlsx")
        if os.path.exists(self.out_path):
            os.remove(self.out_path)

    def test_merge_two_exports(self):
        f1 = os.path.join(self.project_dir, "large_sample_data_program.xlsx")
        f2 = os.path.join(self.project_dir, "large_sample_data_program_v2.xlsx")
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        process(f1)
        process(f2)
        conn = connect_db()
        df_current = pd.read_sql_query("SELECT * FROM records_current", conn)
        conn.close()
        self.assertGreaterEqual(len(df_current), 100)
        self.assertTrue(os.path.exists(self.out_path))
        df_merged = pd.read_excel(self.out_path)
        self.assertEqual(len(df_current), len(df_merged))


if __name__ == "__main__":
    unittest.main()
