import os
import sqlite3
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "db" / "foxflow.db"
EXPORT_DIR = BASE_DIR / "exports"


def export_database():
    if not DB_PATH.exists():
        print(f"Error: Database file not found at {DB_PATH}")
        return

    EXPORT_DIR.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

    print(f"Found {len(tables)} tables in database: {', '.join(tables)}")

    exported_files = []

    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]

        csv_file_path = EXPORT_DIR / f"{table}.csv"
        with open(csv_file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(column_names)
            writer.writerows(rows)

        exported_files.append(csv_file_path)
        print(f"  [✓] Exported '{table}' ({len(rows)} rows) -> {csv_file_path.name}")


    try:
        import pandas as pd
        excel_file_path = EXPORT_DIR / "foxflow_all_data.xlsx"
        with pd.ExcelWriter(excel_file_path, engine="openpyxl") as writer:
            for table in tables:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                df.to_excel(writer, sheet_name=table[:31], index=False)
        print(f"\n[★] Multi-sheet Excel workbook created: {excel_file_path}")
    except ImportError:
        print("\nNote: Install 'pandas' and 'openpyxl' (`pip install pandas openpyxl`) to get a single multi-sheet .xlsx file.")

    conn.close()

    print(f"\nAll data exported successfully to folder: {EXPORT_DIR.resolve()}")
    print("You can double-click any .csv file to open it directly in Microsoft Excel!")


if __name__ == "__main__":
    export_database()
