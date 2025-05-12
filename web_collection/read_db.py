import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()


cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = cursor.fetchall()

# 提取表名列表并格式化输出
table_names = [table[0] for table in tables]
print("数据库包含的表名：")
for name in table_names:
    print(f"· {name}")



rows = cursor.execute("SELECT * FROM core_webpage")
print("WebPage:")
for row in rows:
    print(row)

rows = cursor.execute("SELECT * FROM core_newsarticle")
print("NewsArticle:")
for row in rows:
    print(row)
conn.close()

rows = cursor.execute("SELECT * FROM core_relationship")
print("Relationship:")
for row in rows:
    print(row)
conn.close()

rows = cursor.execute("SELECT * FROM core_entity")
print("Entity:")
for row in rows:
    print(row)
conn.close()