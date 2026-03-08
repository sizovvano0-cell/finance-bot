import aiosqlite
from datetime import datetime

DB_NAME = 'finance.db'

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                category TEXT,
                description TEXT,
                date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        await db.commit()

async def add_user(user_id: int, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
            (user_id, username)
        )
        await db.commit()

async def add_transaction(user_id: int, trans_type: str, amount: float, 
                         category: str, description: str = ''):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO transactions (user_id, type, amount, category, description, date)
            VALUES (?, ?, ?, ?, ?, DATE('now'))
        ''', (user_id, trans_type, amount, category, description))
        await db.commit()

async def get_monthly_report(user_id: int, year: int, month: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE user_id = ? AND type = 'income'
            AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            GROUP BY category
        ''', (user_id, str(year), f'{month:02d}'))
        incomes = await cursor.fetchall()
        
        cursor = await db.execute('''
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE user_id = ? AND type = 'expense'
            AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            GROUP BY category
        ''', (user_id, str(year), f'{month:02d}'))
        expenses = await cursor.fetchall()
        
        cursor = await db.execute('''
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense
            FROM transactions
            WHERE user_id = ? 
            AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
        ''', (user_id, str(year), f'{month:02d}'))
        totals = await cursor.fetchone()
        
        return incomes, expenses, totals

async def get_last_transactions(user_id: int, limit: int = 10):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            SELECT type, amount, category, description, date
            FROM transactions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        return await cursor.fetchall()

async def delete_last_transaction(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            DELETE FROM transactions
            WHERE id = (
                SELECT id FROM transactions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            )
        ''', (user_id,))
        await db.commit()
