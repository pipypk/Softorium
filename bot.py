from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command, StateFilter
import logging
import asyncio

TOKEN = "7661180334:AAERm6nhRtovpK5pfzpsW_q7Q23mGXmZe-k"
ADMIN_ID = 1687585771
admin_list = {ADMIN_ID}
TARGET_CHAT_ID = -1002270604851

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояние FSM
class ReplyState(StatesGroup):
    waiting_for_reply = State()
    waiting_for_user_id = State()  # Для удаления и разблокировки пользователей
    waiting_for_add_admin_user_id = State() # Для добавления админа
    waiting_for_remove_admin_user_id = State() # Для удаления админа
    waiting_for_block_user_id = State()  # Для блокировки пользователей
    waiting_for_unblock_user_id = State()  # Для разблокировки пользователей

class ProfileState(StatesGroup):
    waiting_for_nickname = State()  # Для псевдонима
    waiting_for_timezone = State()  # Для часового пояса

# Статистика и пользователи
user_count = 0
user_profiles = {}
message_count = 0
user_list = set()  # Для хранения уникальных пользователей
blocked_users = set()  # Для хранения заблокированных пользователей

# Клавиатуры
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Статистика")],
        [KeyboardButton(text="Управление пользователями")],
        [KeyboardButton(text="Добавить админа")],
        [KeyboardButton(text="Удалить админа")],
        [KeyboardButton(text="Список админов")],
        [KeyboardButton(text="Изменить ID чата")]
    ],
    resize_keyboard=True
)

user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Связаться с поддержкой")],
        [KeyboardButton(text="Профиль")]
    ],
    resize_keyboard=True
)

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отмена")]],
    resize_keyboard=True
)

async def get_user_profile(user_id):
    return user_profiles.get(user_id, {"nickname": None, "timezone": None})

async def save_user_profile(user_id, nickname=None, timezone=None):
    if user_id not in user_profiles:
        user_profiles[user_id] = {"nickname": None, "timezone": None}
    
    if nickname:
        user_profiles[user_id]["nickname"] = nickname
    
    if timezone:
        user_profiles[user_id]["timezone"] = timezone

# Команда /admin
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id in admin_list:
        await message.answer("Добро пожаловать в админ-панель", reply_markup=admin_keyboard)
    else:
        await message.answer("У вас нет доступа к этой команде.")

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    global user_count
    user_count += 1
    user_list.add(message.from_user.id)  # Добавляем нового пользователя в список
    if message.from_user.id in blocked_users:
        await message.answer("Вы заблокированы. Обратитесь в поддержку.")
        return
    
    # Отправляем фото и краткую информацию о боте
    photo_url = "https://i.imgur.com/3qjGlGy.png"  # Здесь замените на URL изображения
    bot_info = (
        "✊Добрый день!\n\n📌Я — бот Софториум\n"
        "Я помогу вам связаться с нашей командой и получать ответы на ваши вопросы.🔎\n"
        "🔥Если у вас возникнут проблемы или вопросы, не стесняйтесь обращаться к нам!"
    )
    help = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="FAQ", callback_data="faq")],
                [InlineKeyboardButton(text="TG канал", url="https://t.me/softoriumpro")]
            ]
        )


    await message.answer_photo(photo_url, caption=bot_info, reply_markup=user_keyboard)
    await message.answer("Помощь по боту", reply_markup=help)

@dp.callback_query(F.data.startswith("faq"))
async def change_username(callback: types.CallbackQuery, state: FSMContext):
    photo_url = "https://i.imgur.com/9kzbIpO.png"  # Здесь замените на URL изображения
    bot_info = (
        "🔎<b>Является ли переписка с разработчиком анонимной?</b>\n"
        " — Конечно. Мы пытаемся достичь максимальной анонимности. При обращении к разработчикам вы можете изменить свое имя в профиле на любое другое\n"
        "🔎<b>Сколько ждать ответа от разработчика?</b>\n"
        " — В обычное время ответ поступает в течении пары минут. В загруженное время до пары часов\n"
    )



    await callback.message.answer_photo(photo_url, caption=bot_info, reply_markup=user_keyboard)



