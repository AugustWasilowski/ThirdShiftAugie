import sqlite3

conn = sqlite3.connect("chat_history.db")
cursor = conn.cursor()

# query = """UPDATE templates SET title = 'James';"""
query = "SELECT * FROM chat_history"
# query = """PRAGMA table_info(templates);"""
# query = """SELECT * FROM templates;"""
# query = """SELECT * FROM templates WHERE id = 1;"""





cursor.execute(query)

# Fetch all rows from the last executed SQL command
rows = cursor.fetchall()

# Print all rows
for row in rows:
    print(row)

# Close the connection
conn.close()
