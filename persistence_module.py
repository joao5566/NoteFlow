import sqlite3
import os
from PyQt5.QtCore import QDate

DB_PATH = "data.db"

def init_db():
    """Inicializa o banco de dados e cria as tabelas, se necessário."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Tabela de tarefas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                completed INTEGER,
                creation_date TEXT,
                completion_date TEXT
            )
        ''')
        # Tabela de lembretes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                message TEXT
            )
        ''')
        # Tabela de notas (incluindo a coluna custom_css para regras personalizadas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                text TEXT,
                raw_text TEXT,
                categories TEXT,
                tags TEXT,
                is_markdown INTEGER DEFAULT 0,
                custom_css TEXT DEFAULT ""
            )
        ''')
        # Tabela de tema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS theme (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        # Tabela de Kanban - colunas e tarefas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kanban_columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kanban_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                priority TEXT,
                due_date TEXT,
                column_id INTEGER,
                FOREIGN KEY (column_id) REFERENCES kanban_columns(id)
            )
        ''')
        conn.commit()

        # Atualiza a tabela de notas para incluir as colunas raw_text, custom_css e is_markdown, se necessário
        cursor.execute("PRAGMA table_info(notes)")
        columns = [column[1] for column in cursor.fetchall()]
        if "raw_text" not in columns:
            cursor.execute("ALTER TABLE notes ADD COLUMN raw_text TEXT")
            conn.commit()
        if "custom_css" not in columns:
            cursor.execute("ALTER TABLE notes ADD COLUMN custom_css TEXT DEFAULT ''")
            conn.commit()
        if "is_markdown" not in columns:
            cursor.execute("ALTER TABLE notes ADD COLUMN is_markdown INTEGER DEFAULT 0")
            conn.commit()

def load_tasks():
    """Carrega todas as tarefas do banco de dados."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, completed, creation_date, completion_date FROM tasks")
        rows = cursor.fetchall()
        tasks = {}
        for task_id, name, completed, creation_date, completion_date in rows:
            tasks[task_id] = {
                "name": name,
                "completed": bool(completed),
                "creation_date": creation_date,
                "completion_date": completion_date
            }
        return tasks

def save_tasks(tasks):
    """Salva todas as tarefas no banco de dados de forma eficiente."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tasks")
        existing_ids = set(row[0] for row in cursor.fetchall())
        current_ids = set(tasks.keys())
        ids_to_delete = existing_ids - current_ids
        if ids_to_delete:
            cursor.executemany("DELETE FROM tasks WHERE id = ?", [(task_id,) for task_id in ids_to_delete])
        for task_id, task in tasks.items():
            name = task.get("name")
            completed = int(task.get("completed", False))
            creation_date = task.get("creation_date")
            completion_date = task.get("completion_date")
            if task_id in existing_ids:
                cursor.execute(
                    "UPDATE tasks SET name = ?, completed = ?, creation_date = ?, completion_date = ? WHERE id = ?",
                    (name, completed, creation_date, completion_date, task_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO tasks (name, completed, creation_date, completion_date) VALUES (?, ?, ?, ?)",
                    (name, completed, creation_date, completion_date)
                )
                new_id = cursor.lastrowid
                tasks[new_id] = task
        conn.commit()

def load_reminders():
    """Carrega todos os lembretes do banco de dados."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, message FROM reminders")
        rows = cursor.fetchall()
        reminders = {}
        for reminder_id, date, message in rows:
            reminders[reminder_id] = {
                "date": date,
                "message": message
            }
        return reminders

def save_reminders(reminders):
    """Salva todos os lembretes no banco de dados de forma eficiente."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reminders")
        existing_ids = set(row[0] for row in cursor.fetchall())
        current_ids = set(reminders.keys())
        ids_to_delete = existing_ids - current_ids
        if ids_to_delete:
            cursor.executemany("DELETE FROM reminders WHERE id = ?", [(reminder_id,) for reminder_id in ids_to_delete])
        for reminder_id, reminder in reminders.items():
            date = reminder.get("date")
            message = reminder.get("message")
            if reminder_id in existing_ids:
                cursor.execute(
                    "UPDATE reminders SET date = ?, message = ? WHERE id = ?",
                    (date, message, reminder_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO reminders (date, message) VALUES (?, ?)",
                    (date, message)
                )
                new_id = cursor.lastrowid
                reminders[new_id] = reminder
        conn.commit()

def load_notes():
    """Carrega todas as notas do banco de dados."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Seleciona também a coluna custom_css
        cursor.execute("SELECT id, date, text, raw_text, categories, tags, is_markdown, custom_css FROM notes")
        rows = cursor.fetchall()
        notes = {}
        for note_id, date, text, raw_text, categories, tags, is_md, custom_css in rows:
            # Se raw_text estiver vazio, usa o conteúdo de text
            if raw_text is None or raw_text.strip() == "":
                raw_text = text
            if date not in notes:
                notes[date] = []
            notes[date].append({
                "id": note_id,
                "text": text,
                "raw_text": raw_text,
                "categories": categories.split(",") if categories else [],
                "tags": tags.split(",") if tags else [],
                "is_markdown": is_md,
                "custom_css": custom_css or ""
            })
        return notes

