from storage import FileStorage


def main():
    db = FileStorage("data")

    db.create_table(
        "datasets",
        {
            "id": "INT",
            "name": "STRING",
            "task": "STRING",
            "size": "INT",
        },
        primary_key="id",
    )

    db.create_table(
        "models",
        {
            "id": "INT",
            "name": "STRING",
            "version": "STRING",
        },
        primary_key="id",
    )

    db.create_table(
        "experiments",
        {
            "id": "INT",
            "dataset_id": "INT",
            "model_id": "INT",
            "accuracy": "FLOAT",
            "status": "STRING"
        },
        primary_key="id",
        foreign_keys={
            "dataset_id": ("datasets", "id"),
            "model_id": ("models", "id")
        }
    )

    if not db.read_all("datasets"):
        db.insert(
            "datasets",
            {
                "id": 1,
                "name": "CIFAR-10",
                "task": "classification",
                "size": 60000,
            },
        )

    print("Схема datasets:")
    print(db.get_schema("datasets").columns)
    print("Первичный ключ:", db.get_schema("datasets").primary_key)

    print("\nДанные datasets:")
    for row in db.read_all("datasets"):
        print(row)

if __name__ == "__main__":
    main()
