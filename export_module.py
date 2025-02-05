# export_module.py

import json
import sqlite3
import os
from datetime import datetime
from bs4 import BeautifulSoup  # Para remover tags HTML
from PyQt5.QtWidgets import (
    QMessageBox, QFileDialog, QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton,
    QHBoxLayout, QFormLayout, QDateEdit
)
from PyQt5.QtCore import QDate
from fpdf import FPDF

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
    # Converter os IDs para strings para compatibilidade com JSON
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
                    continue  # ignora caso o ID não seja um inteiro válido

                # Prepara os campos – se a nota tiver sido salva em modo Markdown,
                # utiliza o valor de raw_text; caso contrário, utiliza text.
                text = note.get("text", "").strip()
                raw_text = note.get("raw_text", text).strip()
                categories = ",".join(note.get("categories", []))
                tags = ",".join(note.get("tags", []))
                is_markdown = note.get("is_markdown", 0)
                custom_css = note.get("custom_css", "")

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO notes 
                    (id, date, text, raw_text, categories, tags, is_markdown, custom_css)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        note_id,
                        note.get("date", ""),
                        text,
                        raw_text,
                        categories,
                        tags,
                        is_markdown,
                        custom_css
                    )
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
        "relatorio",
        "Arquivos PDF (*.pdf);;JSON (*.json)"
    )
    if not path:
        return

    # Define a extensão com base no filtro selecionado
    if "JSON" in selected_filter or path.lower().endswith(".json"):
        extension = "json"
        if not path.lower().endswith(".json"):
            path += ".json"
    else:
        extension = "pdf"
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

    notes = load_notes_interval(start_date, end_date)

    if extension == "json":
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
    """Carrega notas do banco de dados com condição opcional, retornando os campos atualizados."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        query = """
            SELECT id, date, text, raw_text, categories, tags, is_markdown, custom_css 
            FROM notes
        """
        if condition:
            query += " " + condition
        cursor.execute(query, params)
        rows = cursor.fetchall()
        notes = {}
        for row in rows:
            (note_id, date, text, raw_text, categories, tags, is_md, custom_css) = row
            # Se for nota em Markdown, exporta o raw_text; caso contrário, o conteúdo de text
            export_text = raw_text if is_md else text
            notes[note_id] = {
                "date": date,
                "text": export_text,
                "raw_text": raw_text,
                "categories": categories.split(",") if categories else [],
                "tags": tags.split(",") if tags else [],
                "is_markdown": is_md,
                "custom_css": custom_css or ""
            }
        return notes

def export_to_pdf_with_path(window, notes, path):
    """Exporta notas para um arquivo PDF; se a nota estiver em Markdown, mostra o conteúdo original."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Notas", ln=True, align='C')
    pdf.ln(10)

    for note_id, note in notes.items():
        date = note.get('date', 'Sem data')
        # Se a nota for markdown, utiliza o raw_text (para manter a formatação original);
        # caso contrário, utiliza o text já formatado (HTML convertido para texto simples)
        text = note.get('raw_text') if note.get("is_markdown") else note.get('text', '')
        text = text.strip()
        categories = ', '.join(note.get('categories', [])) or 'Sem categoria'
        tags = ', '.join(note.get('tags', [])) or 'Sem tags'

        # Remove qualquer marcação HTML que eventualmente exista
        clean_text = BeautifulSoup(text, 'html.parser').get_text()

        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, txt=f"ID: {note_id}", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=f"Data: {date}", ln=True)
        pdf.cell(0, 10, txt=f"Categorias: {categories}", ln=True)
        pdf.cell(0, 10, txt=f"Tags: {tags}", ln=True)

        pdf.set_font("Arial", size=12)
        for line in clean_text.split('\n'):
            pdf.multi_cell(0, 10, txt=line, align='L')
        pdf.ln(5)

    try:
        pdf.output(path)
        QMessageBox.information(window, "Exportação Concluída", f"Notas exportadas como PDF em {path}")
    except Exception as e:
        QMessageBox.critical(window, "Erro na Exportação", f"Ocorreu um erro ao exportar para PDF: {e}")

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
    """Valida o formato da data (yyyy-MM-dd)."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# --- Diálogos para seleção de intervalo e edição de nota ---
class DateRangeDialog(QDialog):
    """Diálogo para selecionar um intervalo de datas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Intervalo de Datas")
        self.layout = QVBoxLayout(self)

        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(QLabel("Data Inicial:", self))
        self.layout.addWidget(self.start_date_edit)

        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(QLabel("Data Final:", self))
        self.layout.addWidget(self.end_date_edit)

        buttons_layout = QHBoxLayout()
        self.export_button = QPushButton("Exportar", self)
        self.export_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.export_button)

        self.cancel_button = QPushButton("Cancelar", self)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.layout.addLayout(buttons_layout)

    def get_dates(self):
        """Retorna as datas selecionadas no formato yyyy-MM-dd."""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        return start_date, end_date

# (Outras funções/dialogs, como EditNoteDialog, podem permanecer inalteradas)

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


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    # Para teste, abre o diálogo de intervalo e imprime as datas selecionadas
    dialog = DateRangeDialog()
    if dialog.exec_() == QDialog.Accepted:
        start, end = dialog.get_dates()
        print("Intervalo selecionado:", start, "a", end)
    sys.exit(app.exec_())