# Команда "Профиль"
@dp.message(F.text == "Профиль")
async def profile(message: types.Message):
    user_id = message.from_user.id
    
    # Проверка наличия данных о пользователе
    user_profile = await get_user_profile(user_id)

    profile_message = (
        f"Ваш профиль:\n"
        f"Псевдоним: {user_profile['nickname'] if user_profile['nickname'] else 'Не установлен'}\n"
        f"Часовой пояс: {user_profile['timezone'] if user_profile['timezone'] else 'Не установлен'}\n"
    )

    profile = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Изменить псевдоним", callback_data="change_username")],
                [InlineKeyboardButton(text="Изменить часовой пояс", callback_data="change_hours")]
            ]
        )

    photo_url = "https://imgur.com/kwPz4k6"
    await message.answer_photo(photo_url, caption=profile_message, reply_markup=user_keyboard)
    await message.answer("Вы можете изменить эти данные, нажав на кнопку ниже.", reply_markup=profile)

# Нажатие на "Изменить псевдоним"
@dp.callback_query(F.data.startswith("change_username"))
async def change_username(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите новый псевдоним:")
    await state.set_state(ProfileState.waiting_for_nickname)

# Обработка введенного псевдонима
@dp.message(StateFilter(ProfileState.waiting_for_nickname))
async def set_nickname(message: types.Message, state: FSMContext):
    new_nickname = message.text.strip()
    
    if new_nickname:
        # Сохраняем новый псевдоним в базе данных пользователя
        await save_user_profile(message.from_user.id, nickname=new_nickname)
        await message.answer(f"Ваш псевдоним был обновлен на: {new_nickname}")
    else:
        await message.answer("Псевдоним не может быть пустым.")
    
    await state.clear()  # Завершаем состояние

# Нажатие на "Изменить часовой пояс"
@dp.callback_query(F.data.startswith("change_hours"))
async def change_hours(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите ваш часовой пояс (например, UTC+3):")
    await state.set_state(ProfileState.waiting_for_timezone)

# Обработка введенного часового пояса
@dp.message(StateFilter(ProfileState.waiting_for_timezone))
async def set_timezone(message: types.Message, state: FSMContext):
    new_timezone = message.text.strip()
    
    if new_timezone:
        # Сохраняем новый часовой пояс в базе данных пользователя
        await save_user_profile(message.from_user.id, timezone=new_timezone)
        await message.answer(f"Ваш часовой пояс был обновлен на: {new_timezone}")
    else:
        await message.answer("Часовой пояс не может быть пустым.")
    
    await state.clear()  # Завершаем состояние

# Обработка кнопки "Статистика"
@dp.message(F.text == "Статистика")
async def show_statistics(message: types.Message):
    if message.from_user.id in admin_list:
        stats_message = (
            f"Статистика бота:\n"
            f"Количество пользователей: {user_count}\n"
            f"Количество сообщений: {message_count}\n"
        )
        photo_url = "https://imgur.com/NR69JPA"
        await message.answer_photo(photo_url, caption=stats_message, reply_markup=user_keyboard)
    else:
        await message.answer("У вас нет доступа к этой команде.")

# Обработка кнопки "Управление пользователями"
@dp.message(F.text == "Управление пользователями")
async def manage_users(message: types.Message):
    if message.from_user.id in admin_list:
        user_management_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Просмотр списка пользователей", callback_data="view_users")],
                [InlineKeyboardButton(text="Просмотр заблокированных пользователей", callback_data="view_blocked_users")],
                [InlineKeyboardButton(text="Заблокировать пользователя", callback_data="block_user")],
                [InlineKeyboardButton(text="Разблокировать пользователя", callback_data="unblock_user")],
                [InlineKeyboardButton(text="Удалить пользователя", callback_data="delete_user")]
            ]
        )
        photo_url = "https://imgur.com/O8cki0w"
        await message.answer_photo(photo_url, reply_markup=user_keyboard)
        await message.answer("Выберите действие:", reply_markup=user_management_keyboard)
    else:
        await message.answer("У вас нет доступа к этой команде.")

