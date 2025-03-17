import logging
import aiogram
import psycopg2
import asyncio

from docxtpl import DocxTemplate
import os

from aiogram import Bot, Dispatcher, types,Router,F 
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder


API_TOKEN = '6626656931:AAEK10v9gbhTbBxMQpwIEotSjpmWFzxvg1M'

logging.basicConfig(level=logging.INFO,format="%(filename)s:%(lineno)d #%(levelname)-8s " "[%(asctime)s] - %(name)s - %(message)s")

bot = Bot(token=API_TOKEN)
async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

router: Router=Router()
params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'botpolitech',
        'user': 'postgres',
        'password': 'parol'
     }
conn = psycopg2.connect(**params)

# params2={
#     'host': 'localhost',
#     'port': 5432,
#     'database': 'leaders',
#     'user': 'postgres',
#     'password': 'parol'
# }
# conn2 = psycopg2.connect(**params2)

class dialog(StatesGroup):
    datespractice=State()
    takeleaders=State()
    sendMessage = State()


@router.message(Command('start'))
async def start(message: Message):
    name=message.from_user.full_name
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(types.KeyboardButton(text='Практика'))
    keyboard.add(types.KeyboardButton(text='Трудоустройство'))
    keyboard.add(types.KeyboardButton(text='Заказать письмо в организацию'))
    keyboard.add(types.KeyboardButton(text='Стажировка'))
    keyboard.add(types.KeyboardButton(text='Контакты'))
    keyboard.adjust(2)
    await message.answer(f'Здравствуйте {name}, я чат-бот Центра карьеры и трудоустройства, выберите ниже, какой раздел Вас интересует.', reply_markup=keyboard.as_markup(resize_keyboard=True))


@router.message(F.text=='Практика')
async def practice(message:Message,state:FSMContext):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(types.KeyboardButton(text='Узнать даты практики'))
    keyboard.add(types.KeyboardButton(text='Узнать ответственного за практику'))
    keyboard.add(types.KeyboardButton(text='Список предприятий где можно практиковаться'))
    keyboard.add(types.KeyboardButton(text='Нет нужного пункта'))
    keyboard.add(types.KeyboardButton(text='На главную'))
    keyboard.adjust(1)
    await message.answer('Выберите вопрос из нижепредставленных.',reply_markup=keyboard.as_markup(resize_keyboard=True))

@router.message(F.text=='На главную')
async def practice(message:Message,state:FSMContext):
    await state.clear()
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(types.KeyboardButton(text='Практика'))
    keyboard.add(types.KeyboardButton(text='Трудоустройство'))
    keyboard.add(types.KeyboardButton(text='Заказать письмо в организацию'))
    keyboard.add(types.KeyboardButton(text='Стажировка'))
    keyboard.add(types.KeyboardButton(text='Контакты'))
    keyboard.adjust(1)
    await message.answer(f'Вы на главной странице.', reply_markup=keyboard.as_markup(resize_keyboard=True))


@router.message(F.text=='Узнать даты практики')
async def dtpractice(message:Message,state:FSMContext):
    await state.set_state(dialog.datespractice)
    await message.answer('Напишите свою группу в формате 111-111.')


