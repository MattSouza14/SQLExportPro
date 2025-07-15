import pyodbc
from dotenv import load_dotenv
import logging
import os

load_dotenv()

def get_db_connection():
  
    try:
        conn = pyodbc.connect(
        f"DRIVER={{{os.getenv('SQL_DRIVER')}}};"
        f"SERVER={os.getenv('SQL_SERVER')};"
        f"DATABASE={os.getenv('SQL_DATABASE')};"
        "Trusted_Connection=yes;"
        f"Encrypt={os.getenv('SQL_ENCRYPT', 'yes')};"
        f"TrustServerCertificate={os.getenv('SQL_TRUST_SERVER_CERTIFICATE', 'yes')};"
        f"Connection Timeout={os.getenv('SQL_CONNECTION_TIMEOUT', '30')};"
        f"ApplicationIntent={os.getenv('SQL_APPLICATION_INTENT', 'ReadOnly')};"  
        )
        logging.info("Conexão com o SQL Server estabelecida com sucesso")
        return conn
        
    except pyodbc.InterfaceError as e:
        error_msg = f"Erro de interface ODBC: {str(e)}"
        logging.error(error_msg)
        raise ConnectionError(error_msg)
        
    except pyodbc.OperationalError as e:
        error_msg = f"Erro operacional: {str(e)}"
        logging.error(error_msg)
        raise ConnectionError(error_msg)
        
    except Exception as e:
        error_msg = f"Erro inesperado: {str(e)}"
        logging.error(error_msg)
        raise ConnectionError(error_msg)