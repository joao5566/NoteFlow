# export_module.py

import json
import sqlite3
from PyQt5.QtWidgets import (
    QMessageBox, QFileDialog, QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton,
    QHBoxLayout, QFormLayout, QDateEdit
)
from PyQt5.QtCore import QDate
from fpdf import FPDF
from datetime import datetime
from bs4 import BeautifulSoup  # Biblioteca para remover tags HTML

DB_PATH = "data.db"

def export_notes(window, _=None):
    """Exporta todas as notas do banco de dados para um arquivo JSON."""
    path, _ = QFileDialog.getSaveFileName(
        window,
        "Exportar Notas",
        "notas.json",
        "Arquivos JSON (*.json)"
    )
    if not path:
        return

    notes = load_all_notes()
    # Converter os IDs para strings para garantir compatibilidade JSON
    notes_with_ids = {str(note_id): note for note_id, note in notes.items()}
    try:
        with open(path, "w", encoding='utf-8') as file:
            json.dump(notes_with_ids, file, indent=4, ensure_ascii=False)
        QMessageBox.information(window, "Exportação Concluída", f"Notas exportadas como JSON em {path}")
    except Exception as e:
        QMessageBox.critical(window, "Erro na Exportação", f"Ocorreu um erro ao exportar para JSON: {e}")

def import_notes(window, refresh_calendar):
    """Importa notas de um arquivo JSON e insere no banco de dados."""
    path, _ = QFileDialog.getOpenFileName(
        window,
        "Importar Notas",
        "",
        "Arquivos JSON (*.json)"
    )
    if not path:
        return

    try:
        with open(path, "r", encoding='utf-8') as file:
            imported_notes = json.load(file)
    except Exception as e:
        QMessageBox.critical(window, "Erro na Importação", f"Não foi possível ler o arquivo: {e}")
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for note_id_str, note in imported_notes.items():
                try:
                    note_id = int(note_id_str)
                except ValueError:
                    # Se o ID não for um inteiro válido, ignore esta nota
                    continue

                categories = ",".join(note.get("categories", []))
                tags = ",".join(note.get("tags", []))
                text = note.get("text", "").strip()

                # Inserir ou atualizar a nota com base no ID
                cursor.execute(
                    "INSERT OR REPLACE INTO notes (id, date, text, categories, tags) VALUES (?, ?, ?, ?, ?)",
                    (note_id, note.get("date", ""), text, categories, tags)
                )
            conn.commit()
        refresh_calendar()
        QMessageBox.information(window, "Importação Concluída", f"Notas importadas de {path}")
    except sqlite3.Error as e:
        QMessageBox.critical(window, "Erro de Banco de Dados", f"Ocorreu um erro ao importar as notas: {e}")

def export_to_pdf(window):
    """Abre o diálogo para exportar notas para PDF ou JSON."""
    open_export_interval_dialog(window)

def export_notes_interval(window, start_date, end_date):
    """Exporta notas em um intervalo de datas para um arquivo JSON ou PDF."""
    path, selected_filter = QFileDialog.getSaveFileName(
        window,
        "Exportar Notas",
        "relatorio.pdf",
        "Arquivos PDF (*.pdf);;JSON (*.json)"
    )
    if not path:
        return

    # Determina a extensão com base no filtro selecionado
    if "JSON" in selected_filter:
        extension = "json"
    elif "PDF" in selected_filter:
        extension = "pdf"
    else:
        # Padrão para PDF se nenhum filtro for específico
        if not path.lower().endswith('.pdf') and not path.lower().endswith('.json'):
            path += ".pdf"
            extension = "pdf"
        else:
            extension = path.split(".")[-1].lower()

    notes = load_notes_interval(start_date, end_date)

    if extension == "json":
        # Converter os IDs para strings para garantir compatibilidade JSON
        notes_with_ids = {str(note_id): note for note_id, note in notes.items()}
        try:
            with open(path, "w", encoding='utf-8') as file:
                json.dump(notes_with_ids, file, indent=4, ensure_ascii=False)
            QMessageBox.information(window, "Exportação Concluída", f"Notas exportadas como JSON em {path}")
        except Exception as e:
            QMessageBox.critical(window, "Erro na Exportação", f"Ocorreu um erro ao exportar para JSON: {e}")
    elif extension == "pdf":
        export_to_pdf_with_path(window, notes, path)

