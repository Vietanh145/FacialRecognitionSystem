from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, date
from tkcalendar import DateEntry
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List
from db_config import DB_CONFIG
import uvicorn
import tkinter as tk
import pandas as pd
from admin_interface import AdminInterface

app = FastAPI()

def start_admin_interface():
    root = tk.Tk()
    AdminInterface.start(root)
    root.mainloop()

class CheckInRequest(BaseModel):
    user_id: int

class LogResponse(BaseModel):
    id: int
    user_id: int
    date: Optional[date]
    time_in: Optional[datetime]
    time_out: Optional[datetime]
    status: Optional[str]
    user_name: Optional[str] = None
    role: Optional[str] = None

def get_db():
    return psycopg2.connect(**DB_CONFIG)

@app.post("/attendance/checkin", response_model=LogResponse)
def checkin(data: CheckInRequest):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    now = datetime.now()
    today = date.today()
    try:
        cur.execute("""
            SELECT l.*, u.user_name, u.role
            FROM logs l
            JOIN users u ON u.id = l.user_id
            WHERE l.user_id=%s AND l.date=%s AND l.time_out IS NULL
            ORDER BY l.time_in DESC LIMIT 1
        """, (data.user_id, today))
        log = cur.fetchone()
        if log:
            cur.execute("""
                UPDATE logs SET time_out=%s, status='checked_out'
                WHERE id=%s RETURNING *
            """, (now, log['id']))
            updated = cur.fetchone()
            cur.execute("SELECT user_name, role FROM users WHERE id=%s", (data.user_id,))
            acc = cur.fetchone()
            if acc:
                updated.update(acc)
            conn.commit()
            return updated
        else:
            cur.execute("""
                INSERT INTO logs (user_id, date, time_in, status)
                VALUES (%s, %s, %s, 'checked_in')
                RETURNING *
            """, (data.user_id, today, now))
            new_log = cur.fetchone()
            cur.execute("SELECT user_name, role FROM users WHERE id=%s", (data.user_id,))
            acc = cur.fetchone()
            if acc:
                new_log.update(acc)
            conn.commit()
            return new_log
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/attendance/status/{user_id}", response_model=LogResponse)
def get_status(user_id: int):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    today = date.today()
    try:
        cur.execute("""
            SELECT l.*, u.user_name, u.role
            FROM logs l
            JOIN users u ON u.id = l.user_id
            WHERE l.user_id=%s AND l.date=%s
            ORDER BY l.time_in DESC LIMIT 1
        """, (user_id, today))
        log = cur.fetchone()
        if not log:
            raise HTTPException(status_code=404, detail="No log found for today")
        return log
    finally:
        cur.close()
        conn.close()

@app.get("/logs", response_model=List[LogResponse])
def get_logs(user_id: Optional[int] = None):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if user_id:
            cur.execute("""
                SELECT l.*, u.user_name, u.role
                FROM logs l
                JOIN users u ON u.id = l.user_id
                WHERE l.user_id=%s
                ORDER BY l.time_in DESC
            """, (user_id,))
        else:
            cur.execute("""
                SELECT l.*, u.user_name, u.role
                FROM logs l
                JOIN users u ON u.id = l.user_id
                ORDER BY l.time_in DESC
            """)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import threading
    # Start admin interface in a separate thread
    admin_thread = threading.Thread(target=start_admin_interface, daemon=True)
    admin_thread.start()
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
