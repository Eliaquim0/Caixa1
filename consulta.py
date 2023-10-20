import sqlite3

# Conecte-se ao banco de dados
conn = sqlite3.connect('CaixaApp.db')

# Crie um cursor
cursor = conn.cursor()

# Execute uma consulta SQL para selecionar todos os registros da tabela 'minha_tabela'
cursor.execute("SELECT * FROM transactions")


# Itere sobre os resultados
for row in results:
    print(row)
