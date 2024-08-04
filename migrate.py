from dotenv import load_dotenv
import os
from ypostgres_lib import get_conn, run_static_dml

if __name__ == "__main__":

    load_dotenv()

    # migrate the database
    create_users_table = f"""CREATE TABLE IF NOT EXISTS {os.environ.get("POSTGRES_DATABASE")}.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);"""
    run_static_dml(get_conn(), create_users_table)