@router.message(dialog.datespractice)
async def datespractice(message:Message,state:FSMContext):
    grup=message.text
    menu_buttons = ['Практика', 'Трудоустройство', 'Заказать письмо в организацию', 'Стажировка', 'Контакты', 
                   'Узнать даты практики', 'Узнать ответственного за практику', 
                   'Список предприятий где можно практиковаться', 'Нет нужного пункта']
    
    if grup in menu_buttons:
        await state.clear()
        if grup == 'Практика':
            await practice(message, state)
        elif grup == 'Трудоустройство':
            await practice(message, state)  # Используем существующую функцию practice для обработки
        elif grup == 'Заказать письмо в организацию':
            await letter(message, state)
        elif grup == 'Стажировка':
            await practice(message, state)  # Используем существующую функцию practice для обработки
        elif grup == 'Контакты':
            await practice(message, state)  # Используем существующую функцию practice для обработки
        return

    if grup=='Назад':
        await message.answer('Вы на Главной странице раздела Практика.')
        await state.clear()
    else:
        cur = conn.cursor()
        print(grup)
        base=['fm','aspirantura','feiu','fit','fhtib','fuigh','igrik','iidizh','pi','pishe','tf']
        for i in range(len(base)):
            cur.execute('SELECT datestart, dateend FROM "{}" WHERE TRIM(BOTH FROM REPLACE(REPLACE("group", CHR(13), \'\'), CHR(10), \'\')) = TRIM(BOTH FROM %s)'.format(base[i]), (grup,))
            dates = cur.fetchall()
            if dates:
                break
        if dates==[]:
            await message.answer('Такой группы нет в моей базе данных, проверьте корректность введённых данных')
        else:
            formatted_dates = [(date[0].strftime('%d.%m.%Y'), date[1].strftime('%d.%m.%Y')) for date in dates]
            cur.execute('SELECT type FROM "{}" WHERE TRIM(BOTH FROM REPLACE(REPLACE("group", CHR(13), \'\'), CHR(10), \'\')) = TRIM(BOTH FROM %s)'.format(base[i]), (grup,))
            types = cur.fetchall()
            
            if all(date[0] == '01.01.2001' for date in dates):
                await message.answer('В этом году у Вас нет практики!')
            else:
                answer = 'Ваши практики:\n'
                for idx, (start_date, end_date) in enumerate(formatted_dates):
                    if start_date != '01.01.2001':
                        type_practice = types[idx][0] if idx < len(types) else "Тип не указан"
                        answer += f"\n{idx + 1}. Практика:\n"
                        answer += f"Дата начала: {start_date}\n"
                        answer += f"Дата окончания: {end_date}\n"
                        answer += f"Тип практики: {type_practice}\n"
                await message.answer(answer)
            await state.clear()


@router.message(F.text=='Узнать ответственного за практику')
async def leaders(message:Message,state:FSMContext):
    await state.set_state(dialog.takeleaders)
    await message.answer('Напишите свою группу в формате 111-111.')


@router.message(dialog.takeleaders)
async def leadersractice(message:Message,state:FSMContext):
    grup=message.text
    menu_buttons = ['Практика', 'Трудоустройство', 'Заказать письмо в организацию', 'Стажировка', 'Контакты', 
                   'Узнать даты практики', 'Узнать ответственного за практику', 
                   'Список предприятий где можно практиковаться', 'Нет нужного пункта']
    
    if grup in menu_buttons:
        await state.clear()
        if grup == 'Практика':
            await practice(message, state)
        elif grup == 'Трудоустройство':
            await practice(message, state)  # Используем существующую функцию practice для обработки
        elif grup == 'Заказать письмо в организацию':
            await letter(message, state)
        elif grup == 'Стажировка':
            await practice(message, state)  # Используем существующую функцию practice для обработки
        elif grup == 'Контакты':
            await practice(message, state)  # Используем существующую функцию practice для обработки
        return

    if grup=='Назад':
        await message.answer('Вы на главной странице раздела Практика.')
        await state.clear()
    else:
        cur = conn.cursor()
        base=['fm','aspirantura','feiu','fit','fhtib','fuigh','igrik','iidizh','pi','pishe','tf']
        for i in range(len(base)):
            cur.execute('SELECT leader, type FROM "{}" WHERE TRIM("group") = TRIM(%s)'.format(base[i]), (grup,))
            basee = cur.fetchall()
            if basee:
                break
        if basee==[]:
            await message.answer('Такой группы нет в моей базе данных, проверьте корректность введённых данных.')
        else:
            if all(leader_data[0] == '-' for leader_data in basee):
                await message.answer('В учебном плане практика в этом году не стоит')
            else:
                answer = 'Информация об ответственных за практику:\n'
                for idx, (leader, type_practice) in enumerate(basee, 1):
                    if leader != '-':
                        answer += f"\nПрактика {idx} ({type_practice})\n"
                        # Разделяем данные по запятой, если она есть
                        leader_info = leader.split(',')
                        leader_name = leader_info[0].strip()
                        contact = leader_info[1].strip() if len(leader_info) > 1 and leader_info[1].strip() else 'контакт отсутствует'
                        answer += f"Ответственный: {leader_name}\n"
                        answer += f"Контакт: {contact}\n"
                await message.answer(answer)
            await state.clear()

