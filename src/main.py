from flask import Flask, render_template_string, request, send_file, redirect, url_for, flash, jsonify
import pandas as pd
from datetime import datetime
from config.db_connection import get_db_connection
import logging
import sys
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sql_export.log'),
        logging.StreamHandler(sys.stdout)
    ])

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'a_very_secret_key_for_dev') 

DEFAULT_SQL_QUERY = """"""

HTML_FORM = """<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Exportar Consulta SQL</title>
    <style>
        :root {
            --primary-color: rgb(28, 156, 81);
            --secondary-color: rgb(255, 118, 58);
            --text-on-dark: #ffffff;
            --text-on-light: #333333;
            --background-light: #f9f9f9;
            --border-color: #cccccc;
            --error-color: #dc3545;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--background-light);
            color: var(--text-on-light);
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }

        .container {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            max-width: 900px;
            width: 100%;
            box-sizing: border-box;
        }

        h2 {
            color: var(--primary-color);
            text-align: center;
            margin-bottom: 25px;
            font-size: 2em;
        }

        form {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        label {
            font-weight: bold;
            margin-bottom: 5px;
            color: var(--text-on-light);
        }

        input[type="text"],
        textarea,
        select {
            width: calc(100% - 20px);
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 5px;
            font-size: 1em;
            box-sizing: border-box;
            transition: border-color 0.3s ease;
        }

        input[type="text"]:focus,
        textarea:focus,
        select:focus {
            border-color: var(--primary-color);
            outline: none;
            box-shadow: 0 0 0 2px rgba(28, 156, 81, 0.2);
        }

        textarea#sql_query 
            min-height: 250px; 
            font-family: monospace; 
        }

        .input-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px;
        }

        .input-group {
            display: flex;
            flex-direction: column;
        }

        .button-group {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
            align-items: center;
        }

        button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: background-color 0.3s ease, color 0.3s ease;
            white-space: nowrap; 
        }

        button[name="action"][value="run_query"],
        button[name="action"][value="export"] {
            background-color: var(--primary-color);
            color: var(--text-on-dark);
        }

        button[name="action"][value="run_query"]:hover,
        button[name="action"][value="export"]:hover {
            background-color: rgb(22, 120, 65); 
        }

        button[name="action"][value="save_query"] {
            background-color: var(--secondary-color);
            color: var(--text-on-dark);
        }

        button[name="action"][value="save_query"]:hover {
            background-color: rgb(200, 90, 40); 
        }

        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
            color: #666666;
        }

        select#format {
            flex-grow: 1; 
            min-width: 150px;
        }

        ul {
            list-style: none;
            padding: 0;
            margin-bottom: 20px;
        }

        ul li {
            color: var(--error-color);
            background-color: rgba(220, 53, 69, 0.1);
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            border: 1px solid var(--error-color);
        }

        h3 {
            color: var(--primary-color);
            margin-top: 30px;
            margin-bottom: 15px;
            text-align: center;
        }

        .table-container {
            overflow-x: auto;
            max-width: 100%;
            margin-top: 20px;
            border: 1px solid var(--border-color);
            border-radius: 5px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 0;
            background-color: #ffffff;
        }

        table, th, td {
            border: 1px solid var(--border-color);
        }

        th {
            background-color: var(--primary-color);
            color: var(--text-on-dark);
            padding: 12px 8px;
            text-align: left;
            font-weight: bold;
            white-space: nowrap;
        }

        td {
            padding: 10px 8px;
            text-align: left;
            white-space: nowrap;
            color: var(--text-on-light);
        }

        tr:nth-child(even) {
            background-color: #f2f2f2;
        }

    
    </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/codemirror.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/theme/eclipse.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/addon/hint/show-hint.min.css">
</head>
<body>
    <div class="container">
        <h2>Exportar Consulta SQL</h2>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <ul>
                {% for message in messages %}
                    <li>{{ message }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}
        <form method="post">
            <label for="sql_query">SQL Query:</label>
            <textarea name="sql_query" id="sql_query" rows="15">{{ sql_query or default_sql_query }}</textarea>

            <div class="input-grid">
                <div class="input-group">
                    <label for="filename_base">Nome do arquivo (sem extensão):</label>
                    <input type="text" name="filename_base" id="filename_base" value="{{ filename_base or '_' + now }}">
                </div>
                <div class="input-group">
                    <label for="sheet_name">Nome da planilha/sheet:</label>
                    <input type="text" name="sheet_name" id="sheet_name" value="{{ sheet_name or '' }}">
                </div>
                <div class="input-group">
                    <label for="worksheet">Nome da worksheet:</label>
                    <input type="text" name="worksheet" id="worksheet" value="{{ worksheet or '' }}">
                </div>
                <div class="input-group">
                    <label for="query_name">Nome para salvar a query:</label>
                    <input type="text" name="query_name" id="query_name" value="{{ query_name or '' }}">
                </div>
            </div>
            
            <div class="button-group">
                <button type="submit" name="action" value="run_query">Executar Query</button>
                <button type="submit" name="action" value="export">Exportar</button>
                <button type="submit" name="action" value="save_query">Salvar Query</button>
                <label for="format" style="margin-left: auto; margin-bottom: 0;">Escolha o formato:</label>
                <select name="format" id="format">
                    <option value="excel">Excel (.xlsx)</option>
                    <option value="pdf">PDF</option>
                    <option value="csv">CSV (.xls)</option>
                    <option value="powerbi">Power BI (CSV)</option>
                </select>
            </div>
        </form>
        {% if table_html %}
            <h3>Resultado da Query:</h3>
            <div class="table-container">
                {{ table_html|safe }}
            </div>
        {% endif %}
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/mode/sql/sql.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/addon/hint/show-hint.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/addon/hint/sql-hint.min.js"></script>
    <script>
    var editor = CodeMirror.fromTextArea(document.getElementById("sql_query"), {
        mode: "text/x-sql",
        theme: "eclipse",
        lineNumbers: true,
        extraKeys: {"Ctrl-Space": "autocomplete"},
        hintOptions: {
            tables: {}
        }
    });
    fetch("/autocomplete_metadata")
    .then(response => response.json())
    .then(data => {
        if (data.tables) {
            editor.options.hintOptions.tables = data.tables;
        }
    });
    
    editor.on("inputRead", function(cm, change) {
        if (change.text[0] === "." || change.text[0] === " ") {
            cm.showHint({completeSingle: false});
        }
    });
    </script>
</body>
</html>"""