def load_notes_interval(start_date, end_date):
    """Carrega notas de um intervalo de datas do banco de dados."""
    return load_notes_from_db("WHERE date BETWEEN ? AND ?", (start_date, end_date))

def load_all_notes():
    """Carrega todas as notas do banco de dados."""
    return load_notes_from_db()

def load_notes_from_db(condition="", params=()):
    """Função genérica para carregar notas do banco de dados com uma condição opcional."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        query = "SELECT id, date, text, categories, tags FROM notes " + condition
        cursor.execute(query, params)
        rows = cursor.fetchall()
        notes = {}
        for note_id, date, text, categories, tags in rows:
            notes[note_id] = {
                "date": date,
                "text": text,
                "categories": categories.split(",") if categories else [],
                "tags": tags.split(",") if tags else []
            }
        return notes

def export_to_pdf_with_path(window, notes, path):
    """Exporta notas para um arquivo PDF sem incluir tags HTML."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Notas", ln=True, align='C')
    pdf.ln(10)

    for note_id, note in notes.items():
        date = note.get('date', 'Sem data')
        text = note.get('text', '').strip()
        categories = ', '.join(note.get('categories', [])) or 'Sem categoria'
        tags = ', '.join(note.get('tags', [])) or 'Sem tags'

        # Remover tags HTML do texto
        clean_text = BeautifulSoup(text, 'html.parser').get_text()

        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, txt=f"ID: {note_id}", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=f"Data: {date}", ln=True)
        pdf.cell(0, 10, txt=f"Categorias: {categories}", ln=True)
        pdf.cell(0, 10, txt=f"Tags: {tags}", ln=True)

        pdf.set_font("Arial", size=12)
        # Adicionar o texto sem HTML
        for line in clean_text.split('\n'):
            pdf.multi_cell(0, 10, txt=line, align='L')
        pdf.ln(5)

    try:
        pdf.output(path)
        QMessageBox.information(window, "Exportação Concluída", f"Notas exportadas como PDF em {path}")
    except Exception as e:
        QMessageBox.critical(window, "Erro na Exportação", f"Ocorreu um erro ao exportar para PDF: {e}")

def show_about(window):
    QMessageBox.information(
        window,
        "Ajuda - Calendário Interativo com Notas",
        "Instruções de Uso:\n\n"
        "1. **Adicionar/Editar Notas**:\n"
        "   - Clique em um dia no calendário para abrir o editor de notas.\n"
        "   - Digite o texto da nota e adicione categorias e tags, se desejar.\n"
        "   - Clique em 'Salvar' para gravar a nota.\n\n"
        "2. **Definir Lembretes**:\n"
        "   - Clique no botão 'Definir Lembrete' para criar um novo lembrete.\n"
        "   - Insira a data e a mensagem do lembrete.\n"
        "   - Clique em 'Salvar' para adicionar o lembrete.\n\n"
        "3. **Gerenciar Tarefas**:\n"
        "   - Acesse o gerenciador de tarefas no menu 'Arquivo' > 'Gerenciar Tarefas'.\n"
        "   - Adicione, edite ou apague tarefas conforme necessário.\n\n"
        "4. **Personalizar Tema**:\n"
        "   - Vá em 'Arquivo' > 'Personalizar Tema' para alterar as cores do aplicativo.\n"
        "   - Escolha um esquema predefinido ou defina as cores manualmente.\n\n"
        "5. **Exportar e Importar Notas**:\n"
        "   - Exportar: Salve suas notas em um arquivo JSON ou PDF pelo menu 'Arquivo'.\n"
        "   - Importar: Carregue notas de um arquivo JSON existente.\n\n"
        "Atalhos de Teclado:\n"
        "- **Ctrl+S**: Salvar Nota\n"
        "- **Ctrl+Z**: Desfazer\n"
        "- **Ctrl+Y**: Refazer\n"
        "- **Ctrl+E**: Exportar Nota\n\n"
        "Exemplo de Uso:\n"
        "1. Selecione uma data no calendário.\n"
        "2. Digite a nota e adicione tags como 'trabalho, pessoal'.\n"
        "3. Clique em 'Salvar'.\n"
        "4. Veja a nota marcada no calendário e exporte-a, se necessário.\n\n"
        "Desenvolvido com PyQt5 e matplotlib."
    )