@router.message(F.text=='Заказать письмо в организацию')
async def letter(message:Message,state:FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username

    user_link = f"@{username}" if username else f"[пользователь](tg://user?id={user_id})"
    await state.update_data(user_link=user_link)

    await state.set_state(dialog.sendMessage)
    await message.answer(
        "📄 Введите данные:\n"
        "1️⃣ ФИО и группа студента (например: Иванов Иван Иванович, 221-365)\n"
        "2️⃣ Наименование организации (например: ПАО \"Роснефть\")\n"
        "3️⃣ ФИО и должность получателя письма (например: Петров Петр Петрович, Директор)\n"
        "4️⃣ Куда отправлять письмо? (например: ivanov@example.com)\n"
        "5️⃣ Даты практики (например: 01.06.2025 - 30.07.2025)"
    )

@router.message(F.text=='Через университет')
async def takeLetterUn(message:Message,state:FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username

    user_link = f"@{username}" if username else f"[пользователь](tg://user?id={user_id})"
    await state.update_data(user_link=user_link)

    await state.set_state(dialog.sendMessage)
    await message.answer(
        "📄 Введите данные:\n"
        "1️⃣ ФИО и группа студента (например: Иванов Иван Иванович, 221-365, Прикладная информатика)\n"
        "2️⃣ Наименование организации (например: ПАО \"Роснефть\")\n"
        "3️⃣ ФИО и должность получателя письма (например: Петров Петр Петрович, Директор)\n"
        "4️⃣ Куда отправлять письмо? (например: ivanov@example.com)\n"
        "5️⃣ Даты практики (например: 01.06.2025 - 30.07.2025)"
    )

import os
import re
from docxtpl import DocxTemplate
from aiogram.types import FSInputFile
from docxtpl import DocxTemplate
import os
from aiogram.types import FSInputFile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "soprovoditelnoe-pismo-praktika.docx")

def validate_name_group(text):
    """Проверка формата 'Фамилия Имя Отчество, Группа'"""
    pattern = r"^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+, \d{3}-\d{3}$"
    return bool(re.match(pattern, text))

def validate_organization(text):
    """Название организации не должно быть пустым"""
    return len(text.strip()) > 1

def validate_recipient(text):
    """Проверка формата 'Фамилия Имя Отчество, Должность'"""
    pattern = r"^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+, .+$"
    return bool(re.match(pattern, text))

def validate_email(text):
    """Проверка email"""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, text))

def validate_dates(text):
    """Проверка формата 'дд.мм.гггг - дд.мм.гггг'"""
    pattern = r"^\d{2}\.\d{2}\.\d{4} - \d{2}\.\d{2}\.\d{4}$"
    return bool(re.match(pattern, text))

def validate_direction(text):
    """Название направления не должно быть пустым"""
    return len(text.strip()) > 1

def is_male_name(name):
    """Проверка, является ли имя мужским"""
    # Список женских окончаний
    female_endings = ['а', 'я', 'е', 'и', 'о', 'у', 'ю', 'ь']
    return not any(name.lower().endswith(ending) for ending in female_endings)

def format_recipient_name(full_name):
    """Форматирование имени получателя"""
    parts = full_name.split()
    if len(parts) != 3:
        return None, None
    
    surname, name, patronymic = parts
    
    # Определяем пол по имени
    is_male = is_male_name(name)
    
    # Формируем recipient_name_1 (фамилия с инициалами)
    recipient_name_1 = f"{surname}{'у' if is_male else 'ой'} {name[0]}. {patronymic[0]}."
    
    # Формируем recipient_name_2 (имя и отчество)
    recipient_name_2 = f"{name} {patronymic}"
    
    return recipient_name_1, recipient_name_2

