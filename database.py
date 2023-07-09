import sqlite3


# Зарегистрировать пользователя
def register_user_db(user_tg_id, user_quiz_id):
    connection = sqlite3.connect('bot_data.db')
    sql = connection.cursor()

    sql.execute('INSERT INTO users VALUES (?, ?);', (user_tg_id, user_quiz_id))

    connection.commit()


# Проверка пользователя
def check_user_db(user_tg_id):
    connection = sqlite3.connect('bot_data.db')
    sql = connection.cursor()

    user_quiz_id = sql.execute('SELECT user_quiz_id FROM users WHERE user_tg_id=?;', (user_tg_id, )).fetchone()

    # если есть пользователь, возвращаем его айди который был получен с api
    if user_quiz_id:
        return user_quiz_id[0]

    return []


# Создать таблицу
def create_tables():
    connection = sqlite3.connect('bot_data.db')
    sql = connection.cursor()

    sql.execute('CREATE TABLE IF NOT EXISTS users (user_tg_id INTEGER, user_quiz_id INTEGER);')

    return 'Done'



create_tables()