def open_export_interval_dialog(window):
    """Abre o diálogo para selecionar intervalo de datas e exportar notas."""
    dialog = DateRangeDialog(window)
    if dialog.exec_() == QDialog.Accepted:
        start_date, end_date = dialog.get_dates()
        if validate_date_format(start_date) and validate_date_format(end_date):
            if start_date > end_date:
                QMessageBox.warning(
                    window,
                    "Intervalo Inválido",
                    "A data inicial não pode ser posterior à data final."
                )
                return
            export_notes_interval(window, start_date, end_date)
        else:
            QMessageBox.warning(
                window,
                "Formato de Data Inválido",
                "Por favor, insira datas válidas no formato yyyy-MM-dd."
            )

def validate_date_format(date_str):
    """Valida o formato da data."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

class DateRangeDialog(QDialog):
    """Diálogo para selecionar um intervalo de datas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Intervalo de Datas")
        self.layout = QVBoxLayout(self)

        # Widget de seleção de data inicial
        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(QLabel("Data Inicial:", self))
        self.layout.addWidget(self.start_date_edit)

        # Widget de seleção de data final
        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(QLabel("Data Final:", self))
        self.layout.addWidget(self.end_date_edit)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        self.export_button = QPushButton("Exportar", self)
        self.export_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.export_button)

        self.cancel_button = QPushButton("Cancelar", self)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.layout.addLayout(buttons_layout)

    def get_dates(self):
        """Retorna as datas selecionadas."""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        return start_date, end_date

class EditNoteDialog(QDialog):
    """Diálogo para adicionar ou editar uma nota."""

    def __init__(self, date="", text="", categories=None, tags=None, parent=None):
        """
        Inicializa o EditNoteDialog.

        Args:
            date (str, optional): Data da nota no formato 'yyyy-MM-dd'.
            text (str, optional): Texto da nota.
            categories (list, optional): Lista de categorias.
            tags (list, optional): Lista de tags.
            parent (QWidget, optional): Widget pai.
        """
        super().__init__(parent)
        self.setWindowTitle("Adicionar/Editar Nota")
        self.layout = QFormLayout(self)

        # Entrada para data
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        if date:
            self.date_edit.setDate(QDate.fromString(date, "yyyy-MM-dd"))
        else:
            self.date_edit.setDate(QDate.currentDate())
        self.layout.addRow("Data:", self.date_edit)

        # Entrada para texto da nota
        self.text_input = QLineEdit(self)
        self.text_input.setText(text)
        self.layout.addRow("Texto:", self.text_input)

        # Entrada para categorias
        self.categories_input = QLineEdit(self)
        self.categories_input.setText(", ".join(categories) if categories else "")
        self.layout.addRow("Categorias (separadas por vírgula):", self.categories_input)

        # Entrada para tags
        self.tags_input = QLineEdit(self)
        self.tags_input.setText(", ".join(tags) if tags else "")
        self.layout.addRow("Tags (separadas por vírgula):", self.tags_input)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar", self)
        self.save_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancelar", self)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.layout.addRow(buttons_layout)

    def get_data(self):
        """Retorna os dados inseridos pelo usuário."""
        date = self.date_edit.date().toString("yyyy-MM-dd")
        text = self.text_input.text().strip()
        categories = [cat.strip() for cat in self.categories_input.text().split(",")] if self.categories_input.text() else []
        tags = [tag.strip() for tag in self.tags_input.text().split(",")] if self.tags_input.text() else []
        return date, text, categories, tags

