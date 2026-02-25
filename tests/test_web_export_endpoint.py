import os
import unittest
import pandas as pd
from process_export import process, connect_db
from web_app import app, load_dataframe


class TestWebExportEndpoint(unittest.TestCase):
    def setUp(self):
        base = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(base)
        self.db_path = os.path.join(self.project_dir, "data_pipeline.sqlite")
        self.merged_path = os.path.join(self.project_dir, "merged_current.xlsx")
        f1 = os.path.join(self.project_dir, "large_sample_data_program.xlsx")
        f2 = os.path.join(self.project_dir, "large_sample_data_program_v2.xlsx")
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        process(f1)
        process(f2)

    def test_export_uses_merged_data(self):
        df_loaded = load_dataframe()
        self.assertGreaterEqual(len(df_loaded), 100)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["logged_in"] = True
            resp = client.get("/export")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                resp.content_type,
            )
            tmp_path = os.path.join(self.project_dir, "tmp_export_test.xlsx")
            with open(tmp_path, "wb") as f:
                f.write(resp.data)
            df_exported = pd.read_excel(tmp_path)
            os.remove(tmp_path)
            self.assertEqual(len(df_loaded), len(df_exported))


if __name__ == "__main__":
    unittest.main()
