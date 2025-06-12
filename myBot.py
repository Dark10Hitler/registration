from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher, types, F
from icecream import ic
import asyncio
import os
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from aiogram.fsm.storage.memory import MemoryStorage

# user_id_v = '1585564954'
TOKEN = "7943153137:AAGcnE-QLPr7Ltc6_O8ZCHcu57Jt0YHpjxA"
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
user_id = 5060772866
# ✅ Укажем точный путь к БД
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "my_employees.db")

@dp.message(F.text == '/start')
async def start(message: types.Message):
    await send_main_menu(message)

async def send_main_menu(target):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Администрация', callback_data='admin')],
            [InlineKeyboardButton(text='Категория A', callback_data='cat_1')],
            [InlineKeyboardButton(text='Категория B', callback_data='cat_2')],
            [InlineKeyboardButton(text='Категория C', callback_data='cat_3')],
            [InlineKeyboardButton(text='Категория D', callback_data='cat_4')],
            [InlineKeyboardButton(text='Категория E', callback_data='cat_5')],
            [InlineKeyboardButton(text='Категория F', callback_data='cat_6')],
            [InlineKeyboardButton(text='Категория G', callback_data='cat_7')],
        ]
    )
    await target.answer('Приветствую вас в головном управлении центра "Св. Мария"')
    await target.answer('Выберите операцию', reply_markup=markup)


# 🔧 ИНИЦИАЛИЗАЦИЯ БД
def init_db():
    conn = sqlite3.connect("my_employees.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            position TEXT NOT NULL,
            phone_number TEXT
        )
    ''')
    conn.commit()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Employees'")
    table_exists = cursor.fetchone()
    print("Таблица Employees существует:", bool(table_exists))


# 📦 СОСТОЯНИЯ FSM
class AddEmployeeStates(StatesGroup):
    first_name = State()
    last_name = State()
    position = State()
    phone_number = State()
    confirm = State()

class RemoveEmployeeStates(StatesGroup):
    waiting_for_id = State()

# 📋 ПОКАЗАТЬ СОТРУДНИКОВ
@dp.callback_query(F.data == 'admin')
async def show_employees(callback: types.CallbackQuery):
    conn = sqlite3.connect("my_employees.db")
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT employee_id, first_name, last_name, position, phone_number FROM Employees')
        employees = cursor.fetchall()
    except sqlite3.Error as e:
        await callback.message.answer(f"Ошибка базы данных: {e}")
        await callback.answer()
        return
    finally:
        conn.close()

    if employees:
        text = "📋 Список сотрудников:\n"
        for emp in employees:
            emp_id, first_name, last_name, position, phone_number = emp
            text += (
                f"ID: {emp_id}\n"
                f"Имя: {first_name}\n"
                f"Фамилия: {last_name}\n"
                f"Должность: {position}\n"
                f"Телефон: {phone_number}\n\n"
            )
    else:
        text = "Сотрудники в базе отсутствуют."

    await callback.message.answer(text)

    if callback.from_user.id == user_id:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='➕ Добавить', callback_data='add_employee')],
            [InlineKeyboardButton(text='➖ Удалить', callback_data='remove_employee')]
        ])
        await callback.message.answer("Выберите операцию:", reply_markup=markup)
    else:
        await callback.message.answer('⛔ Только админ может управлять сотрудниками.')

    await callback.answer()

# ➕ ДОБАВИТЬ СОТРУДНИКА (FSM)
@dp.callback_query(F.data == 'add_employee')
async def start_add(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите имя сотрудника:')
    await state.set_state(AddEmployeeStates.first_name)
    await callback.answer()

@dp.message(AddEmployeeStates.first_name)
async def get_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Введите фамилию сотрудника:")
    await state.set_state(AddEmployeeStates.last_name)

@dp.message(AddEmployeeStates.last_name)
async def get_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.answer("Введите должность сотрудника:")
    await state.set_state(AddEmployeeStates.position)

@dp.message(AddEmployeeStates.position)
async def get_position(message: types.Message, state: FSMContext):
    await state.update_data(position=message.text)
    await message.answer("Введите номер телефона:")
    await state.set_state(AddEmployeeStates.phone_number)

@dp.message(AddEmployeeStates.phone_number)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone_number=message.text)
    data = await state.get_data()

    confirm_text = (
        f"Добавить этого сотрудника?\n\n"
        f"👤 Имя: {data['first_name']}\n"
        f"👤 Фамилия: {data['last_name']}\n"
        f"📌 Должность: {data['position']}\n"
        f"📱 Телефон: {data['phone_number']}\n\n"
        f"Напишите **да** или **нет**."
    )
    await message.answer(confirm_text)
    await state.set_state(AddEmployeeStates.confirm)

@dp.message(AddEmployeeStates.confirm)
async def confirm_employee(message: types.Message, state: FSMContext):
    menu_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")]]
    )

    if message.text.lower() == "да":
        data = await state.get_data()

        conn = sqlite3.connect("my_employees.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Employees (first_name, last_name, position, phone_number)
            VALUES (?, ?, ?, ?)
        ''', (
            data['first_name'],
            data['last_name'],
            data['position'],
            data['phone_number']
        ))
        conn.commit()
        conn.close()

        await message.answer("✅ Сотрудник добавлен в базу данных.", reply_markup=menu_markup)
    else:
        await message.answer("❌ Добавление отменено.", reply_markup=menu_markup)

    await state.clear()