def add_note_dialog(window, refresh_calendar):
    """Abre o diálogo para adicionar uma nova nota."""
    dialog = EditNoteDialog(parent=window)
    if dialog.exec_() == QDialog.Accepted:
        date, text, categories, tags = dialog.get_data()
        if not validate_note_data(date, text):
            return
        # Inserir no banco de dados
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO notes (date, text, categories, tags) VALUES (?, ?, ?, ?)",
                    (date, text, ",".join(categories), ",".join(tags))
                )
                conn.commit()
                new_id = cursor.lastrowid
        except sqlite3.Error as e:
            QMessageBox.critical(window, "Erro de Banco de Dados", f"Ocorreu um erro ao adicionar a nota: {e}")
            return
        QMessageBox.information(window, "Nota Adicionada", "A nota foi adicionada com sucesso.")
        refresh_calendar()

def edit_note_dialog(window, note_id, refresh_calendar):
    """Abre o diálogo para editar uma nota existente."""
    note = load_single_note(note_id)
    if not note:
        QMessageBox.warning(window, "Erro", "Nota não encontrada.")
        return

    dialog = EditNoteDialog(
        date=note['date'],
        text=note['text'],
        categories=note['categories'],
        tags=note['tags'],
        parent=window
    )
    if dialog.exec_() == QDialog.Accepted:
        date, text, categories, tags = dialog.get_data()
        if not validate_note_data(date, text):
            return
        # Atualizar no banco de dados
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE notes SET date = ?, text = ?, categories = ?, tags = ? WHERE id = ?",
                    (date, text, ",".join(categories), ",".join(tags), note_id)
                )
                conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(window, "Erro de Banco de Dados", f"Ocorreu um erro ao atualizar a nota: {e}")
            return
        QMessageBox.information(window, "Nota Atualizada", "A nota foi atualizada com sucesso.")
        refresh_calendar()

def delete_note_dialog(window, note_id, refresh_calendar):
    """Exclui uma nota selecionada."""
    note = load_single_note(note_id)
    if not note:
        QMessageBox.warning(window, "Erro", "Nota não encontrada.")
        return

    reply = QMessageBox.question(
        window, "Confirmação",
        f"Tem certeza de que deseja excluir a nota de {note['date']}?",
        QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(window, "Erro de Banco de Dados", f"Ocorreu um erro ao excluir a nota: {e}")
            return
        QMessageBox.information(window, "Nota Excluída", "A nota foi excluída com sucesso.")
        refresh_calendar()

def validate_note_data(date_str, text):
    """Valida os dados da nota."""
    if not date_str or not text:
        QMessageBox.warning(None, "Dados Inválidos", "Data e texto da nota não podem estar vazios.")
        return False
    if not validate_date_format(date_str):
        QMessageBox.warning(None, "Formato de Data Inválido", "Por favor, insira uma data válida no formato yyyy-MM-dd.")
        return False
    return True

def load_single_note(note_id):
    """Carrega uma única nota do banco de dados."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date, text, categories, tags FROM notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()
        if row:
            date, text, categories, tags = row
            return {
                "date": date,
                "text": text,
                "categories": categories.split(",") if categories else [],
                "tags": tags.split(",") if tags else []
            }
        return None

def export_to_pdf_with_path(window, notes, path):
    """Exporta notas para um arquivo PDF sem incluir tags HTML."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Notas", ln=True, align='C')
    pdf.ln(10)

    for note_id, note in notes.items():
        date = note.get('date', 'Sem data')
        text = note.get('text', '').strip()
        categories = ', '.join(note.get('categories', [])) or 'Sem categoria'
        tags = ', '.join(note.get('tags', [])) or 'Sem tags'

        # Remover tags HTML do texto
        clean_text = BeautifulSoup(text, 'html.parser').get_text()

        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, txt=f"ID: {note_id}", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=f"Data: {date}", ln=True)
        pdf.cell(0, 10, txt=f"Categorias: {categories}", ln=True)
        pdf.cell(0, 10, txt=f"Tags: {tags}", ln=True)

        pdf.set_font("Arial", size=12)
        # Adicionar o texto sem HTML
        for line in clean_text.split('\n'):
            pdf.multi_cell(0, 10, txt=line, align='L')
        pdf.ln(5)

    try:
        pdf.output(path)
        QMessageBox.information(window, "Exportação Concluída", f"Notas exportadas como PDF em {path}")
    except Exception as e:
        QMessageBox.critical(window, "Erro na Exportação", f"Ocorreu um erro ao exportar para PDF: {e}")

