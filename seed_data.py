from storage import FileStorage


db = FileStorage("data")


def fill_table(table_name, records, minimum):
    existing = db.read_all(table_name)
    existing_ids = {int(row["id"]) for row in existing}
    next_id = max(existing_ids, default=0) + 1

    for record in records:
        if len(existing_ids) >= minimum:
            break

        record["id"] = next_id
        db.insert(table_name, record)
        existing_ids.add(next_id)
        next_id += 1

    return db.read_all(table_name)


datasets = fill_table(
    "datasets",
    [
        {"name": "MNIST", "task": "classification", "size": 70000},
        {"name": "CIFAR-10", "task": "classification", "size": 60000},
        {"name": "IMDB", "task": "sentiment", "size": 50000},
        {"name": "ImageNet", "task": "classification", "size": 1000000},
        {"name": "Housing", "task": "regression", "size": 20000},
    ],
    5,
)

models = fill_table(
    "models",
    [
        {"name": "CNN", "version": "1.0"},
        {"name": "ResNet", "version": "2.1"},
        {"name": "RandomForest", "version": "1.2"},
        {"name": "LinearRegression", "version": "1.0"},
        {"name": "Transformer", "version": "3.0"},
    ],
    5,
)

dataset_ids = [int(row["id"]) for row in datasets]
model_ids = [int(row["id"]) for row in models]

experiments = db.read_all("experiments")
existing_experiment_ids = {
    int(row["id"]) for row in experiments
}
next_id = max(existing_experiment_ids, default=0) + 1

while len(experiments) < 20:
    i = len(experiments)

    record = {
        "id": next_id,
        "dataset_id": dataset_ids[i % len(dataset_ids)],
        "model_id": model_ids[i % len(model_ids)],
        "accuracy": round(0.70 + (i % 25) / 100, 2),
        "status": "completed" if i % 4 else "pending",
    }

    db.insert("experiments", record)
    experiments.append(record)
    next_id += 1

print("База заполнена.")
for table in ("datasets", "models", "experiments"):
    print(f"{table}: {len(db.read_all(table))} записей")
