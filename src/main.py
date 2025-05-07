import pandas as pd
from datetime import datetime
from config.db_connection import get_db_connection
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sql_export.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def export_to_excel():
    
    try:
        conn = get_db_connection()
        
        query = """

"""
        df = pd.read_sql(query, conn)
        
        nome_arquivo = f"Relatorio_Dev_Venda_Recusas{datetime.now().strftime('%d%m%Y')}.xlsx"
        
        with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Adiantamentos")
            
           #ajuste das laguras das colunas
            worksheet = writer.sheets["Adiantamentos"]
            for column in worksheet.columns:
                max_length = max(len(str(cell.value)) for cell in column)
                adjusted_width = min(max_length + 2, 50) 
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
        
        logging.info(f"Arquivo gerado com sucesso: {nome_arquivo}")
        return True
        
    except ConnectionError as e:
        logging.error(f"Erro de conexão: {str(e)}")
        return False
        
    except pd.errors.DatabaseError as e:
        logging.error(f"Erro na query SQL: {str(e)}")
        return False
        
    except Exception as e:
        logging.error(f"Erro inesperado: {str(e)}")
        return False
        
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logging.info("Conexão com o banco de dados fechada")

if __name__ == "__main__":
    
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    
    success = export_to_excel()
    if success:
        print("Operação concluída com sucesso")
    else:
        print("Ocorreu um erro durante a operação")