def save_notes(notes):
    """Salva todas as notas no banco de dados de forma mais eficiente."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM notes")
        existing_ids = set(row[0] for row in cursor.fetchall())
        current_ids = set()
        for date, notes_list in notes.items():
            for note in notes_list:
                note_id = note.get("id")
                if note_id:
                    current_ids.add(note_id)
        ids_to_delete = existing_ids - current_ids
        if ids_to_delete:
            cursor.executemany("DELETE FROM notes WHERE id = ?", [(note_id,) for note_id in ids_to_delete])
        for date, notes_list in notes.items():
            for note in notes_list:
                note_id = note.get("id")
                text = note.get("text", "")
                raw_text = note.get("raw_text", "")
                categories = ",".join(note.get("categories", []))
                tags = ",".join(note.get("tags", []))
                custom_css = note.get("custom_css", "")
                if note_id in existing_ids:
                    cursor.execute(
                        "UPDATE notes SET date = ?, text = ?, raw_text = ?, categories = ?, tags = ?, custom_css = ? WHERE id = ?",
                        (date, text, raw_text, categories, tags, custom_css, note_id)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO notes (date, text, raw_text, categories, tags, custom_css) VALUES (?, ?, ?, ?, ?, ?)",
                        (date, text, raw_text, categories, tags, custom_css)
                    )
        conn.commit()

def add_font_size_column():
    """Adiciona a coluna 'font_size' na tabela 'theme' se ela não existir."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(theme)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'font_size' not in columns:
            cursor.execute("ALTER TABLE theme ADD COLUMN font_size INTEGER DEFAULT 12")
            conn.commit()

def initialize_theme():
    """Inicializa o tema, adiciona a coluna font_size se necessário e carrega o tema."""
    add_font_size_column()
    theme = load_theme()
    return theme

def load_theme():
    """Carrega o tema do banco de dados, incluindo o tamanho da fonte."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM theme")
        rows = cursor.fetchall()
        if not rows:
            return {
                "background": "#ffffff",
                "button": "#cccccc",
                "marked_day": "#ffcccc",
                "text": "#000000",
                "dark_mode": False,
                "font_size": 10
            }
        theme = {key: (int(value) if key == "font_size" else value) for key, value in rows}
        if "font_size" not in theme:
            theme["font_size"] = 12
        return theme

def save_theme(theme):
    """Salva o tema no banco de dados, incluindo o tamanho da fonte."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for key, value in theme.items():
            cursor.execute('''
                INSERT OR REPLACE INTO theme (key, value) VALUES (?, ?)
            ''', (key, str(value)))
        conn.commit()

def load_kanban_columns():
    """Carrega as colunas do Kanban do banco de dados."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM kanban_columns")
        rows = cursor.fetchall()
        columns = {}
        for column_id, name in rows:
            columns[column_id] = {
                "name": name,
                "tasks": load_tasks_for_column(column_id)
            }
        return columns

def load_tasks_for_column(column_id):
    """Carrega as tarefas para uma coluna específica."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, description, priority, due_date FROM kanban_tasks WHERE column_id = ?", (column_id,))
        rows = cursor.fetchall()
        tasks = []
        for task_id, description, priority, due_date in rows:
            tasks.append({
                "id": task_id,
                "description": description,
                "priority": priority,
                "due_date": due_date
            })
        return tasks

def save_kanban(columns):
    """Salva as colunas e suas respectivas tarefas no banco de dados."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for column_id, column in columns.items():
            cursor.execute("INSERT OR REPLACE INTO kanban_columns (id, name) VALUES (?, ?)",
                           (column_id, column["name"]))
            for task in column["tasks"]:
                cursor.execute('''
                    INSERT OR REPLACE INTO kanban_tasks (id, description, priority, due_date, column_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (task["id"], task["description"], task["priority"], task["due_date"], column_id))
        conn.commit()

# Inicializa o banco de dados na primeira execução
if not os.path.exists(DB_PATH):
    init_db()
else:
    # Mesmo se o banco já existir, garante que a estrutura esteja atualizada
    init_db()
