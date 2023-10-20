import sqlite3

# Crie uma conexão com o banco de dados (ou crie um novo arquivo de banco de dados se não existir)
conn = sqlite3.connect('CaixaApp.db')

# Crie um cursor para executar consultas SQL
cursor = conn.cursor()

# Crie uma tabela para armazenar os dados de transação
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        transaction_type TEXT,
        amount REAL,
        reason TEXT
    )
''')

# Feche a conexão com o banco de dados
conn.close()

print("Banco de dados 'my_money_app.db' criado com sucesso.")