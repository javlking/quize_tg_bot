import requests
from aiogram import Dispatcher, Bot, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove

import states
import buttons
import database

bot = Bot('6157892774:AAEtE5lz9E9fTPEZ3XNOuRWcaqhW8rYoWlw')
dp = Dispatcher(bot, storage=MemoryStorage())

main_url = 'http://127.0.0.1:5000'


# Start
@dp.message_handler(commands=['start'])
async def start_message(message):
    user_id = message.from_user.id
    text = 'Добро пожаловать в бот для тестирования\nОтправьте свое имя'

    checker = database.check_user_db(user_id)

    if checker:
        await message.answer('Выберите пункт меню', reply_markup=buttons.main_menu_kb())

    else:
        await message.answer(text)

        # Переход на этап получения имени
        await states.Registration.get_name_state.set()


# Этап получения имени
@dp.message_handler(state=states.Registration.get_name_state)
async def get_user_name(message, state=states.Registration.get_name_state):
    user_id = message.from_user.id

    # Получаем имя отправленное сообщением
    username = message.text

    # Сохраняем во временный словарь как ключ name
    await state.update_data(name=username)

    # Отправляем ответ с кнопкой для отправки номера телефона
    await message.answer('Отправьте номер телефона', reply_markup=buttons.get_phone_number_kb())

    # Переходим на этап получения номера телефона
    await states.Registration.get_number_state.set()


# Этап получения номера и завершения регистрации
@dp.message_handler(state=states.Registration.get_number_state, content_types=['contact'])
async def get_user_number(message, state=states.Registration.get_number_state):
    user_id = message.from_user.id

    # Получаем контакт
    user_contact = message.contact.phone_number

    # Получаем имя из временного словаря
    user_data = await state.get_data()
    user_name = user_data.get('name')  # Сохраняли на 52 строке

    # Отправляем post запрос на регистрацию в наш quiz_api и получаем уникальный айди для пользователя
    register_url = main_url + f'/register/{user_name}/{user_contact}'
    response = requests.post(register_url)

    # Получаем ответ в виде json
    data = response.json()  # -> {'status': 1, 'user_id': some integer}

    # регистрируем на локальную базу уже нашего бота
    database.register_user_db(user_tg_id=user_id, user_quiz_id=data.get('user_id'))

    # Отправляем ответ
    await message.answer(f'Вы успешно зарегистрированы\nВаш идентификатор: {data.get("user_id")}',
                         reply_markup=buttons.main_menu_kb())

    # Завершаем процесс регистрации
    await state.finish()


# Обработчик сообщений основного меню
@dp.message_handler(lambda message: message.text in ['Начать тест', 'Список лидеров'])
async def main_menu_handler(message):
    user_id = message.from_user.id

    if message.text == 'Начать тест':
        await message.answer('Выберите уровень сложности', reply_markup=buttons.choose_test_level_kb())

        # переход на этап получения уровня сложности
        await states.TestProcess.waiting_for_level.set()

    elif message.text == 'Список лидеров':
        # пропишите запрос на получение списка лидеров и сформируйте сообщение
        await message.answer('В коде есть комментарий\nСамостоятельно реализуйте')

        # Должен быть переход на этап получения уровня сложности и там же обращение к api


@dp.message_handler(state=states.TestProcess.waiting_for_level)
async def get_question_level(message, state=states.TestProcess.waiting_for_level):
    user_id = message.from_user.id
    user_answer = message.text

    if user_answer == 'Назад':
        await message.answer('Выберите пункт меню', reply_markup=buttons.main_menu_kb())

        await state.finish()

    elif user_answer in ['Easy', 'Medium', 'Hard']:
        # Отправляем get запрос на получение вопросов
        # по выбранному уровню в наш quiz_api и получаем 20 из них если есть
        get_questions_url = main_url + f'/get-questions/{user_answer}'
        response = requests.get(get_questions_url)

        # Получаем ответ в виде json
        data = response.json()  # -> {'timer': some integer, 'questions': some dict}

        # Проверяем нашел ли вопросы
        if data.get('questions'):
            # Если есть вопросы, то локально сохраним в state и выбранный уровень
            await state.update_data(user_questions=data.get('questions')[1:],
                                    level=user_answer,
                                    user_correct_answers=0)

            # Отправляем первый вопрос из списка
            first_question = data.get('questions')[0]

            question_text = first_question.get('question').get('question_text')
            variants = first_question.get('question').get('variants')
            question_id = first_question.get('question_id')

            # Перед тем как задать вопрос посмотри на эти принты и что они напечатают на терминале
            # print(first_question)
            # print(first_question.get('question'))
            # print(first_question.get('question').get('question_text'))

            await message.answer('Начинаем', reply_markup=ReplyKeyboardRemove())

            await message.answer(question_text,
                                 reply_markup=buttons.get_question_variants(question_id, variants))

            # Переход на этап прохождения теста
            await states.TestProcess.waiting_for_answer.set()


