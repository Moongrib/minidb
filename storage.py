import csv
import os

from schema import TableSchema


class FileStorage:
    def __init__(self, database_path="data"):
        self.database_path = database_path
        os.makedirs(database_path, exist_ok=True)

    def create_table(self, table_name, columns, primary_key):
        schema = TableSchema(table_name, columns, primary_key)

        file_path = os.path.join(
            self.database_path, f"{table_name}.csv"
        )

        if os.path.exists(file_path):
            with open(
                file_path, "r", newline="", encoding="utf-8"
            ) as file:
                saved_columns = next(csv.reader(file), None)

            if saved_columns != list(columns.keys()):
                raise ValueError(
                    "Заголовки существующего файла не совпадают со схемой"
                )
        else:
            with open(
                file_path, "w", newline="", encoding="utf-8"
            ) as file:
                csv.writer(file).writerow(columns.keys())

        schema.save(self.database_path)

    def get_schema(self, table_name):
        return TableSchema.load(self.database_path, table_name)

    def insert(self, table_name, record):
        schema = self.get_schema(table_name)
        schema.validate_record(record)

        file_path = os.path.join(
            self.database_path, f"{table_name}.csv"
        )

        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Таблица {table_name} не существует"
            )

        with open(
            file_path, "r", newline="", encoding="utf-8"
        ) as file:
            reader = csv.reader(file)
            columns = next(reader, None)

        if columns != list(schema.columns.keys()):
            raise ValueError("Файл таблицы не соответствует схеме")

        with open(
            file_path, "a", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writerow(record)

    def read_all(self, table_name):
        
        self.get_schema(table_name)

        file_path = os.path.join(
            self.database_path, f"{table_name}.csv"
        )

        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Файл таблицы {table_name} не найден"
            )

        with open(
            file_path, "r", newline="", encoding="utf-8"
        ) as file:
            return list(csv.DictReader(file))
