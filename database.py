import sqlite3

DB_NAME = "interns.db"

def create_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn


def create_table():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interns (
        id TEXT,
        name TEXT,
        intern_type TEXT,
        paid_unpaid TEXT,
        location TEXT,
        college_name TEXT,
        business_unit TEXT,
        line_of_service TEXT,
        date_of_joining TEXT,
        duration TEXT,
        expected_completion_date TEXT,
        actual_completion_date TEXT,
        quarter_joined TEXT,
        quarter_converted_relieved TEXT,
        status TEXT,
        project_associates TEXT,
        resumes TEXT,
        monthly_evaluation TEXT,
        fte_recommendation TEXT
    )
    """)

    conn.commit()
    conn.close()