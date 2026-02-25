import os
import unittest
import pandas as pd
import web_app


class TestWebAppLoading(unittest.TestCase):
    def setUp(self):
        base = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(base)
        self.merged_path = os.path.join(self.project_dir, "merged_current.xlsx")
        os.environ["EXCEL_DASHBOARD_FILE"] = self.merged_path

    def test_load_dataframe_prefers_merged_snapshot_or_db(self):
        self.assertTrue(os.path.exists(self.merged_path))
        df = web_app.load_dataframe()
        self.assertGreaterEqual(len(df), 100)
        self.assertGreater(len(df.columns), 0)


if __name__ == "__main__":
    unittest.main()
