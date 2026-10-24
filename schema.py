import os
import re

SUPPORTED_TYPES = {"INT", "STRING", "FLOAT"}


class TableSchema:
    def __init__(
        self, table_name, columns, primary_key, foreign_keys=None
    ):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
            raise ValueError("Некорректное имя таблицы")

        if not columns:
            raise ValueError("Таблица должна содержать столбцы")

        if len(columns) != len(set(columns)):
            raise ValueError("Названия столбцов не должны повторяться")

        for column, data_type in columns.items():
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", column):
                raise ValueError(f"Некорректное имя столбца: {column}")
            if data_type not in SUPPORTED_TYPES:
                raise ValueError(f"Неизвестный тип: {data_type}")

        if primary_key not in columns:
            raise ValueError("PRIMARY KEY должен существовать в таблице")

        if columns[primary_key] != "INT":
            raise ValueError("PRIMARY KEY должен иметь тип INT")

        self.table_name = table_name
        self.columns = dict(columns)
        self.primary_key = primary_key
        self.foreign_keys = dict(foreign_keys or {})

        for column, reference in self.foreign_keys.items():
            if column not in self.columns:
                raise ValueError(
                    f"Внешний ключ ссылается на неизвестный столбец: {column}"
                )
            if not isinstance(reference, tuple) or len(reference) != 2:
                raise ValueError(
                    "Внешний ключ должен содержать таблицу и столбец"
                )

    def save(self, database_path):
        os.makedirs(database_path, exist_ok=True)
        path = os.path.join(
            database_path, f"{self.table_name}.schema"
        )

        with open(path, "w", encoding="utf-8") as file:
            file.write(f"TABLE\t{self.table_name}\n")
            file.write(f"PRIMARY_KEY\t{self.primary_key}\n")

            for name, data_type in self.columns.items():
                file.write(f"COLUMN\t{name}\t{data_type}\n")

            for column, reference in self.foreign_keys.items():
                ref_table, ref_column = reference
                file.write(
                    f"FOREIGN_KEY\t{column}\t{ref_table}\t{ref_column}\n"
                )

    @classmethod
    def load(cls, database_path, table_name):
        path = os.path.join(database_path, f"{table_name}.schema")
        columns = {}
        foreign_keys = {}
        saved_table = None
        primary_key = None

        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                parts = line.rstrip("\n").split("\t")

                if parts[0] == "TABLE" and len(parts) == 2:
                    saved_table = parts[1]
                elif parts[0] == "PRIMARY_KEY" and len(parts) == 2:
                    primary_key = parts[1]
                elif parts[0] == "COLUMN" and len(parts) == 3:
                    columns[parts[1]] = parts[2]
                elif parts[0] == "FOREIGN_KEY" and len(parts) == 4:
                    foreign_keys[parts[1]] = (parts[2], parts[3])
                else:
                    raise ValueError("Повреждён файл схемы")

        if saved_table != table_name or primary_key is None:
            raise ValueError("Некорректная схема таблицы")

        return cls(
            saved_table, columns, primary_key, foreign_keys
        )

    def validate_record(self, record):
        if set(record.keys()) != set(self.columns.keys()):
            raise ValueError("Поля записи не совпадают со схемой")

        for name, data_type in self.columns.items():
            value = record[name]

            if data_type == "INT":
                if isinstance(value, bool) or not isinstance(value, int):
                    raise TypeError(f"{name} должен быть INT")
            elif data_type == "STRING":
                if not isinstance(value, str):
                    raise TypeError(f"{name} должен быть STRING")
            elif data_type == "FLOAT":
                if isinstance(value, bool) or not isinstance(
                    value, (int, float)
                ):
                    raise TypeError(f"{name} должен быть FLOAT")
