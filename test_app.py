import unittest
import tempfile
from pathlib import Path
import app as findfit_app

class FindFitzSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = findfit_app.DB_PATH
        self.old_data = findfit_app.DATA_DIR
        findfit_app.DB_PATH = Path(self.temp.name) / "test.db"
        findfit_app.DATA_DIR = Path(self.temp.name) / "documents"
        findfit_app.initialize_db()
        findfit_app.app.config["TESTING"] = True
        self.client = findfit_app.app.test_client()

    def tearDown(self):
        findfit_app.DB_PATH = self.old_db
        findfit_app.DATA_DIR = self.old_data
        self.temp.cleanup()

    def test_home_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_search_page_loads(self):
        response = self.client.get("/?q=information")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
