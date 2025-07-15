from flask import Flask, render_template_string, request, send_file, redirect, url_for, flash
import pandas as pd
from datetime import datetime
from config.db_connection import get_db_connection
import logging
import sys
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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
        <label for="format">Escolha o formato:</label>
        <select name="format" id="format">
            <option value="excel">Excel (.xlsx)</option>
            <option value="pdf">PDF</option>
            <option value="csv">CSV (.xls)</option>
            <option value="powerbi">Power BI (CSV)</option>
        </select>
        <button type="submit">Exportar</button>
    </form>
</body>
</html>
"""

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

@app.route('/', methods=['GET', 'POST'])
def index():
    sql_query = DEFAULT_SQL_QUERY
    if request.method == 'POST':
        sql_query = request.form.get('sql_query') or DEFAULT_SQL_QUERY
        export_format = request.form.get('format')
        df = run_query(sql_query)
        if df is None or df.empty:
            flash("Erro ao executar a consulta ou nenhum dado retornado.")
            return redirect(url_for('index'))

        filename_base = f"Componente_25140_{datetime.now().strftime('%d%m%Y')}"
        if export_format == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="Componente 25140")
                worksheet = writer.sheets["Componente 25140"]
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
    return render_template_string(HTML_FORM, sql_query=sql_query, default_sql_query=DEFAULT_SQL_QUERY)

if __name__ == "__main__":
    app.run(debug=True)
