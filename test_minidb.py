import tempfile
import unittest

from storage import FileStorage


class MiniDBTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = FileStorage(self.temp_dir.name)

        self.db.create_table(
            "datasets",
            {
                "id": "INT",
                "name": "STRING",
                "task": "STRING",
                "size": "INT",
            },
            primary_key="id",
        )

        self.db.create_table(
            "models",
            {
                "id": "INT",
                "name": "STRING",
                "version": "STRING",
            },
            primary_key="id",
        )

        self.db.create_table(
            "experiments",
            {
                "id": "INT",
                "dataset_id": "INT",
                "model_id": "INT",
                "accuracy": "FLOAT",
                "status": "STRING",
            },
            primary_key="id",
            foreign_keys={
                "dataset_id": ("datasets", "id"),
                "model_id": ("models", "id"),
            },
        )

        self.db.insert("datasets", {
            "id": 1,
            "name": "Images",
            "task": "classification",
            "size": 5000,
        })
        self.db.insert("datasets", {
            "id": 2,
            "name": "Text",
            "task": "classification",
            "size": 100,
        })
        self.db.insert("models", {
            "id": 1,
            "name": "CNN",
            "version": "1.0",
        })

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_primary_key_must_be_unique(self):
        with self.assertRaises(ValueError):
            self.db.insert("datasets", {
                "id": 1,
                "name": "Duplicate",
                "task": "classification",
                "size": 200,
            })

    def test_foreign_key_must_exist(self):
        with self.assertRaises(ValueError):
            self.db.insert("experiments", {
                "id": 1,
                "dataset_id": 999,
                "model_id": 1,
                "accuracy": 0.9,
                "status": "completed",
            })

    def test_select_columns_and_filter(self):
        result = self.db.select(
            "datasets",
            columns=["name"],
            where=("size", ">", 1000),
        )
        self.assertEqual(result, [{"name": "Images"}])

    def test_select_and(self):
        result = self.db.select(
            "datasets",
            columns=["id"],
            where=[
                ("size", ">", 1000),
                ("task", "=", "classification"),
            ],
            logic="AND",
        )
        self.assertEqual(result, [{"id": "1"}])

    def test_select_or(self):
        result = self.db.select(
            "datasets",
            columns=["id"],
            where=[
                ("size", "<", 200),
                ("size", ">", 4000),
            ],
            logic="OR",
        )
        self.assertEqual(
            {row["id"] for row in result},
            {"1", "2"},
        )

    def test_update_record(self):
        self.db.update("datasets", 1, {"size": 6000})
        result = self.db.select(
            "datasets",
            columns=["size"],
            where=("id", "=", 1),
        )
        self.assertEqual(result, [{"size": "6000"}])

    def test_delete_record(self):
        self.db.delete("datasets", 2)
        self.assertEqual(len(self.db.read_all("datasets")), 1)

    def test_cannot_delete_referenced_dataset(self):
        self.db.insert("experiments", {
            "id": 1,
            "dataset_id": 1,
            "model_id": 1,
            "accuracy": 0.95,
            "status": "completed",
        })
        with self.assertRaises(ValueError):
            self.db.delete("datasets", 1)

    def test_data_persists_after_reopening_storage(self):
        reopened_db = FileStorage(self.temp_dir.name)
        self.assertEqual(len(reopened_db.read_all("datasets")), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
