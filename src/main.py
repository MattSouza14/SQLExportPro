from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify
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

DEFAULT_SQL_QUERY = ""
QUERIES_DIR = os.path.join(os.path.dirname(__file__), 'queries_salvas')
os.makedirs(QUERIES_DIR, exist_ok=True)


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

    for _, row in df.iterrows():
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


def run_query(query):
    conn = None
    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn).fillna("")
        return df
    except Exception as e:
        logging.error(f"Erro ao executar a consulta: {str(e)}")
        return None
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

        df = run_query(sql_query)
        if df is None or df.empty:
            flash("Erro ao executar a consulta ou nenhum dado retornado.")
            return redirect(url_for('index'))

        table_html = df.head(100).to_html(index=False, classes="table table-bordered", border=1)

        if action == "export":
            if export_format == 'excel':
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name=sheet_name or "Sheet1")
                    worksheet = writer.sheets[sheet_name or "Sheet1"]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                output.seek(0)
                return send_file(output, as_attachment=True, download_name=f"{filename_base}.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

            elif export_format == 'pdf':
                pdf_buffer = df_to_pdf(df)
                return send_file(pdf_buffer, as_attachment=True, download_name=f"{filename_base}.pdf", mimetype='application/pdf')

            elif export_format in ('csv', 'powerbi'):
                output = io.StringIO()
                sep = ';' if export_format == 'csv' else ','
                df.to_csv(output, index=False, sep=sep)
                output.seek(0)
                ext = 'xls' if export_format == 'csv' else 'csv'
                mimetype = 'application/vnd.ms-excel' if export_format == 'csv' else 'text/csv'
                return send_file(io.BytesIO(output.getvalue().encode('utf-8')), as_attachment=True, download_name=f"{filename_base}.{ext}", mimetype=mimetype)

            else:
                flash("Formato inválido.")
                return redirect(url_for('index'))

    return render_template(
        "index.html",
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