async def generate_word_document(user_data):
    """Генерация документа из шаблона"""
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Шаблон не найден: {TEMPLATE_PATH}")

    # Создаем директорию для временных файлов, если она не существует
    temp_dir = os.path.join(BASE_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Форматируем имя получателя
    recipient_name_1, recipient_name_2 = format_recipient_name(user_data.get("recipient_name", ""))

    doc = DocxTemplate(TEMPLATE_PATH)
    context = {
        "organization": user_data.get("organization", "Название организации"),
        "recipient_name_1": recipient_name_1 or "ФИО получателя",
        "recipient_name_2": recipient_name_2 or "Имя Отчество",
        "position": user_data.get("position", "Должность"),
        "name": user_data.get("name", "ФИО студента"),
        "group": user_data.get("group", "Группа"),
        "practice_type": "производственная",
        "start_date": user_data.get("start_date", "Неизвестно"),
        "end_date": user_data.get("end_date", "Неизвестно"),
        "email": user_data.get("email", "Неизвестно")
    }

    doc.render(context)
    
    # Создаем безопасное имя файла
    safe_filename = sanitize_filename(f"Сопроводительное письмо_{user_data['name']}.docx")
    file_path = os.path.join(temp_dir, safe_filename)
    
    doc.save(file_path)
    return file_path

@router.message(dialog.sendMessage)
async def sendingMessage(message: types.Message, state: FSMContext):
    """Обработка сообщения и генерация письма"""
    user_data = await state.get_data()
    text_lines = message.text.strip().split("\n")

    if len(text_lines) < 5:
        await message.answer(
            "⚠️ Ошибка! Данные введены некорректно! Попробуйте снова.\n\n"
            "📌 Пример правильного ввода:\n"
            "1️⃣ Иванов Иван Иванович, 221-365\n"
            "2️⃣ ПАО \"Роснефть\"\n"
            "3️⃣ Петров Петр Петрович, Директор\n"
            "4️⃣ ivanov@example.com\n"
            "5️⃣ 01.06.2025 - 30.07.2025"
        )
        return

    elif len(text_lines) > 5:
        await message.answer(
            "⚠️ Ошибка! Вы ввели больше строк, чем нужно. Пожалуйста, введите только 5 строк."
        )
        return
    try:
        name_group = text_lines[0]
        organization = text_lines[1]
        recipient = text_lines[2]
        email = text_lines[3]
        dates = text_lines[4]

        if not validate_name_group(name_group):
            await message.answer("⚠️ Ошибка! ФИО и группа должны быть в формате: Иванов Иван Иванович, 221-365")
            return
        if not validate_organization(organization):
            await message.answer("⚠️ Ошибка! Название организации не может быть пустым и не должно превышать 200 символов.")
            return
        if not validate_recipient(recipient):
            await message.answer("⚠️ Ошибка! ФИО и должность должны быть в формате: Петров Петр Петрович, Директор")
            return
        if not validate_email(email):
            await message.answer("⚠️ Ошибка! Введите корректный email (например, ivanov@example.com)")
            return
        if not validate_dates(dates):
            await message.answer("⚠️ Ошибка! Даты должны быть в формате: 01.06.2025 - 30.07.2025")
            return

        name_group_parts = name_group.split(", ")
        user_data["name"], user_data["group"] = name_group_parts[0], name_group_parts[1]
        user_data["organization"] = organization
        recipient_data = recipient.split(", ")
        user_data["recipient_name"] = recipient_data[0]
        user_data["position"] = recipient_data[1]
        user_data["email"] = email
        date_parts = dates.split(" - ")
        user_data["start_date"] = date_parts[0]
        user_data["end_date"] = date_parts[1]

        file_path = await generate_word_document(user_data)

        target_user_id = '825730913'
        try:
            await message.bot.send_document(target_user_id, FSInputFile(file_path))
            logging.info(f"Документ отправлен пользователю с ID {target_user_id}")
            await message.answer("✅ Ваше письмо успешно создано и отправлено!")
        except Exception as e:
            logging.error(f"Ошибка при отправке документа пользователю с ID {target_user_id}: {e}")
            await message.answer("❌ Произошла ошибка при отправке письма. Пожалуйста, попробуйте позже.")

        # Удаляем временный файл
        try:
            os.remove(file_path)
        except Exception as e:
            logging.error(f"Ошибка при удалении временного файла: {e}")

    except Exception as e:
        logging.error(f"Ошибка при обработке данных: {e}")
        await message.answer("❌ Произошла ошибка при обработке данных. Проверьте формат ввода и попробуйте снова.")

    await state.clear()


@router.message(F.text=='Список предприятий где можно практиковаться')
async def leaders(message:Message,state:FSMContext):
    await message.answer('Ознакомиться со списком предприятий Вы можете по ссылке: https://docs.google.com/spreadsheets/d/1CHqkL9HFrMwTht4JforpcM3VwWNUeofkSnJ4vUHU9Wk/edit#gid=0')

@router.message(F.text=='Нет нужного пункта')
async def punkt(message:Message,state:FSMContext):
    await message.answer('По всем интересующим Вас вопросам Вы можете обратиться по следующему контакту: @zhenia_korshunova.')

@router.message(F.text=='Трудоустройство')
async def practice(message:Message,state:FSMContext):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(types.KeyboardButton(text='Как записаться на консультацию в центр карьеры трудоустройства'))
    keyboard.add(types.KeyboardButton(text='Как составить резюме'))
    keyboard.add(types.KeyboardButton(text='Лайфхаки как пройти собеседование'))
    keyboard.add(types.KeyboardButton(text='Оставить отзыв по работе центра карьеры'))
    keyboard.add(types.KeyboardButton(text='На главную'))
    keyboard.adjust(1)
    await message.answer('Выбери вопрос из нижепредставленных',reply_markup=keyboard.as_markup(resize_keyboard=True))

@router.message(F.text=='Как записаться на консультацию в центр карьеры трудоустройства')
async def help_command(message:Message,state:FSMContext):
    await message.answer(text='Телефон центра карьеры: +7 (495) 223-05-23 доб. 1516, 1565, более подробная информация на сайте: https://mospolytech.ru/obuchauschimsya/trudoustrojstvo/')

@router.message(F.text=='Как составить резюме')
async def help_command1(message:Message,state:FSMContext):
    await message.answer(text='Ссылка на гайд по созданию резюме: https://mospolytech.ru/obuchauschimsya/trudoustrojstvo/kak-sostavit-rezyume/')

@router.message(F.text=='Лайфхаки как пройти собеседование')
async def help_command2(message:Message,state:FSMContext):
    await message.answer(text= 'Ссылка на источник с полезными советами для увеличения вероятности прохождения собеседования:https://smolensk.hh.ru/article/29604')

@router.message(F.text=='Оставить отзыв по работе центра карьеры')
async def help_command3(message:Message,state:FSMContext):
    await message.answer(text= 'Отзыв можно отправить по почте: partner@mospolytech.ru')

@router.message(F.text=='Стажировка')
async def practice(message:Message,state:FSMContext):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(types.KeyboardButton(text='Сервисы поиска стажировки'))
    keyboard.add(types.KeyboardButton(text='Оставить отзыв по работе центра карьеры'))
    keyboard.add(types.KeyboardButton(text='Как оформиться на стажировку'))
    keyboard.add(types.KeyboardButton(text='На главную'))
    keyboard.adjust(1)
    await message.answer('Выберите вопрос из нижепредставленных.',reply_markup=keyboard.as_markup(resize_keyboard=True))

@router.message(F.text=='Сервисы поиска стажировки')
async def practice(message:Message,state:FSMContext):
    await message.answer('Ниже представлены ссылки, на которых Вы можете найти для себя стажировку:\n1. https://fut.ru/catalog/\n2. Социальные сети Центра Карьеры\n3. Cайты организаций\n4. Факультетус: https://facultetus.ru/jobfinder\n5.  HH.ру: https://hh.ru/stazhirovki')

@router.message(F.text=='Оставить отзыв по работе центра карьеры')
async def practice(message:Message,state:FSMContext):
    await message.answer('Отзыв можно отправить по почте: partner@mospolytech.ru')

@router.message(F.text=='Как оформиться на стажировку')
async def practice(message:Message,state:FSMContext):
    await message.answer('Вам необходимо выбрать интересующую Вас кампанию и Университет подготовит для Вас сопроводительное письмо.')

@router.message(F.text=='Контакты')
async def practice(message:Message,state:FSMContext):
    await message.answer('1. E-mail: partner@mospolytech.ru\n2. Телефон: +7 (495) 223-05-23 доб. 1516, 1565\n3. Начальник центра: Дьякова Дарья Сергеевна\n4. E-mail Начальника центра: d.s.dyakova@mospolytech.ru\n5. Адрес: Москва, Большая Семёновская, 38, А-404')




if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())