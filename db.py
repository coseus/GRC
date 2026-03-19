import sqlite3
from datetime import datetime

import sqlite3

DB_NAME = "assessment.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Companies
    c.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    # Assessments
    c.execute("""
    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        name TEXT NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    )
    """)

    # Answers
    c.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER,
        domain TEXT,
        question TEXT,
        score INTEGER,              -- NULL pentru Not Applicable
        notes TEXT,
        proof TEXT,
        FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
    )
    """)

    # Manual recommendations - cu câmpuri extinse
    c.execute("""
    CREATE TABLE IF NOT EXISTS manual_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER,
        text TEXT NOT NULL,
        risk TEXT CHECK(risk IN ('Low','Medium','High','Critical')),
        domain TEXT,
        responsible TEXT,
        deadline DATE,
        status TEXT DEFAULT 'Open' CHECK(status IN ('Open','In Progress','Done','Rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()


def create_company(name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO companies (name) VALUES (?)", (name.strip(),))
    conn.commit()
    cid = c.lastrowid
    conn.close()
    return cid


def get_companies():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name FROM companies ORDER BY name")
    data = c.fetchall()
    conn.close()
    return data


def create_assessment(company_id, name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO assessments (company_id, name) VALUES (?, ?)",
        (company_id, name.strip())
    )
    conn.commit()
    aid = c.lastrowid
    conn.close()
    return aid


def save_answer(assessment_id, domain, question, score, notes, proof):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    INSERT INTO answers (assessment_id, domain, question, score, notes, proof)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (assessment_id, domain, question, score, notes or "", proof or ""))
    conn.commit()
    conn.close()


def get_answers_for_assessment(assessment_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    SELECT domain, question, score, notes, proof
    FROM answers WHERE assessment_id = ?
    ORDER BY domain, question
    """, (assessment_id,))
    rows = c.fetchall()
    conn.close()
    return [{"domain": r[0], "question": r[1], "score": r[2], "notes": r[3], "proof": r[4]} for r in rows]


def add_manual_recommendation(assessment_id, text, risk, domain, responsible="", deadline=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    INSERT INTO manual_recommendations 
    (assessment_id, text, risk, domain, responsible, deadline)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (assessment_id, text.strip(), risk, domain, responsible.strip() or None, deadline))
    conn.commit()
    conn.close()


def get_manual_recommendations(assessment_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    SELECT id, text, risk, domain, responsible, deadline, status, created_at
    FROM manual_recommendations
    WHERE assessment_id = ?
    ORDER BY created_at
    """, (assessment_id,))
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "text": r[1], "risk": r[2], "domain": r[3],
            "responsible": r[4], "deadline": r[5], "status": r[6], "created_at": r[7]
        }
        for r in rows
    ]


def update_manual_recommendation(reco_id, text, risk, responsible, deadline, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    UPDATE manual_recommendations
    SET text = ?, risk = ?, responsible = ?, deadline = ?, status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (text.strip(), risk, responsible.strip() or None, deadline, status, reco_id))
    conn.commit()
    conn.close()


def delete_manual_recommendation(reco_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM manual_recommendations WHERE id = ?", (reco_id,))
    conn.commit()
    conn.close()

def get_assessment_scores():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT 
        a.name AS assessment_name,
        comp.name AS company_name,
        AVG(ans.score * q.weight) / AVG(q.weight) AS weighted_avg_score
    FROM assessments a
    JOIN companies comp ON a.company_id = comp.id
    LEFT JOIN answers ans ON ans.assessment_id = a.id
    LEFT JOIN (
        -- presupunem ca weight vine din JSON, dar pentru simplitate folosim 1 daca nu ai salvat
        SELECT DISTINCT question, 1 AS weight FROM answers
    ) q ON ans.question = q.question
    GROUP BY a.id
    ORDER BY a.date DESC
    """)

    data = c.fetchall()
    conn.close()
    return data