# Просмотр списка пользователей
@dp.callback_query(F.data == "view_users")
async def view_users(callback: types.CallbackQuery):
    if callback.from_user.id in admin_list:
        users_list_text = "Список пользователей:\n"
        for user_id in user_list:
            users_list_text += f"User_{user_id}\n"
        await callback.message.answer(users_list_text)
    await callback.answer()

# Просмотр списка заблокированных пользователей
@dp.callback_query(F.data == "view_blocked_users")
async def view_blocked_users(callback: types.CallbackQuery):
    if callback.from_user.id in admin_list:
        if blocked_users:
            blocked_users_text = "Список заблокированных пользователей:\n"
            for user_id in blocked_users:
                blocked_users_text += f"User_{user_id}\n"
            await callback.message.answer(blocked_users_text)
        else:
            await callback.message.answer("Список заблокированных пользователей пуст.")
    await callback.answer()

# Удаление пользователя
@dp.callback_query(F.data == "delete_user")
async def delete_user(callback: types.CallbackQuery):
    await callback.message.answer("Введите ID пользователя для удаления:")

    # Ожидаем ID пользователя
    await dp.current_state().set_state(ReplyState.waiting_for_user_id)

# Блокировка пользователя
@dp.callback_query(F.data == "block_user")
async def block_user(callback: types.CallbackQuery):
    await callback.message.answer("Введите ID пользователя для блокировки:")

    # Ожидаем ID пользователя
    await dp.current_state().set_state(ReplyState.waiting_for_block_user_id)

# Разблокировка пользователя
@dp.callback_query(F.data == "unblock_user")
async def unblock_user(callback: types.CallbackQuery):
    await callback.message.answer("Введите ID пользователя для разблокировки:")

    # Ожидаем ID пользователя
    await dp.current_state().set_state(ReplyState.waiting_for_unblock_user_id)

# Обработка введенного ID пользователя для удаления
@dp.message(StateFilter(ReplyState.waiting_for_user_id))
async def delete_user_by_id(message: types.Message):
    user_id_to_delete = message.text.strip()
    
    if user_id_to_delete.isdigit():
        user_id_to_delete = int(user_id_to_delete)
        if user_id_to_delete in user_list:
            user_list.remove(user_id_to_delete)
            await message.answer(f"Пользователь с ID {user_id_to_delete} был удален.")
        else:
            await message.answer(f"Пользователь с ID {user_id_to_delete} не найден.")
    else:
        await message.answer("Введите правильный ID пользователя.")

    await dp.current_state().clear()  # Завершаем процесс удаления

# Обработка введенного ID пользователя для блокировки
@dp.message(StateFilter(ReplyState.waiting_for_block_user_id))
async def block_user_by_id(message: types.Message):
    user_id_to_block = message.text.strip()

    if user_id_to_block.isdigit():
        user_id_to_block = int(user_id_to_block)
        if user_id_to_block in user_list:
            blocked_users.add(user_id_to_block)
            await message.answer(f"Пользователь с ID {user_id_to_block} был заблокирован.")
        else:
            await message.answer(f"Пользователь с ID {user_id_to_block} не найден.")
    else:
        await message.answer("Введите правильный ID пользователя.")

    await dp.current_state().clear()  # Завершаем процесс блокировки

# Обработка введенного ID пользователя для разблокировки
@dp.message(StateFilter(ReplyState.waiting_for_unblock_user_id))
async def unblock_user_by_id(message: types.Message):
    user_id_to_unblock = message.text.strip()

    if user_id_to_unblock.isdigit():
        user_id_to_unblock = int(user_id_to_unblock)
        if user_id_to_unblock in blocked_users:
            blocked_users.remove(user_id_to_unblock)
            await message.answer(f"Пользователь с ID {user_id_to_unblock} был разблокирован.")
        else:
            await message.answer(f"Пользователь с ID {user_id_to_unblock} не найден в списке заблокированных.")
    else:
        await message.answer("Введите правильный ID пользователя.")

    await dp.current_state().clear()  # Завершаем процесс разблокировки