# ❌ УДАЛЕНИЕ СОТРУДНИКА
@dp.callback_query(F.data == 'remove_employee')
async def ask_for_employee_id(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != user_id:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")]]
        )
        await callback.message.answer("⛔ Только админ может удалять сотрудников.", reply_markup=markup)
        await callback.answer()
        return

    await callback.message.answer("Введите ID сотрудника, которого хотите удалить:")
    await state.set_state(RemoveEmployeeStates.waiting_for_id)
    await callback.answer()

@dp.message(RemoveEmployeeStates.waiting_for_id)
async def process_employee_id_for_deletion(message: types.Message, state: FSMContext):
    # Главное меню-кнопка
    menu_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")]]
    )

    # Проверка доступа
    if message.from_user.id != user_id:
        await message.answer("⛔ Только админ может выполнять это действие.", reply_markup=menu_markup)
        await state.clear()
        return

    emp_id_text = message.text.strip()

    # Проверка, что введён ID — число
    if not emp_id_text.isdigit():
        await message.answer("❗ Пожалуйста, введите корректный числовой ID сотрудника.", reply_markup=menu_markup)
        return

    emp_id = int(emp_id_text)

    # Работа с базой
    try:
        conn = sqlite3.connect("my_employees.db")
        cursor = conn.cursor()

        print(f"Ищу сотрудника с ID = {emp_id}")
        cursor.execute("SELECT * FROM Employees WHERE employee_id = ?", (emp_id,))
        employee = cursor.fetchone()
        print("Найден сотрудник:", employee)

        if not employee:
            await message.answer(f"❌ Сотрудник с ID {emp_id} не найден.", reply_markup=menu_markup)
        else:
            cursor.execute("DELETE FROM Employees WHERE employee_id = ?", (emp_id,))
            conn.commit()
            await message.answer(f"✅ Сотрудник с ID {emp_id} успешно удалён.", reply_markup=menu_markup)

    except sqlite3.Error as e:
        await message.answer(f"⚠️ Ошибка базы данных: {e}", reply_markup=menu_markup)
    finally:
        conn.close()

    await state.clear()

# 🔁 ВОЗВРАТ В МЕНЮ
@dp.callback_query(F.data == 'menu')
async def return_to_main_menu(callback: types.CallbackQuery):
    await callback.message.delete()  # Убираем сообщение с кнопкой
    await send_main_menu(callback.message)
    await callback.answer()

# 👤 FSM состояния для ребёнка
class AddChildStates(StatesGroup):
    first_name = State()
    last_name = State()
    parents = State()
    phone_number = State()
    phone_number_parents = State()

# 👤 FSM состояния для удаления ребёнка
class RemoveChildStates(StatesGroup):
    waiting_for_id = State()

