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
    ]
)

app = Flask(__name__)
app.secret_key = f"SECRET_KEY = os.getenv('SECRET_KEY')"

DEFAULT_SQL_QUERY = """

"""

HTML_FORM = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Exportar Consulta SQL</title>
    <style>
        table, th, td { border: 1px solid #ccc; border-collapse: collapse; padding: 4px; }
        th { background: #eee; }
    </style>
    <!-- CodeMirror CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/codemirror.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/theme/eclipse.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/addon/hint/show-hint.min.css">
</head>
<body>
    <h2>Exportar Consulta SQL</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
        {% for message in messages %}
          <li style="color:red;">{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="post">
        <label for="sql_query">SQL Query:</label><br>
        <textarea name="sql_query" id="sql_query" rows="8" cols="80">{{ sql_query or default_sql_query }}</textarea><br><br>
        <label for="filename_base">Nome do arquivo (sem extensão):</label>
        <input type="text" name="filename_base" id="filename_base" value="{{ filename_base or 'Componente_25140_' + now }}"><br><br>
        <label for="sheet_name">Nome da planilha/sheet:</label>
        <input type="text" name="sheet_name" id="sheet_name" value="{{ sheet_name or 'Componente 25140' }}"><br><br>
        <label for="worksheet">Nome da worksheet:</label>
        <input type="text" name="worksheet" id="worksheet" value="{{ worksheet or 'Componente 25140' }}"><br><br>
        <label for="query_name">Nome para salvar a query:</label>
        <input type="text" name="query_name" id="query_name" value="{{ query_name or '' }}"><br>
        <button type="submit" name="action" value="run_query">Executar Query</button>
        <button type="submit" name="action" value="export">Exportar</button>
        <button type="submit" name="action" value="save_query">Salvar Query</button>
        <label for="format">Escolha o formato:</label>
        <select name="format" id="format">
            <option value="excel">Excel (.xlsx)</option>
            <option value="pdf">PDF</option>
            <option value="csv">CSV (.xls)</option>
            <option value="powerbi">Power BI (CSV)</option>
        </select>
    </form>
    {% if table_html %}
    <h3>Resultado da Query:</h3>
    <div style="overflow-x:auto; max-width:90vw;">
        {{ table_html|safe }}
    </div>
    {% endif %}

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
</html>
"""

QUERIES_DIR = os.path.join(os.path.dirname(__file__), '..', 'queries_salvas')
os.makedirs(QUERIES_DIR, exist_ok=True)

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
    filename_base = f"NomeDoArquivo_{now}"
    sheet_name = "NomeDaPlanilha"
    worksheet_name = "NomeDaWorksheet"
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
                worksheet = writer.sheets[worksheet_name if worksheet_name in writer.sheets else sheet_name]
                for column in worksheet.columns:
                    max_length = max(len(str(cell.value)) for cell in column)
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
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