# Обработка кнопки "Добавить админа"
@dp.message(F.text == "Добавить админа")
async def add_admin(message: types.Message, state: FSMContext):
    if message.from_user.id in admin_list:
        await message.answer("Введите ID пользователя, которого хотите добавить в администраторы:")
        await state.set_state(ReplyState.waiting_for_add_admin_user_id)
    else:
        await message.answer("У вас нет доступа к этой команде.")

# Обработка введенного ID для добавления админа
@dp.message(StateFilter(ReplyState.waiting_for_add_admin_user_id))
async def add_admin_by_id(message: types.Message, state: FSMContext):
    new_admin_id = message.text.strip()

    if new_admin_id.isdigit():
        new_admin_id = int(new_admin_id)
        if new_admin_id not in admin_list:
            admin_list.add(new_admin_id)
            await message.answer(f"Пользователь с ID {new_admin_id} был добавлен в администраторы.")
            
            # Отправляем сообщение пользователю, что он стал администратором
            try:
                await bot.send_message(new_admin_id, "Поздравляю! Вы стали администратором.")
            except Exception as e:
                await message.answer(f"Ошибка при отправке сообщения пользователю: {e}")
        else:
            await message.answer(f"Пользователь с ID {new_admin_id} уже является администратором.")
    else:
        await message.answer("Введите правильный ID пользователя.")

    await state.clear()  # Завершаем процесс добавления админа

# Обработка кнопки "Удалить админа"
@dp.message(F.text == "Удалить админа")
async def remove_admin(message: types.Message, state: FSMContext):
    if message.from_user.id in admin_list:
        await message.answer("Введите ID пользователя, которого хотите удалить из администраторов:")
        await state.set_state(ReplyState.waiting_for_remove_admin_user_id)
    else:
        await message.answer("У вас нет доступа к этой команде.")

# Обработка введенного ID для удаления админа
@dp.message(StateFilter(ReplyState.waiting_for_remove_admin_user_id))
async def remove_admin_by_id(message: types.Message, state: FSMContext):
    admin_id_to_remove = message.text.strip()

    if admin_id_to_remove.isdigit():
        admin_id_to_remove = int(admin_id_to_remove)
        if admin_id_to_remove in admin_list:
            admin_list.remove(admin_id_to_remove)
            await message.answer(f"Пользователь с ID {admin_id_to_remove} был удален из администраторов.")
            
            # Отправляем сообщение пользователю, что его удалили из администраторов
            try:
                await bot.send_message(admin_id_to_remove, "Вы больше не являетесь администратором.")
            except Exception as e:
                await message.answer(f"Ошибка при отправке сообщения пользователю: {e}")
        else:
            await message.answer(f"Пользователь с ID {admin_id_to_remove} не является администратором.")
    else:
        await message.answer("Введите правильный ID пользователя.")

    await state.clear()  # Завершаем процесс удаления админа

# Обработка кнопки "Список админов"
@dp.message(F.text == "Список админов")
async def list_admins(message: types.Message):
    if message.from_user.id in admin_list:
        if admin_list:
            admins_list_text = "Список администраторов:\n"
            for admin_id in admin_list:
                admins_list_text += f"Admin_{admin_id}\n"
            await message.answer(admins_list_text)
        else:
            await message.answer("В данный момент нет администраторов.")
    else:
        await message.answer("У вас нет доступа к этой команде.")

# "Связаться с поддержкой"
@dp.message(F.text == "Связаться с поддержкой")
async def contact_support(message: types.Message):
    await message.answer("Напишите ваше сообщение, и оно будет отправлено разработчикам.")