QUERIES_DIR = os.path.join(os.path.dirname(__file__), '..', 'queries_salvas')
os.makedirs(QUERIES_DIR, exist_ok=True)

# Funções
def run_query(query):
    conn = None
    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        logging.error(f"Erro ao executar a consulta: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def df_to_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    font_size = 7 
    c.setFont("Helvetica", font_size)
    col_width = 55 
    row_height = 12 
    x_start = 30
    y = height - 30
    
    x = x_start
    for col in df.columns:
        c.drawString(x, y, str(col))
        x += col_width
    y -= row_height
    for idx, row in df.iterrows():
        x = x_start
        for item in row:
            c.drawString(x, y, str(item))
            x += col_width
        y -= row_height
        if y < 30: 
            c.showPage()
            c.setFont("Helvetica", font_size)
            y = height - 30
          
            x = x_start
            for col in df.columns:
                c.drawString(x, y, str(col))
                x += col_width
            y -= row_height
    c.save()
    buffer.seek(0)
    return buffer

@app.route('/autocomplete_metadata')
def autocomplete_metadata():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TABLE_NAME, COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
        """)
        data = cursor.fetchall()
        from collections import defaultdict
        tables_dict = defaultdict(list)
        for table, column in data:
            tables_dict[table].append(column)
        return jsonify({"tables": tables_dict})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    sql_query = DEFAULT_SQL_QUERY
    now = datetime.now().strftime('%d%m%Y')
    filename_base = f"_{now}"
    sheet_name = ""
    worksheet_name = ""
    query_name = ""
    table_html = None

    if request.method == 'POST':
        sql_query = request.form.get('sql_query') or DEFAULT_SQL_QUERY
        export_format = request.form.get('format')
        filename_base = request.form.get('filename_base') or filename_base
        sheet_name = request.form.get('sheet_name') or sheet_name
        worksheet_name = request.form.get('worksheet') or worksheet_name
        query_name = request.form.get('query_name') or ""
        action = request.form.get('action')

        if action == "save_query":
            if not query_name.strip():
                flash("Informe um nome para salvar a query.")
            else:
                safe_name = "".join(c for c in query_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                filepath = os.path.join(QUERIES_DIR, f"{safe_name}.sql")
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(sql_query)
                    flash(f"Query salva em: {filepath}")
                except Exception as e:
                    flash(f"Erro ao salvar a query: {str(e)}")
            return redirect(url_for('index'))

        if action == "run_query":
            df = run_query(sql_query)
            if df is None or df.empty:
                flash("Erro ao executar a consulta ou nenhum dado retornado.")
            else:
                table_html = df.head(100).to_html(index=False, classes="table table-bordered", border=1)
            return render_template_string(
                HTML_FORM,
                sql_query=sql_query,
                default_sql_query=DEFAULT_SQL_QUERY,
                filename_base=filename_base,
                sheet_name=sheet_name,
                worksheet=worksheet_name,
                now=now,
                query_name=query_name,
                table_html=table_html
            )
        

        df = run_query(sql_query)
        if df is None or df.empty:
            flash("Erro ao executar a consulta ou nenhum dado retornado.")
            return redirect(url_for('index'))
        
        table_html = df.head(100).to_html(index=False, classes="table table-bordered", border=1) 

        if export_format == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=sheet_name)
          
                worksheet = writer.sheets[sheet_name] 
                for column in worksheet.columns:
                    max_length = 0
                    column_name = column[0].column_letter 
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50) 
                    worksheet.column_dimensions[column_name].width = adjusted_width
            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"{filename_base}.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        elif export_format == 'pdf':
            pdf_buffer = df_to_pdf(df)
            return send_file(pdf_buffer, as_attachment=True, download_name=f"{filename_base}.pdf", mimetype='application/pdf')
        elif export_format == 'csv' or export_format == 'powerbi':
            output = io.StringIO()
            df.to_csv(output, index=False, sep=';' if export_format == 'csv' else ',')
            output.seek(0)
            ext = 'xls' if export_format == 'csv' else 'csv'
            mimetype = 'application/vnd.ms-excel' if export_format == 'csv' else 'text/csv'
            return send_file(io.BytesIO(output.getvalue().encode('utf-8')), as_attachment=True, download_name=f"{filename_base}.{ext}", mimetype=mimetype)
        else:
            flash("Formato inválido.")
            return redirect(url_for('index'))

    return render_template_string(
        HTML_FORM,
        sql_query=sql_query,
        default_sql_query=DEFAULT_SQL_QUERY,
        filename_base=filename_base,
        sheet_name=sheet_name,
        worksheet=worksheet_name,
        now=now,
        query_name=query_name,
        table_html=table_html
    )

if __name__ == "__main__":
    app.run(debug=True)