def show_about(window):
    QMessageBox.information(
        window,
        "Ajuda - Calendário Interativo com Notas",
        "Instruções de Uso:\n\n"
        "1. **Adicionar/Editar Notas**:\n"
        "   - Clique em um dia no calendário para abrir o editor de notas.\n"
        "   - Digite o texto da nota e adicione categorias e tags, se desejar.\n"
        "   - Clique em 'Salvar' para gravar a nota.\n\n"
        "2. **Definir Lembretes**:\n"
        "   - Clique no botão 'Definir Lembrete' para criar um novo lembrete.\n"
        "   - Insira a data e a mensagem do lembrete.\n"
        "   - Clique em 'Salvar' para adicionar o lembrete.\n\n"
        "3. **Gerenciar Tarefas**:\n"
        "   - Acesse o gerenciador de tarefas no menu 'Arquivo' > 'Gerenciar Tarefas'.\n"
        "   - Adicione, edite ou apague tarefas conforme necessário.\n\n"
        "4. **Personalizar Tema**:\n"
        "   - Vá em 'Arquivo' > 'Personalizar Tema' para alterar as cores do aplicativo.\n"
        "   - Escolha um esquema predefinido ou defina as cores manualmente.\n\n"
        "5. **Exportar e Importar Notas**:\n"
        "   - Exportar: Salve suas notas em um arquivo JSON ou PDF pelo menu 'Arquivo'.\n"
        "   - Importar: Carregue notas de um arquivo JSON existente.\n\n"
        "Atalhos de Teclado:\n"
        "- **Ctrl+S**: Salvar Nota\n"
        "- **Ctrl+Z**: Desfazer\n"
        "- **Ctrl+Y**: Refazer\n"
        "- **Ctrl+E**: Exportar Nota\n\n"
        "Exemplo de Uso:\n"
        "1. Selecione uma data no calendário.\n"
        "2. Digite a nota e adicione tags como 'trabalho, pessoal'.\n"
        "3. Clique em 'Salvar'.\n"
        "4. Veja a nota marcada no calendário e exporte-a, se necessário.\n\n"
        "Desenvolvido com PyQt5 e matplotlib."
    )

