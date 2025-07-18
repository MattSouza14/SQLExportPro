# 📊 SQLExportPro

**SQLExportPro** é uma aplicação web construída com **Flask** que permite executar consultas SQL e exportar os resultados em diversos formatos: **Excel (.xlsx)**, **PDF**, **CSV (.xls)** e **CSV compatível com Power BI**. Além disso, oferece recursos como salvamento de consultas e **autocompletar inteligente** com base nas tabelas e colunas do banco de dados.

---

## 🔧 Funcionalidades

- ✅ Interface web responsiva e amigável
- 🧠 Autocompletar de tabelas e colunas (baseado em `INFORMATION_SCHEMA`)
- 📝 Execução de consultas SQL diretamente via navegador
- 💾 Salvamento de consultas personalizadas em arquivos `.sql`
- 📤 Exportação de resultados nos formatos:
  - Excel (.xlsx)
  - PDF
  - CSV (.xls compatível com Excel)
- 📁 Organização por nome de planilha, worksheet e nome de arquivo
- 🔐 Chave secreta de sessão segura

---

## 📁 Estrutura do Projeto









---

## ⚙️ Requisitos

- Python 3.8+
- Um banco de dados compatível com `pyodbc` ou `pymssql` (ex: SQL Server)
- Pacotes Python:

```bash



