import os
import json
import psycopg2
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Підключення до бази даних
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# SQL-запит для отримання даних
query = """
SELECT u.user_id, u.username, COUNT(s.id) AS screenshots_uploaded
FROM users u
LEFT JOIN screenshots s ON u.user_id = s.user_id
GROUP BY u.user_id, u.username
ORDER BY screenshots_uploaded DESC;
"""
cursor.execute(query)
results = cursor.fetchall()

# Створення списку словників для JSON-даних
data = [
    {"user_id": row[0], "username": row[1], "screenshots_uploaded": row[2]}
    for row in results
]

# Запис у JSON-файл
with open("user_data.json", "w", encoding='utf-8') as json_file:
    json.dump(data, json_file, indent=4, ensure_ascii=False)

# Генерація діаграми
usernames = [item['username'] for item in data]
screenshots = [item['screenshots_uploaded'] for item in data]

plt.figure(figsize=(10, 6))
plt.bar(usernames, screenshots, color='skyblue')
plt.xlabel("Username")
plt.ylabel("Screenshots Uploaded")
plt.title("Screenshots Uploaded by Users")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# Зберігає діаграму як зображення
plt.savefig("screenshots_uploaded.png")
plt.close()

# Закриття підключення
cursor.close()
conn.close()