class DateRangeDialog(QDialog):
    """Diálogo para selecionar um intervalo de datas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Intervalo de Datas")
        self.layout = QVBoxLayout(self)

        # Widget de seleção de data inicial
        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(QLabel("Data Inicial:", self))
        self.layout.addWidget(self.start_date_edit)

        # Widget de seleção de data final
        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(QLabel("Data Final:", self))
        self.layout.addWidget(self.end_date_edit)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        self.export_button = QPushButton("Exportar", self)
        self.export_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.export_button)

        self.cancel_button = QPushButton("Cancelar", self)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.layout.addLayout(buttons_layout)

    def get_dates(self):
        """Retorna as datas selecionadas."""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        return start_date, end_date

class EditNoteDialog(QDialog):
    """Diálogo para adicionar ou editar uma nota."""

    def __init__(self, date="", text="", categories=None, tags=None, parent=None):
        """
        Inicializa o EditNoteDialog.

        Args:
            date (str, optional): Data da nota no formato 'yyyy-MM-dd'.
            text (str, optional): Texto da nota.
            categories (list, optional): Lista de categorias.
            tags (list, optional): Lista de tags.
            parent (QWidget, optional): Widget pai.
        """
        super().__init__(parent)
        self.setWindowTitle("Adicionar/Editar Nota")
        self.layout = QFormLayout(self)

        # Entrada para data
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        if date:
            self.date_edit.setDate(QDate.fromString(date, "yyyy-MM-dd"))
        else:
            self.date_edit.setDate(QDate.currentDate())
        self.layout.addRow("Data:", self.date_edit)

        # Entrada para texto da nota
        self.text_input = QLineEdit(self)
        self.text_input.setText(text)
        self.layout.addRow("Texto:", self.text_input)

        # Entrada para categorias
        self.categories_input = QLineEdit(self)
        self.categories_input.setText(", ".join(categories) if categories else "")
        self.layout.addRow("Categorias (separadas por vírgula):", self.categories_input)

        # Entrada para tags
        self.tags_input = QLineEdit(self)
        self.tags_input.setText(", ".join(tags) if tags else "")
        self.layout.addRow("Tags (separadas por vírgula):", self.tags_input)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar", self)
        self.save_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancelar", self)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.layout.addRow(buttons_layout)

    def get_data(self):
        """Retorna os dados inseridos pelo usuário."""
        date = self.date_edit.date().toString("yyyy-MM-dd")
        text = self.text_input.text().strip()
        categories = [cat.strip() for cat in self.categories_input.text().split(",")] if self.categories_input.text() else []
        tags = [tag.strip() for tag in self.tags_input.text().split(",")] if self.tags_input.text() else []
        return date, text, categories, tags

def add_note_dialog(window, refresh_calendar):
    """Abre o diálogo para adicionar uma nova nota."""
    dialog = EditNoteDialog(parent=window)
    if dialog.exec_() == QDialog.Accepted:
        date, text, categories, tags = dialog.get_data()
        if not validate_note_data(date, text):
            return
        # Inserir no banco de dados
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO notes (date, text, categories, tags) VALUES (?, ?, ?, ?)",
                    (date, text, ",".join(categories), ",".join(tags))
                )
                conn.commit()
                new_id = cursor.lastrowid
        except sqlite3.Error as e:
            QMessageBox.critical(window, "Erro de Banco de Dados", f"Ocorreu um erro ao adicionar a nota: {e}")
            return
        QMessageBox.information(window, "Nota Adicionada", "A nota foi adicionada com sucesso.")
        refresh_calendar()

def edit_note_dialog(window, note_id, refresh_calendar):
    """Abre o diálogo para editar uma nota existente."""
    note = load_single_note(note_id)
    if not note:
        QMessageBox.warning(window, "Erro", "Nota não encontrada.")
        return

    dialog = EditNoteDialog(
        date=note['date'],
        text=note['text'],
        categories=note['categories'],
        tags=note['tags'],
        parent=window
    )
    if dialog.exec_() == QDialog.Accepted:
        date, text, categories, tags = dialog.get_data()
        if not validate_note_data(date, text):
            return
        # Atualizar no banco de dados
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE notes SET date = ?, text = ?, categories = ?, tags = ? WHERE id = ?",
                    (date, text, ",".join(categories), ",".join(tags), note_id)
                )
                conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(window, "Erro de Banco de Dados", f"Ocorreu um erro ao atualizar a nota: {e}")
            return
        QMessageBox.information(window, "Nota Atualizada", "A nota foi atualizada com sucesso.")
        refresh_calendar()

def delete_note_dialog(window, note_id, refresh_calendar):
    """Exclui uma nota selecionada."""
    note = load_single_note(note_id)
    if not note:
        QMessageBox.warning(window, "Erro", "Nota não encontrada.")
        return

    reply = QMessageBox.question(
        window, "Confirmação",
        f"Tem certeza de que deseja excluir a nota de {note['date']}?",
        QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(window, "Erro de Banco de Dados", f"Ocorreu um erro ao excluir a nota: {e}")
            return
        QMessageBox.information(window, "Nota Excluída", "A nota foi excluída com sucesso.")
        refresh_calendar()

def validate_note_data(date_str, text):
    """Valida os dados da nota."""
    if not date_str or not text:
        QMessageBox.warning(None, "Dados Inválidos", "Data e texto da nota não podem estar vazios.")
        return False
    if not validate_date_format(date_str):
        QMessageBox.warning(None, "Formato de Data Inválido", "Por favor, insira uma data válida no formato yyyy-MM-dd.")
        return False
    return True

def load_single_note(note_id):
    """Carrega uma única nota do banco de dados."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date, text, categories, tags FROM notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()
        if row:
            date, text, categories, tags = row
            return {
                "date": date,
                "text": text,
                "categories": categories.split(",") if categories else [],
                "tags": tags.split(",") if tags else []
            }
        return None

