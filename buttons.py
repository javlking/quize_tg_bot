from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


# Кнопка для получения номера телефона
def get_phone_number_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    number = KeyboardButton('Поделиться контактом', request_contact=True)

    kb.add(number)

    return kb


# Основное меню
def main_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    start_test = KeyboardButton('Начать тест')
    statistic = KeyboardButton('Список лидеров')

    kb.add(start_test, statistic)

    return kb


def choose_test_level_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    easy = KeyboardButton('Easy')
    medium = KeyboardButton('Medium')
    hard = KeyboardButton('Hard')
    back = KeyboardButton('Назад')

    kb.add(easy, medium, hard, back)

    return kb


# Кнопки для динамической генерации вариантов к вопросу
def get_question_variants(question_id, question_variants):
    kb = InlineKeyboardMarkup(row_width=1)

    for var in question_variants:
        kb.add(InlineKeyboardButton(text=var,
                                    callback_data=f'{question_id}_{question_variants.index(var)+1}'))

    return kb
