import hashlib
import sqlite3

DB_NAME = "assessment.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _table_columns(conn, table_name: str):
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _ensure_column(conn, table_name: str, column_name: str, column_sql: str):
    if column_name not in _table_columns(conn, table_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','auditor','viewer')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                user_id INTEGER,
                name TEXT NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL,
                domain_id TEXT,
                domain_name TEXT,
                question_id TEXT,
                question_text TEXT,
                answer_value TEXT,
                score INTEGER,
                notes TEXT,
                proof TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
            )
        """)

        _ensure_column(conn, "answers", "answer_value", "answer_value TEXT")

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_answers_assessment_question
            ON answers(assessment_id, question_id)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS executive_summary (
                assessment_id INTEGER PRIMARY KEY,
                summary TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL,
                domain_id TEXT,
                domain_name TEXT,
                source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('auto','manual')),
                recommendation_key TEXT,
                text TEXT NOT NULL,
                risk TEXT NOT NULL CHECK(risk IN ('Low','Medium','High','Critical')),
                responsible TEXT,
                deadline DATE,
                status TEXT NOT NULL DEFAULT 'Open'
                    CHECK(status IN ('Open','In Progress','Done','Rejected')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
            )
        """)

        _ensure_column(conn, "recommendations", "recommendation_key", "recommendation_key TEXT")

        user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        if user_count == 0:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", hash_password("admin"), "admin"),
            )


def verify_user(username: str, password: str):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, username, role
            FROM users
            WHERE username = ? AND password_hash = ? AND is_active = 1
            """,
            (username, hash_password(password)),
        ).fetchone()
        return dict(row) if row else None


def create_user(username: str, password: str, role: str):
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, hash_password(password), role),
            )
        return True, "User created."
    except sqlite3.IntegrityError:
        return False, "Username already exists."


def list_users():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, username, role, is_active, created_at FROM users ORDER BY username"
        ).fetchall()
        return [dict(r) for r in rows]


def get_user_by_id(user_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, role, is_active, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def update_user(user_id: int, username: str, role: str, is_active: bool):
    try:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE users
                SET username = ?, role = ?, is_active = ?
                WHERE id = ?
                """,
                (username, role, 1 if is_active else 0, user_id),
            )
        return True, "User updated."
    except sqlite3.IntegrityError:
        return False, "Username already exists."


def update_user_password(user_id: int, new_password: str):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (hash_password(new_password), user_id),
        )
    return True, "Password updated."


def delete_user(user_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return True, "User deleted."


def create_company(name: str):
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM companies WHERE name = ?", (name,)).fetchone()
        if row:
            return row["id"]
        cur = conn.execute("INSERT INTO companies (name) VALUES (?)", (name,))
        return cur.lastrowid


def get_companies():
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name, created_at FROM companies ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def create_assessment(company_id: int, user_id: int, name: str):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO assessments (company_id, user_id, name) VALUES (?, ?, ?)",
            (company_id, user_id, name),
        )
        return cur.lastrowid


def get_assessments_for_company(company_id: int):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, company_id, user_id, name, date
            FROM assessments
            WHERE company_id = ?
            ORDER BY date DESC, id DESC
            """,
            (company_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_assessment_details(assessment_id: int):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, company_id, user_id, name, date
            FROM assessments
            WHERE id = ?
            """,
            (assessment_id,),
        ).fetchone()
        return dict(row) if row else None


def upsert_answer(
    assessment_id: int,
    domain_id: str,
    domain_name: str,
    question_id: str,
    question_text: str,
    answer_value,
    score,
    notes: str,
    proof: str,
):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO answers (
                assessment_id, domain_id, domain_name, question_id, question_text,
                answer_value, score, notes, proof, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(assessment_id, question_id)
            DO UPDATE SET
                domain_id = excluded.domain_id,
                domain_name = excluded.domain_name,
                question_text = excluded.question_text,
                answer_value = excluded.answer_value,
                score = excluded.score,
                notes = excluded.notes,
                proof = excluded.proof,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                assessment_id,
                domain_id,
                domain_name,
                question_id,
                question_text,
                answer_value,
                score,
                notes or "",
                proof or "",
            ),
        )


def get_answers_for_assessment(assessment_id: int):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT assessment_id, domain_id, domain_name, question_id, question_text,
                   answer_value, score, notes, proof, updated_at
            FROM answers
            WHERE assessment_id = ?
            ORDER BY domain_name, question_text
            """,
            (assessment_id,),
        ).fetchall()

        result = {}
        for row in rows:
            d = dict(row)
            if d["question_id"]:
                result[d["question_id"]] = d
        return result


def save_executive_summary(assessment_id: int, summary: str):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO executive_summary (assessment_id, summary, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(assessment_id)
            DO UPDATE SET summary = excluded.summary, updated_at = CURRENT_TIMESTAMP
            """,
            (assessment_id, summary or ""),
        )


def get_executive_summary(assessment_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT summary FROM executive_summary WHERE assessment_id = ?",
            (assessment_id,),
        ).fetchone()
        return row["summary"] if row else ""


def add_recommendation(
    assessment_id: int,
    domain_id: str,
    domain_name: str,
    text: str,
    risk: str,
    source: str = "manual",
    recommendation_key: str = "",
    responsible: str = "",
    deadline=None,
    status: str = "Open",
):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO recommendations (
                assessment_id, domain_id, domain_name, source, recommendation_key, text, risk,
                responsible, deadline, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assessment_id,
                domain_id,
                domain_name,
                source,
                recommendation_key or None,
                text,
                risk,
                responsible or None,
                deadline,
                status,
            ),
        )


def get_recommendations(assessment_id: int):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, assessment_id, domain_id, domain_name, source, recommendation_key, text, risk,
                   responsible, deadline, status, created_at, updated_at
            FROM recommendations
            WHERE assessment_id = ?
            ORDER BY
                CASE risk
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                    ELSE 5
                END,
                COALESCE(responsible, ''),
                CASE WHEN deadline IS NULL OR deadline = '' THEN '9999-12-31' ELSE deadline END,
                domain_name,
                created_at DESC,
                id DESC
            """,
            (assessment_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def update_recommendation(
    reco_id: int,
    text: str,
    risk: str,
    responsible: str,
    deadline,
    status: str,
):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE recommendations
            SET text = ?, risk = ?, responsible = ?, deadline = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (text, risk, responsible or None, deadline, status, reco_id),
        )


def delete_recommendation(reco_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM recommendations WHERE id = ?", (reco_id,))