def export_to_pdf_with_path(window, notes, path):
    """Exporta notas para um arquivo PDF sem incluir tags HTML."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Notas", ln=True, align='C')
    pdf.ln(10)

    for note_id, note in notes.items():
        date = note.get('date', 'Sem data')
        text = note.get('text', '').strip()
        categories = ', '.join(note.get('categories', [])) or 'Sem categoria'
        tags = ', '.join(note.get('tags', [])) or 'Sem tags'

        # Remover tags HTML do texto
        clean_text = BeautifulSoup(text, 'html.parser').get_text()

        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, txt=f"ID: {note_id}", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=f"Data: {date}", ln=True)
        pdf.cell(0, 10, txt=f"Categorias: {categories}", ln=True)
        pdf.cell(0, 10, txt=f"Tags: {tags}", ln=True)

        pdf.set_font("Arial", size=12)
        # Adicionar o texto sem HTML
        for line in clean_text.split('\n'):
            pdf.multi_cell(0, 10, txt=line, align='L')
        pdf.ln(5)

    try:
        pdf.output(path)
        QMessageBox.information(window, "Exportação Concluída", f"Notas exportadas como PDF em {path}")
    except Exception as e:
        QMessageBox.critical(window, "Erro na Exportação", f"Ocorreu um erro ao exportar para PDF: {e}")

def show_about(window):
    QMessageBox.information(
        window,
        "Ajuda - Calendário Interativo com Notas",
        "Instruções de Uso:\n\n"
        "1. **Adicionar/Editar Notas**:\n"
        "   - Clique em um dia no calendário para abrir o editor de notas.\n"
        "   - Digite o texto da nota e adicione categorias e tags, se desejar.\n"
        "   - Clique em 'Salvar' para gravar a nota.\n\n"
        "2. **Definir Lembretes**:\n"
        "   - Clique no botão 'Definir Lembrete' para criar um novo lembrete.\n"
        "   - Insira a data e a mensagem do lembrete.\n"
        "   - Clique em 'Salvar' para adicionar o lembrete.\n\n"
        "3. **Gerenciar Tarefas**:\n"
        "   - Acesse o gerenciador de tarefas no menu 'Arquivo' > 'Gerenciar Tarefas'.\n"
        "   - Adicione, edite ou apague tarefas conforme necessário.\n\n"
        "4. **Personalizar Tema**:\n"
        "   - Vá em 'Arquivo' > 'Personalizar Tema' para alterar as cores do aplicativo.\n"
        "   - Escolha um esquema predefinido ou defina as cores manualmente.\n\n"
        "5. **Exportar e Importar Notas**:\n"
        "   - Exportar: Salve suas notas em um arquivo JSON ou PDF pelo menu 'Arquivo'.\n"
        "   - Importar: Carregue notas de um arquivo JSON existente.\n\n"
        "Atalhos de Teclado:\n"
        "- **Ctrl+S**: Salvar Nota\n"
        "- **Ctrl+Z**: Desfazer\n"
        "- **Ctrl+Y**: Refazer\n"
        "- **Ctrl+E**: Exportar Nota\n\n"
        "Exemplo de Uso:\n"
        "1. Selecione uma data no calendário.\n"
        "2. Digite a nota e adicione tags como 'trabalho, pessoal'.\n"
        "3. Clique em 'Salvar'.\n"
        "4. Veja a nota marcada no calendário e exporte-a, se necessário.\n\n"
        "Desenvolvido com PyQt5 e matplotlib."
    )

def open_export_interval_dialog(window):
    """Abre o diálogo para selecionar intervalo de datas e exportar notas."""
    dialog = DateRangeDialog(window)
    if dialog.exec_() == QDialog.Accepted:
        start_date, end_date = dialog.get_dates()
        if validate_date_format(start_date) and validate_date_format(end_date):
            if start_date > end_date:
                QMessageBox.warning(
                    window,
                    "Intervalo Inválido",
                    "A data inicial não pode ser posterior à data final."
                )
                return
            export_notes_interval(window, start_date, end_date)
        else:
            QMessageBox.warning(
                window,
                "Formato de Data Inválido",
                "Por favor, insira datas válidas no formato yyyy-MM-dd."
            )

class DateRangeDialog(QDialog):
    """Diálogo para selecionar um intervalo de datas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Intervalo de Datas")
        self.layout = QVBoxLayout(self)

        # Widget de seleção de data inicial
        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(QLabel("Data Inicial:", self))
        self.layout.addWidget(self.start_date_edit)

        # Widget de seleção de data final
        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(QLabel("Data Final:", self))
        self.layout.addWidget(self.end_date_edit)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        self.export_button = QPushButton("Exportar", self)
        self.export_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.export_button)

        self.cancel_button = QPushButton("Cancelar", self)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.layout.addLayout(buttons_layout)

    def get_dates(self):
        """Retorna as datas selecionadas."""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        return start_date, end_date