# процесс прохождения теста
@dp.callback_query_handler(state=states.TestProcess.waiting_for_answer)
async def answering_process(call, state=states.TestProcess.waiting_for_answer):
    user_id = call.message.chat.id
    user_answer = call.data  # -> questionid_variantnumber (34_2)

    # Переводим данные нажатой кнопки в нужный формат (получаем айди вопроса
    # и тот вариант на который нажал пользователь)
    current_question_id = user_answer.split('_')[0]
    user_chosen_variant = user_answer.split('_')[1]

    # Посмотри обязательно !!!
    # print(user_answer)
    # print(user_answer.split('_'))
    # print(user_answer.split('_')[0])
    # print(user_answer.split('_')[1])

    # Отправляем post запрос на наш api для проверки ответа
    get_question_correctness_url = main_url + f'/check-answer/{current_question_id}/{user_chosen_variant}'
    response = requests.post(get_question_correctness_url)

    # Получаем ответ в виде json
    data = response.json()  # -> {'status': if correct 1, if not 0}

    # получаем данные из state (временное хранилище)
    questions_from_state = await state.get_data()

    # Проверка на: остались ли вопросы
    if len(questions_from_state.get('user_questions')) > 0:
        # Получаем следующий вопрос
        next_question = questions_from_state.get('user_questions')[0]
        corrects_counter = questions_from_state.get('user_correct_answers')

        # Обновляем вопросы для state
        await state.update_data(user_questions=questions_from_state.get('user_questions')[1:],)

        # счетчик правильных ответов
        if data.get('status') == 1:
            await state.update_data(user_correct_answers=corrects_counter+1)

        question_text = next_question.get('question').get('question_text')
        variants = next_question.get('question').get('variants')
        question_id = next_question.get('question_id')

        # Перед тем как задать вопрос посмотри на эти принты и что они напечатают на терминале
        # print(next_question)
        # print(next_question.get('question'))
        # print(next_question.get('question').get('question_text'))

        correct_or_not = 'Вы ответили правильно' if data.get('status') == 1 else 'Вы ответили неправильно'

        await call.message.edit_text(f'{correct_or_not}\n\nСледующий вопрос:\n{question_text}',
                                     reply_markup=buttons.get_question_variants(question_id, variants))

    else:
        correct_or_not = 'Вы ответили правильно' if data.get('status') == 1 else 'Вы ответили неправильно'
        user_correct_answers = questions_from_state.get("user_correct_answers") + 1 if data.get('status') == 1 else questions_from_state.get("user_correct_answers")

        # Получим quiz_id пользователя из локальной базы
        user_quiz_api = database.check_user_db(user_id)

        # Отправим post запрос на запись результатов
        get_top_url = main_url + f'/done/{user_quiz_api}/{user_correct_answers}/{questions_from_state.get("level")}'
        response = requests.post(get_top_url)

        # Получаем ответ в виде json
        pos_on_top = response.json()  # -> {'status': if correct 1, if not 0}

        result = pos_on_top.get('position_on_top')
        await call.message.edit_text(f'{correct_or_not}\n\n'
                                     f'Ваш тест завершен\n\n'
                                     f'Количество правильных ответов: {user_correct_answers}\n'
                                     f'Ваша позиция в топе: {result}')

        # Завершаем процесс прохождения теста
        await state.finish()

        await call.message.answer('Выберите пункт меню', reply_markup=buttons.main_menu_kb())

executor.start_polling(dp)
