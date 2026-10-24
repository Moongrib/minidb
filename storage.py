import csv
import os

from schema import TableSchema


class FileStorage:
    def __init__(self, database_path="data"):
        self.database_path = database_path
        os.makedirs(database_path, exist_ok=True)

    def create_table(
        self, table_name, columns, primary_key, foreign_keys=None
    ):
        schema = TableSchema(
            table_name, columns, primary_key, foreign_keys
        )

        for column, reference in schema.foreign_keys.items():
            ref_table, ref_column = reference
            ref_schema = self.get_schema(ref_table)

            if ref_column not in ref_schema.columns:
                raise ValueError(
                    f"Столбец {ref_column} не существует в таблице {ref_table}"
                )

            if ref_schema.columns[ref_column] != schema.columns[column]:
                raise ValueError("Типы внешнего и связанного ключей не совпадают")

            if ref_column != ref_schema.primary_key:
                raise ValueError(
                    "Внешний ключ должен ссылаться на PRIMARY KEY"
                )

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
                f"Файл таблицы {table_name} не найден"
            )

        with open(file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            if reader.fieldnames != list(schema.columns.keys()):
                raise ValueError(
                    "Файл таблицы не соответствует схеме"
                )

            primary_key = schema.primary_key
            new_id = str(record[primary_key])

            for row in reader:
                if row[primary_key] == new_id:
                    raise ValueError(
                        f"Нарушение PRIMARY KEY: "
                        f"{primary_key}={new_id} уже существует"
                    )

            for column, reference in schema.foreign_keys.items():
                ref_table, ref_column = reference
                referenced_rows = self.read_all(ref_table)
                new_value = str(record[column])

                if not any(
                    row[ref_column] == new_value
                    for row in referenced_rows
                ):
                    raise ValueError(
                        f"Нарушение FOREIGN KEY: значение "
                        f"{record[column]} отсутствует в "
                        f"{ref_table}.{ref_column}"
                    )
        
        with open(file_path, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file, fieldnames=list(schema.columns.keys())
            )
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

    
    def select(self, table_name, columns=None, where=None):
        schema = self.get_schema(table_name)
        rows = self.read_all(table_name)

        if columns is None:
            columns = list(schema.columns.keys())

        for column in columns:
            if column not in schema.columns:
                raise ValueError(
                    f"Столбец {column} не существует в таблице {table_name}"
                )
            
        if where is not None:
            if len(where) != 3:
                raise ValueError(
                    "Условие должно иметь вид (столбец, оператор, значение)"
                )

            column, operator, value = where

            if column not in schema.columns:
                raise ValueError(f"Неизвестный столбец: {column}")

            operators = {"=", "!=", ">", "<", ">=", "<="}
            if operator not in operators:
                raise ValueError(f"Неподдерживаемый оператор: {operator}")

            data_type = schema.columns[column]

            if data_type == "INT":
                if isinstance(value, bool):
                    raise TypeError("Ожидалось значение типа INT")
                value = int(value)
            elif data_type == "FLOAT":
                if isinstance(value, bool):
                    raise TypeError("Ожидалось значение типа FLOAT")
                value = float(value)
            elif data_type == "STRING":
                value = str(value)

            def convert(raw_value):
                if data_type == "INT":
                    return int(raw_value)
                if data_type == "FLOAT":
                    return float(raw_value)
                return raw_value

            def matches(row):
                actual = convert(row[column])

                if operator == "=":
                    return actual == value
                if operator == "!=":
                    return actual != value
                if operator == ">":
                    return actual > value
                if operator == "<":
                    return actual < value
                if operator == ">=":
                    return actual >= value
                if operator == "<=":
                    return actual <= value

            rows = [row for row in rows if matches(row)]

 
        return [
            {column: row[column] for column in columns}
            for row in rows
        ]

