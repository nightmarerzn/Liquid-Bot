import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage


# ───────── НАСТРОЙКИ ─────────
BOT_TOKEN = "8590834935:AAEEkafriz7Lm9HEG46TaNF1u9KZzmtlQf8"

ADMIN_ID = 1298938655  # 👈 ВСТАВ СВІЙ TELEGRAM ID
ADMIN_ID = 2089987846  # 👈 ВСТАВ СВІЙ TELEGRAM ID

SUPPORT_USERNAME = "liquidsupp"

PROMO_CODES = {
    "HAYPER": 10,
    "XAM": 10,
    "TEMA LOPATA": хуй,
}

logging.basicConfig(level=logging.INFO)


# ───────── FSM ─────────
class BuyForm(StatesGroup):
    aroma = State()
    promo = State()


# ───────── КЛАВІАТУРИ ─────────
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Купить", callback_data="buy")],
        [InlineKeyboardButton(text="💬 Поддержка", callback_data="support")],
    ])


def promo_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏷 Ввести промокод", callback_data="enter_promo")],
        [InlineKeyboardButton(text="➡️ Без промокода", callback_data="skip_promo")],
    ])


# ───────── ROUTER ─────────
router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Liquid Store",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    await callback.message.answer(f"💬 Поддержка: @{SUPPORT_USERNAME}")
    await callback.answer()


@router.callback_query(F.data == "buy")
async def buy(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BuyForm.aroma)
    await callback.message.answer("🌸 Введите аромат:")
    await callback.answer()


@router.message(BuyForm.aroma)
async def aroma_step(message: Message, state: FSMContext):
    await state.update_data(aroma=message.text)
    await state.set_state(BuyForm.promo)

    await message.answer(
        "Хотите ввести промокод?",
        reply_markup=promo_keyboard()
    )


@router.callback_query(F.data == "enter_promo")
async def enter_promo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BuyForm.promo)
    await callback.message.answer("Введите промокод:")
    await callback.answer()


# ───────── ОТПРАВКА АДМИНУ ─────────
async def send_admin(bot: Bot, user, aroma, promo=None, discount=None):
    text = (
        "🆕 НОВЫЙ ЗАКАЗ\n\n"
        f"👤 Пользователь: @{user.username if user.username else user.id}\n"
        f"🌸 Аромат: {aroma}\n"
    )

    if promo:
        text += f"🏷 Промокод: {promo}\n💸 Скидка: {discount}%"
    else:
        text += "🏷 Промокод: не использован"

    await bot.send_message(ADMIN_ID, text)


@router.message(BuyForm.promo)
async def check_promo(message: Message, state: FSMContext, bot: Bot):
    code = message.text.strip().upper()
    data = await state.get_data()
    aroma = data.get("aroma")

    if code in PROMO_CODES:
        discount = PROMO_CODES[code]

        await message.answer(f"✅ Скидка {discount}% применена! Информация перенаправлена менеджеру, ожидайте подтверждения заказа.")
        await state.clear()

        await send_admin(
            bot,
            message.from_user,
            aroma,
            promo=code,
            discount=discount
        )

    else:
        await message.answer(
            "❌ Неверный промокод",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➡️ Без промокода", callback_data="skip_promo")]
            ])
        )


@router.callback_query(F.data == "skip_promo")
async def skip(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    aroma = data.get("aroma")

    await state.clear()

    await callback.message.answer("✅ Заказ принят! Информация перенаправлена менеджеру, ожидайте подтверждения заказа.")

    await send_admin(
        bot,
        callback.from_user,
        aroma
    )

    await callback.answer()


# ───────── ЗАПУСК ─────────
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
