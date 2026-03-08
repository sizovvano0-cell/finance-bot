from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from datetime import datetime
import database as db
import os

BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

INCOME_CATEGORIES = ["💼 Зарплата", "💰 Подработка", "🎁 Подарок", "📈 Инвестиции", "💵 Другое"]
EXPENSE_CATEGORIES = ["🍔 Еда", "🏠 Жильё", "🚗 Транспорт", "👕 Одежда", "💊 Здоровье", 
                     "🎮 Развлечения", "📚 Образование", "💳 Другое"]

class AddIncome(StatesGroup):
    amount = State()
    category = State()
    description = State()

class AddExpense(StatesGroup):
    amount = State()
    category = State()
    description = State()

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить доход"), KeyboardButton(text="➖ Добавить расход")],
            [KeyboardButton(text="📊 Отчёт за месяц"), KeyboardButton(text="📝 История")],
            [KeyboardButton(text="🗑 Удалить последнюю"), KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )

def category_keyboard(categories):
    buttons = [[KeyboardButton(text=cat)] for cat in categories]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(CommandStart())
async def start(message: types.Message):
    await db.add_user(message.from_user.id, message.from_user.username or "")
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я помогу вести учёт твоих финансов.\n"
        "Используй кнопки ниже:",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "❓ Помощь")
async def help_cmd(message: types.Message):
    await message.answer(
        "📖 <b>Как пользоваться:</b>\n\n"
        "➕ <b>Добавить доход</b> — записать поступление денег\n"
        "➖ <b>Добавить расход</b> — записать трату\n"
        "📊 <b>Отчёт за месяц</b> — статистика по категориям\n"
        "📝 <b>История</b> — последние 10 операций\n"
        "🗑 <b>Удалить последнюю</b> — отменить ошибочную запись",
        parse_mode="HTML"
    )

@dp.message(F.text == "➕ Добавить доход")
async def add_income_start(message: types.Message, state: FSMContext):
    await state.set_state(AddIncome.amount)
    await message.answer(
        "💰 Введите сумму дохода:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )

@dp.message(AddIncome.amount)
async def add_income_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=main_keyboard())
        return
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError
        await state.update_data(amount=amount)
        await state.set_state(AddIncome.category)
        await message.answer("Выберите категорию:", reply_markup=category_keyboard(INCOME_CATEGORIES))
    except ValueError:
        await message.answer("❌ Введите корректную сумму")

@dp.message(AddIncome.category)
async def add_income_category(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=main_keyboard())
        return
    await state.update_data(category=message.text)
    await state.set_state(AddIncome.description)
    await message.answer(
        "Добавьте описание (или '-' чтобы пропустить):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="-")], [KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )

@dp.message(AddIncome.description)
async def add_income_description(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=main_keyboard())
        return
    data = await state.get_data()
    description = "" if message.text == "-" else message.text
    await db.add_transaction(message.from_user.id, 'income', data['amount'], data['category'], description)
    await state.clear()
    await message.answer(
        f"✅ Доход добавлен!\n\n💰 Сумма: {data['amount']} ₽\n"
        f"📁 Категория: {data['category']}\n📝 Описание: {description or '-'}",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "➖ Добавить расход")
async def add_expense_start(message: types.Message, state: FSMContext):
    await state.set_state(AddExpense.amount)
    await message.answer(
        "💸 Введите сумму расхода:",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)
    )

@dp.message(AddExpense.amount)
async def add_expense_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=main_keyboard())
        return
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError
        await state.update_data(amount=amount)
        await state.set_state(AddExpense.category)
        await message.answer("Выберите категорию:", reply_markup=category_keyboard(EXPENSE_CATEGORIES))
    except ValueError:
        await 
