import pandas as pd
import psycopg
import os
from dotenv import load_dotenv
load_dotenv()


DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

TABLES = [
    "live_tracking_apilog",
    "live_tracking_apitoken",
    "live_tracking_livelocation",
    "live_tracking_smslog",
    "live_tracking_trackingsession",
]

OUTPUT_FILE = "live_tracking_tables.xlsx"


def export_tables():
    conn = psycopg.connect(**DB_CONFIG)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for table in TABLES:
            print(f"Exporting {table}")

            df = pd.read_sql(
                f'SELECT * FROM "{table}"',
                conn
            )

            # Remove timezone information from datetime columns
            for col in df.select_dtypes(include=["datetime64[ns, UTC]", "datetimetz"]).columns:
                df[col] = df[col].dt.tz_localize(None)

            df.to_excel(
                writer,
                sheet_name=table[:31],
                index=False
            )

    conn.close()
    print(f"\nExport completed: {OUTPUT_FILE}")


if __name__ == "__main__":
    export_tables()