# 🔧 Функция для инициализации базы (один раз, лучше запускать при старте бота)
def init_db_backup():
    with sqlite3.connect("my_children.db") as conn:
        cursor = conn.cursor()  # Вот тут создаём курсор!
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS children (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                parents TEXT,
                phone_number TEXT,
                phone_number_parents TEXT
            )
        ''')

# 🚩 Обработка выбора категории (дети)
@dp.callback_query(F.data.startswith('cat'))
async def show_category(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]

    if callback.from_user.id == user_id:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='➕ Добавить ребёнка', callback_data='add_child')],
                [InlineKeyboardButton(text='➖ Удалить ребёнка', callback_data='remove_child')]
            ]
        )
        await callback.message.answer(f'🔐 Категория {category}: что хотите сделать?', reply_markup=markup)
    else:
        await callback.message.answer(f"📁 Вы открыли категорию {category}. Действия доступны только администратору.")

    # 👇 Показать список детей
    with sqlite3.connect("my_children.db") as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, first_name, last_name, parents, phone_number, phone_number_parents FROM children')
        children = cursor.fetchall()

    if children:
        text = "📋 Список детей:\n"
        for i, child in enumerate(children):
            id_,first_name, last_name, parents, phone, phone_parent = child
            text += f"{id_}.\nИмя: {first_name}\nФамилия: {last_name}\nРодитель: {parents}\nТелефон: {phone}\nТелефон родителя: {phone_parent}\n\n"
    else:
        text = "❗ Дети в базе отсутствуют."

    await callback.message.answer(text)
    await callback.answer()


# ▶️ Начало FSM добавления ребёнка
@dp.callback_query(F.data == "add_child")
async def start_add_child(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != user_id:
        await callback.answer("⛔ Только админ может добавлять детей.", show_alert=True)
        return

    await callback.message.answer("Введите имя ребёнка:")
    await state.set_state(AddChildStates.first_name)


# ➕ Шаги FSM
@dp.message(AddChildStates.first_name)
async def child_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text.strip())
    await message.answer("Введите фамилию:")
    await state.set_state(AddChildStates.last_name)


@dp.message(AddChildStates.last_name)
async def child_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text.strip())
    await message.answer("Введите имя родителя:")
    await state.set_state(AddChildStates.parents)


@dp.message(AddChildStates.parents)
async def child_parents(message: types.Message, state: FSMContext):
    await state.update_data(parents=message.text.strip())
    await message.answer("Введите номер телефона ребёнка:")
    await state.set_state(AddChildStates.phone_number)


@dp.message(AddChildStates.phone_number)
async def child_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone_number=message.text.strip())
    await message.answer("Введите номер телефона родителя:")
    await state.set_state(AddChildStates.phone_number_parents)


@dp.message(AddChildStates.phone_number_parents)
async def save_child_to_db(message: types.Message, state: FSMContext):
    await state.update_data(phone_number_parents=message.text.strip())
    data = await state.get_data()

    with sqlite3.connect("my_children.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO children (first_name, last_name, parents, phone_number, phone_number_parents)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['first_name'],
            data['last_name'],
            data['parents'],
            data['phone_number'],
            data['phone_number_parents']
        ))
        conn.commit()

    # Кнопка "Главное меню"
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")]
        ]
    )

    await message.answer("✅ Ребёнок успешно добавлен!", reply_markup=markup)
    await state.clear()

@dp.callback_query(F.data == 'menu')
async def return_to_main_menu(callback: types.CallbackQuery):
    await callback.message.delete()  # Убираем сообщение с кнопкой
    await send_main_menu(callback.message)
    await callback.answer()

@dp.callback_query(F.data == 'remove_child')
async def ask_for_child_id(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != user_id:
        await callback.message.answer("⛔ Только админ может удалять детей.")
        await callback.answer()
        return

    await callback.message.answer("Кого желаете удалить?\nВведите номер ребёнка (ID):")
    await state.set_state(RemoveChildStates.waiting_for_id)
    await callback.answer()

@dp.message(RemoveChildStates.waiting_for_id)
async def process_child_id_for_deletion(message: types.Message, state: FSMContext):
    menu_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")]]
    )

    if message.from_user.id != user_id:
        await message.answer("⛔ Только админ может выполнять это действие.", reply_markup=menu_markup)
        await state.clear()
        return

    child_id_text = message.text.strip()

    if not child_id_text.isdigit():
        await message.answer("❗ Пожалуйста, введите корректный числовой ID ребёнка.", reply_markup=menu_markup)
        return

    child_id = int(child_id_text)

    conn = sqlite3.connect("my_children.db")
    cursor = conn.cursor()

    try:
        print(f"Ищу ребенка с ID = {child_id}")
        cursor.execute("SELECT * FROM children WHERE id = ?", (child_id,))
        child = cursor.fetchone()
        print("Найден ребенок:", child)

        if not child:
            await message.answer(f"❌ Ребёнок с ID {child_id} не найден.", reply_markup=menu_markup)
        else:
            cursor.execute("DELETE FROM children WHERE id = ?", (child_id,))
            conn.commit()
            await message.answer(f"✅ Ребёнок с ID {child_id} успешно удалён.", reply_markup=menu_markup)
    except sqlite3.Error as e:
        await message.answer(f"Ошибка базы данных: {e}", reply_markup=menu_markup)
    finally:
        conn.close()

    await state.clear()


@dp.callback_query(F.data == 'menu')
async def return_to_main_menu(callback: types.CallbackQuery):
    await callback.message.delete()  # Убираем сообщение с кнопкой
    await send_main_menu(callback.message)
    await callback.answer()

async def main():
    init_db()  # Создаём таблицу перед запуском бота
    init_db_backup()
    ic("Запускаю бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())