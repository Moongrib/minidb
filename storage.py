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

    
    def insert_many(self, table_name, records):
        if not records:
            raise ValueError("Список записей пуст")

        for record in records:
            self.insert(table_name, record)

        print(f"Добавлено записей: {len(records)}")



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

    
    
    def select(self, table_name, columns=None, where=None, logic="AND"):
        schema = self.get_schema(table_name)
        rows = self.read_all(table_name)

        if columns is None:
            columns = list(schema.columns.keys())

        for column in columns:
            if column not in schema.columns:
                raise ValueError(
                    f"Столбец {column} не существует в таблице {table_name}"
                )

        if logic not in {"AND", "OR"}:
            raise ValueError("logic должен быть AND или OR")

        if where is not None:
            if (
                isinstance(where, tuple)
                and len(where) == 3
                and isinstance(where[0], str)
            ):
                conditions = [where]
            else:
                conditions = list(where)

            prepared = []
            operators = {"=", "!=", ">", "<", ">=", "<="}

            for condition in conditions:
                if len(condition) != 3:
                    raise ValueError(
                        "Условие должно иметь вид (столбец, оператор, значение)"
                    )

                column, operator, value = condition

                if column not in schema.columns:
                    raise ValueError(f"Неизвестный столбец: {column}")

                if operator not in operators:
                    raise ValueError(f"Неподдерживаемый оператор: {operator}")

                data_type = schema.columns[column]

                if data_type == "INT":
                    if isinstance(value, bool):
                        raise TypeError("Ожидалось значение INT")
                    value = int(value)
                elif data_type == "FLOAT":
                    if isinstance(value, bool):
                        raise TypeError("Ожидалось значение FLOAT")
                    value = float(value)
                elif data_type == "STRING":
                    value = str(value)

                prepared.append((column, operator, value, data_type))

            def matches_condition(row, condition):
                column, operator, value, data_type = condition
                raw = row[column]

                if data_type == "INT":
                    actual = int(raw)
                elif data_type == "FLOAT":
                    actual = float(raw)
                else:
                    actual = raw

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
                return actual <= value

            def matches_row(row):
                results = [
                    matches_condition(row, condition)
                    for condition in prepared
                ]
                return all(results) if logic == "AND" else any(results)

            rows = [row for row in rows if matches_row(row)]

        return [
            {column: row[column] for column in columns}
            for row in rows
        ]

    
    def list_tables(self):
        return sorted(
            filename[:-7]
            for filename in os.listdir(self.database_path)
            if filename.endswith(".schema")
        )

    def update(self, table_name, primary_key_value, updates):
        schema = self.get_schema(table_name)
        rows = self.read_all(table_name)
        pk = schema.primary_key

        if not updates:
            raise ValueError("Не указаны изменения")

        for column in updates:
            if column not in schema.columns:
                raise ValueError(f"Неизвестный столбец: {column}")

        index = next(
            (
                i for i, row in enumerate(rows)
                if row[pk] == str(primary_key_value)
            ),
            None
        )

        if index is None:
            raise ValueError(
                f"Запись с {pk}={primary_key_value} не найдена"
            )

        candidate = {}
        for column, data_type in schema.columns.items():
            raw = rows[index][column]
            if data_type == "INT":
                candidate[column] = int(raw)
            elif data_type == "FLOAT":
                candidate[column] = float(raw)
            else:
                candidate[column] = raw

        for column, value in updates.items():
            data_type = schema.columns[column]
            if data_type == "INT":
                if isinstance(value, bool):
                    raise TypeError(f"{column} должен быть INT")
                candidate[column] = int(value)
            elif data_type == "FLOAT":
                if isinstance(value, bool):
                    raise TypeError(f"{column} должен быть FLOAT")
                candidate[column] = float(value)
            else:
                candidate[column] = str(value)

        schema.validate_record(candidate)

        new_pk = str(candidate[pk])
        for i, row in enumerate(rows):
            if i != index and row[pk] == new_pk:
                raise ValueError(
                    f"PRIMARY KEY {new_pk} уже существует"
                )

        for column, reference in schema.foreign_keys.items():
            ref_table, ref_column = reference
            referenced_rows = self.read_all(ref_table)
            value = str(candidate[column])

            if not any(
                row[ref_column] == value for row in referenced_rows
            ):
                raise ValueError(
                    f"FOREIGN KEY: {value} отсутствует в "
                    f"{ref_table}.{ref_column}"
                )

        rows[index] = {
            column: str(candidate[column])
            for column in schema.columns
        }

        file_path = os.path.join(
            self.database_path, f"{table_name}.csv"
        )
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file, fieldnames=list(schema.columns.keys())
            )
            writer.writeheader()
            writer.writerows(rows)

    def delete(self, table_name, primary_key_value):
        schema = self.get_schema(table_name)
        pk = schema.primary_key
        rows = self.read_all(table_name)

        target = next(
            (row for row in rows
             if row[pk] == str(primary_key_value)),
            None
        )

        if target is None:
            raise ValueError(
                f"Запись с {pk}={primary_key_value} не найдена"
            )

        for other_table in self.list_tables():
            other_schema = self.get_schema(other_table)

            for column, reference in other_schema.foreign_keys.items():
                ref_table, ref_column = reference

                if ref_table != table_name or ref_column != pk:
                    continue

                for row in self.read_all(other_table):
                    if row[column] == target[pk]:
                        raise ValueError(
                            f"Удаление запрещено: {other_table}."
                            f"{column} ссылается на эту запись"
                        )

        rows = [row for row in rows if row[pk] != target[pk]]

        file_path = os.path.join(
            self.database_path, f"{table_name}.csv"
        )
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file, fieldnames=list(schema.columns.keys())
            )
            writer.writeheader()
            writer.writerows(rows)