class EditNoteDialog(QDialog):
    """Diálogo para adicionar ou editar uma nota."""

    def __init__(self, date="", text="", categories=None, tags=None, parent=None):
        """
        Inicializa o EditNoteDialog.

        Args:
            date (str, optional): Data da nota no formato 'yyyy-MM-dd'.
            text (str, optional): Texto da nota.
            categories (list, optional): Lista de categorias.
            tags (list, optional): Lista de tags.
            parent (QWidget, optional): Widget pai.
        """
        super().__init__(parent)
        self.setWindowTitle("Adicionar/Editar Nota")
        self.layout = QFormLayout(self)

        # Entrada para data
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        if date:
            self.date_edit.setDate(QDate.fromString(date, "yyyy-MM-dd"))
        else:
            self.date_edit.setDate(QDate.currentDate())
        self.layout.addRow("Data:", self.date_edit)

        # Entrada para texto da nota
        self.text_input = QLineEdit(self)
        self.text_input.setText(text)
        self.layout.addRow("Texto:", self.text_input)

        # Entrada para categorias
        self.categories_input = QLineEdit(self)
        self.categories_input.setText(", ".join(categories) if categories else "")
        self.layout.addRow("Categorias (separadas por vírgula):", self.categories_input)

        # Entrada para tags
        self.tags_input = QLineEdit(self)
        self.tags_input.setText(", ".join(tags) if tags else "")
        self.layout.addRow("Tags (separadas por vírgula):", self.tags_input)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar", self)
        self.save_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancelar", self)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.layout.addRow(buttons_layout)