# Обработчик фото
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    global message_count
    message_count += 1
    
    if message.from_user.id in blocked_users:
        await message.answer("Вы заблокированы. Обратитесь в поддержку.")
        return
    
    user_profile = await get_user_profile(message.from_user.id)
    nickname = user_profile["nickname"] if user_profile["nickname"] else f"User_{message.from_user.id}"
    
    forward_text = f"<b>{nickname}:</b> отправляет фото."
    
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Ответить", callback_data=f"reply_{message.from_user.id}")
        ]]
    )

    await bot.send_photo(chat_id=TARGET_CHAT_ID, photo=message.photo[-1].file_id, caption=forward_text, reply_markup=reply_markup)

# Обработчик видео
@dp.message(F.video)
async def handle_video(message: types.Message):

    global message_count
    message_count += 1
    
    if message.from_user.id in blocked_users:
        await message.answer("Вы заблокированы. Обратитесь в поддержку.")
        return
    
    user_profile = await get_user_profile(message.from_user.id)
    nickname = user_profile["nickname"] if user_profile["nickname"] else f"User_{message.from_user.id}"
    
    forward_text = f"<b>{nickname}:</b> отправляет видео"
    
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Ответить", callback_data=f"reply_{message.from_user.id}")
        ]]
    )

    await bot.send_video(chat_id=TARGET_CHAT_ID, video=message.video.file_id, caption=forward_text, reply_markup=reply_markup)

# Обработчик документов (файлов)
@dp.message(F.document)
async def handle_document(message: types.Message):

    global message_count
    message_count += 1
    
    if message.from_user.id in blocked_users:
        await message.answer("Вы заблокированы. Обратитесь в поддержку.")
        return
    
    user_profile = await get_user_profile(message.from_user.id)
    nickname = user_profile["nickname"] if user_profile["nickname"] else f"User_{message.from_user.id}"
    
    forward_text = f"<b>{nickname}:</b> отправляет файл."
    
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Ответить", callback_data=f"reply_{message.from_user.id}")
        ]]
    )

    await bot.send_document(chat_id=TARGET_CHAT_ID, document=message.document.file_id, caption=forward_text, reply_markup=reply_markup)

# Отправка сообщений в чат поддержки
@dp.message(F.text & ~F.reply_to_message)
async def forward_to_admins(message: types.Message):
    global message_count
    message_count += 1
    
    if message.from_user.id in blocked_users:
        await message.answer("Вы заблокированы. Обратитесь в поддержку.")
        return
    
    user_profile = await get_user_profile(message.from_user.id)
    nickname = user_profile["nickname"] if user_profile["nickname"] else f"User_{message.from_user.id}"
    
    forward_text = f"<b>{nickname}:</b> {message.text}"
    
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Ответить", callback_data=f"reply_{message.from_user.id}")
        ]]
    )

    await bot.send_message(chat_id=TARGET_CHAT_ID, text=forward_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

# Нажатие на "Ответить"
@dp.callback_query(F.data.startswith("reply_"))
async def reply_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[1])
    await state.update_data(user_id=user_id)

    await callback.message.answer(
        f"Введите ответ для пользователя {user_id}:",
        reply_markup=cancel_keyboard
    )

    await state.set_state(ReplyState.waiting_for_reply)

# Обработка сообщения администратора (ответ пользователю)
@dp.message(ReplyState.waiting_for_reply)
async def reply_to_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")

    # Проверка текста "Отмена"
    if message.text == "Отмена":
        await message.answer("Отмена ответа.", reply_markup=admin_keyboard)  # Кнопка "Отмена" убирается
        await state.clear()  # Завершаем состояние
        return

    if user_id:
        try:
            await bot.send_message(user_id, f"<b>Ответ от поддержки:</b>\n{message.text}", parse_mode=ParseMode.HTML)
            await message.answer("Сообщение отправлено пользователю.", reply_markup=admin_keyboard)
        except Exception as e:
            await message.answer(f"Ошибка при отправке сообщения: {e}", reply_markup=admin_keyboard)
        await state.clear()  # Завершаем состояние после отправки сообщения
    else:
        await message.answer("Ошибка: не найден ID пользователя.", reply_markup=admin_keyboard)
        await state.clear()  # Завершаем состояние


# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
