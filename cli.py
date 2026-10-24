import re

from storage import FileStorage

db = FileStorage("data")

def parse_value(value, data_type):
    value = value.strip()

    if data_type == "INT":
        return int(value)
    if data_type == "FLOAT":
        return float(value)
    return value

def show_rows(rows):
    if not rows:
        print("Записи не найдены.")
        return

    columns = list(rows[0].keys())
    widths = {
        column: max(
            len(column),
            *(len(str(row[column])) for row in rows)
        )
        for column in columns
    }

    header = " | ".join(
        column.ljust(widths[column]) for column in columns
    )
    print(header)
    print("-+-".join("-" * widths[c] for c in columns))

    for row in rows:
        print(" | ".join(
            str(row[column]).ljust(widths[column])
            for column in columns
        ))

def choose_table():
    tables = db.list_tables()

    if not tables:
        print("Таблиц нет. Сначала запустите python main.py")
        return None

    print("Доступные таблицы:", ", ".join(tables))
    table = input("Имя таблицы: ").strip()

    if table not in tables:
        print("Такой таблицы нет.")
        return None

    return table

def insert_record():
    table = choose_table()
    if table is None:
        return

    schema = db.get_schema(table)
    record = {}

    for column, data_type in schema.columns.items():
        value = input(f"{column} ({data_type}): ")
        record[column] = parse_value(value, data_type)

    db.insert(table, record)
    print("Запись добавлена.")

def select_records():
    table = choose_table()
    if table is None:
        return

    schema = db.get_schema(table)
    raw_columns = input(
        "Столбцы через запятую (Enter — все): "
    ).strip()

    columns = (
        [item.strip() for item in raw_columns.split(",")]
        if raw_columns else None
    )

    raw_where = input(
        "Условия через запятую, например size > 1000, task = classification "
        "(Enter — без фильтра): "
    ).strip()

    where = None
    logic = "AND"

    if raw_where:
        logic = input("Логика AND или OR [AND]: ").strip().upper() or "AND"

        if logic not in {"AND", "OR"}:
            raise ValueError("Нужно выбрать AND или OR")

        where = []
        pattern = r"^\s*([A-Za-z_]\w*)\s*(>=|<=|!=|=|>|<)\s*(.*?)\s*$"

        for item in raw_where.split(","):
            match = re.fullmatch(pattern, item)

            if not match:
                raise ValueError(
                    f"Некорректное условие: {item}"
                )

            column, operator, raw_value = match.groups()

            if column not in schema.columns:
                raise ValueError(f"Неизвестный столбец: {column}")

            value = parse_value(raw_value, schema.columns[column])
            where.append((column, operator, value))

    rows = db.select(
        table, columns=columns, where=where, logic=logic
    )
    show_rows(rows)


def update_record():
    table = choose_table()
    if table is None:
        return

    schema = db.get_schema(table)
    pk = schema.primary_key
    pk_value = parse_value(
        input(f"Значение PRIMARY KEY ({pk}): "),
        schema.columns[pk]
    )

    print("Столбцы:", ", ".join(schema.columns))
    print("Введи изменения в формате: name=NewName,size=500")
    raw_updates = input("Изменения: ").strip()

    updates = {}
    for item in raw_updates.split(","):
        if "=" not in item:
            raise ValueError(f"Некорректное изменение: {item}")

        column, raw_value = item.split("=", 1)
        column = column.strip()

        if column not in schema.columns:
            raise ValueError(f"Неизвестный столбец: {column}")

        updates[column] = parse_value(
            raw_value, schema.columns[column]
        )

    db.update(table, pk_value, updates)
    print("Запись обновлена.")


def delete_record():
    table = choose_table()
    if table is None:
        return

    schema = db.get_schema(table)
    pk = schema.primary_key
    pk_value = parse_value(
        input(f"Значение PRIMARY KEY ({pk}): "),
        schema.columns[pk]
    )

    confirmation = input(
        f"Удалить запись {pk}={pk_value}? (да/нет): "
    ).strip().lower()

    if confirmation == "да":
        db.delete(table, pk_value)
        print("Запись удалена.")
    else:
        print("Удаление отменено.")


def main():
    if not db.list_tables():
        print("Сначала запустите python main.py для создания таблиц.")
        return

    while True:
        print("\n=== MiniDB ===")
        print("1. Показать таблицы")
        print("2. Просмотреть данные")
        print("3. Добавить запись")
        print("4. Найти записи (SELECT)")
        print("5. Изменить запись (UPDATE)")
        print("6. Удалить запись (DELETE)")
        print("0. Выход")

        choice = input("Выберите действие: ").strip()

        try:
            if choice == "1":
                print("Таблицы:", ", ".join(db.list_tables()))
            elif choice == "2":
                table = choose_table()
                if table:
                    show_rows(db.read_all(table))
            elif choice == "3":
                insert_record()
            elif choice == "4":
                select_records()
            elif choice == "5":
                update_record()
            elif choice == "6":
                delete_record()
            elif choice == "0":
                print("До свидания!")
                break
            else:
                print("Неизвестный пункт меню.")
        except (ValueError, TypeError, FileNotFoundError) as error:
            print("Ошибка:", error)


if __name__ == "__main__":
    main()
