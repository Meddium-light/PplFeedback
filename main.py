import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = os.getenv("BOT_TOKEN")
MOD_IDS = list(map(int, os.getenv("MOD_IDS", "").split(",")))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class AppealStates(StatesGroup):
    step1 = State()
    step2 = State()
    step3 = State()
    step4 = State()
    step5 = State()

class FeedbackStates(StatesGroup):
    step1 = State()
    step2 = State()
    step3 = State()
    step4 = State()

start_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="⚠️Апелляция", callback_data="appeal"),
        InlineKeyboardButton(text="📝Отзыв", callback_data="feedback")
    ]
])

back_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👈Назад", callback_data="back")]
])

done_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👍Готово", callback_data="done")]
])

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Привет! Ты попал в бота-предложку <b><i><u>PplFeedBack</u></i></b> (@pplfeedback)\n\nЗдесь ты можешь оставить отзыв о работяге или обжаловать несправедливый по твоему мнению отзыв о тебе, используя кнопки <b>Апелляция</b> и <b>Отзыв</b>.\n\nВсе пожелания и отзывы касаемо бота и развития функционала можете предлагать в тг <b>@jophonk</b>",
        parse_mode="HTML",
        reply_markup=start_buttons
    )

@dp.callback_query(F.data == "appeal")
async def appeal_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "Вы выбрали ⚠️<b>Апелляция</b>\nПришлите ссылку на пост",
        parse_mode="HTML",
        reply_markup=back_button
    )
    await state.set_state(AppealStates.step1)

@dp.callback_query(F.data == "feedback")
async def feedback_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "Вы выбрали 📝<b>Отзыв</b>\n\nВведите ник вашего работника",
        parse_mode="HTML",
        reply_markup=back_button
    )
    await state.set_state(FeedbackStates.step1)

@dp.message(AppealStates.step1)
async def appeal_step1(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пришлите ссылку текстом")
        return
    await state.update_data(post_link=message.text)
    await message.answer("Введите ваш ник", reply_markup=back_button)
    await state.set_state(AppealStates.step2)

@dp.message(AppealStates.step2)
async def appeal_step2(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пришли ник текстом")
        return
    await state.update_data(user_nick=message.text)
    await message.answer("Введите ник вашего заказчика(-ов)", reply_markup=back_button)
    await state.set_state(AppealStates.step3)

@dp.message(AppealStates.step3)
async def appeal_step3(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Текстом напиши ники заказчиков")
        return
    await state.update_data(client_nick=message.text)
    await message.answer(
        "Опишите ситуацию с вашей стороны максимально подробно. Почему вы считаете отзыв необоснованным. Покажите нам ситуацию с другой стороны (скриншоты-пруфы можно прикрепить на следующем шаге)",
        reply_markup=back_button
    )
    await state.set_state(AppealStates.step4)

@dp.message(AppealStates.step4)
async def appeal_step4(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Без твоего описания ситуации, мы ничем помочь не можем")
        return
    await state.update_data(description=message.text)
    await state.update_data(screenshots=[])
    await state.update_data(appeal_sent=False)
    await message.answer(
        "Отправьте скриншоты-пруфы, подтверждающие ваши слова <b>(до 10)</b>.\nНажмите <b>Готово</b>, когда закончите",
        parse_mode="HTML",
        reply_markup=done_button
    )
    await state.set_state(AppealStates.step5)

@dp.message(AppealStates.step5)
async def appeal_step5(message: Message, state: FSMContext):
    data = await state.get_data()

    if data.get("appeal_sent"):  
        return

    screenshots = data.get("screenshots", [])

    if message.photo:
        largest_photo = message.photo[-1].file_id
        if largest_photo not in screenshots:
            screenshots.append(largest_photo)
        if len(screenshots) > 10:
            screenshots = screenshots[:10]
        await state.update_data(screenshots=screenshots)

    if len(screenshots) == 10:
        await state.update_data(appeal_sent=True)
        await send_appeal_once(state, message, appeal_type="Апелляция")

@dp.message(FeedbackStates.step1)
async def feedback_step1(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Введите текст")
        return
    await state.update_data(builder_nick=message.text)
    await message.answer("Введите ваш ник", reply_markup=back_button)
    await state.set_state(FeedbackStates.step2)

@dp.message(FeedbackStates.step2)
async def feedback_step2(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Введите текст")
        return
    await state.update_data(user_nick=message.text)
    await message.answer(
        "Оставьте подробный отзыв о работнике и проделанной им работе. Опишите ваш опыт взаимодействия, соблюдения сроков, поставленных задач. Желательно указать какой был объем работы, какая оплата была согласована, какую оценку вы бы поставили работнику по 10-бальной шкале (Картинки и скриншоты можно будет прикрепить на следующем этапе)",
        reply_markup=back_button
    )
    await state.set_state(FeedbackStates.step3)

@dp.message(FeedbackStates.step3)
async def feedback_step3(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Введите текст")
        return
    await state.update_data(description=message.text)
    await state.update_data(screenshots=[])
    await state.update_data(feedback_sent=False)
    await message.answer(
        "Отправьте картинки и скриншоты, которые мы сможем приложить к посту <b>(до 10)</b>.\nНажмите <b>Готово</b>, когда закончите",
        parse_mode="HTML",
        reply_markup=done_button
    )
    await state.set_state(FeedbackStates.step4)

@dp.message(FeedbackStates.step4)
async def feedback_step4(message: Message, state: FSMContext):
    data = await state.get_data()

    if data.get("feedback_sent"):
        return

    screenshots = data.get("screenshots", [])

    if message.photo:
        largest_photo = message.photo[-1].file_id
        if largest_photo not in screenshots:
            screenshots.append(largest_photo)
        if len(screenshots) > 10:
            screenshots = screenshots[:10]
        await state.update_data(screenshots=screenshots)

    if len(screenshots) == 10:
        await state.update_data(feedback_sent=True)
        await send_feedback_once(state, message)

@dp.callback_query(F.data == "done")
async def done_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if 'appeal_sent' in data and not data.get("appeal_sent"):
        screenshots = data.get("screenshots", [])
        if screenshots:
            await state.update_data(appeal_sent=True)
            await send_appeal_once(state, callback.message, appeal_type="Апелляция")
        return
    if 'feedback_sent' in data and not data.get("feedback_sent"):
        screenshots = data.get("screenshots", [])
        if screenshots:
            await state.update_data(feedback_sent=True)
            await send_feedback_once(state, callback.message)
        return
    await callback.answer("Ты уже отправил форму, дурачок")

async def send_appeal_once(state: FSMContext, message_obj, appeal_type="Апелляция"):
    data = await state.get_data()
    if data.get("appeal_sent") is False:
        await state.update_data(appeal_sent=True)

    post_link = data.get("post_link", "")
    user_nick = data.get("user_nick", "")
    client_nick = data.get("client_nick", "")
    description = data.get("description", "")
    screenshots = data.get("screenshots", [])

    final_text = (
        f"{appeal_type}\n\n"
        f"Ссылка на пост для апелляции:\n{post_link}\n\n"
        f"Ник человека подающего апелляцию:{user_nick}\n"
        f"Ник заказчика(-ов): {client_nick}\n\n"
        f"{description}"
    )

    for mod_id in MOD_IDS:
        try:
            if screenshots:
                media = []
                for i, file_id in enumerate(screenshots):
                    if i == 0:
                        media.append(InputMediaPhoto(media=file_id, caption=final_text))
                    else:
                        media.append(InputMediaPhoto(media=file_id))
                await bot.send_media_group(mod_id, media)
            else:
                await bot.send_message(mod_id, final_text)
        except Exception as e:
            print(f"Ошибка при отправке модератору {mod_id}: {e}")

    await message_obj.answer(f"{appeal_type} отправлена модераторам ✅")
    await message_obj.answer(
        "Привет! Ты попал в бота-предложку <b><i><u>PplFeedBack</u></i></b> (@pplfeedback)\n\nЗдесь ты можешь оставить отзыв о работяге или обжаловать несправедливый по твоему мнению отзыв о тебе, используя кнопки <b>Апелляция</b> и <b>Отзыв</b>.\n\nВсе пожелания и отзывы касаемо бота и развития функционала можете предлагать в тг <b>@jophonk</b>",
        parse_mode="HTML",
        reply_markup=start_buttons
    )
    await state.clear()

async def send_feedback_once(state: FSMContext, message_obj):
    data = await state.get_data()
    if data.get("feedback_sent") is False:
        await state.update_data(feedback_sent=True)

    builder_nick = data.get("builder_nick", "")
    user_nick = data.get("user_nick", "")
    description = data.get("description", "")
    screenshots = data.get("screenshots", [])

    final_text = (
        f"Отзыв\n\n"
        f"Ник строителя: {builder_nick}\n"
        f"Ник человека отправившего отзыв: {user_nick}\n\n"
        f"{description}"
    )

    for mod_id in MOD_IDS:
        try:
            if screenshots:
                media = []
                for i, file_id in enumerate(screenshots):
                    if i == 0:
                        media.append(InputMediaPhoto(media=file_id, caption=final_text))
                    else:
                        media.append(InputMediaPhoto(media=file_id))
                await bot.send_media_group(mod_id, media)
            else:
                await bot.send_message(mod_id, final_text)
        except Exception as e:
            print(f"Ошибка при отправке модератору {mod_id}: {e}")

    await message_obj.answer("Отзыв отправлен модераторам ✅")
    await message_obj.answer(
        "Привет! Ты попал в бота-предложку <b><i><u>PplFeedBack</u></i></b> (@pplfeedback)\n\nЗдесь ты можешь оставить отзыв о работяге или обжаловать несправедливый по твоему мнению отзыв о тебе, используя кнопки <b>Апелляция</b> и <b>Отзыв</b>.\n\nВсе пожелания и отзывы касаемо бота и развития функционала можете предлагать в тг <b>@jophonk</b>",
        parse_mode="HTML",
        reply_markup=start_buttons
    )
    await state.clear()

@dp.callback_query(F.data == "back")
async def go_back(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "Привет! Ты попал в бота-предложку <b><i><u>PplFeedBack</u></i></b> (@pplfeedback)\n\nЗдесь ты можешь оставить отзыв о работяге или обжаловать несправедливый по твоему мнению отзыв о тебе, используя кнопки <b>Апелляция</b> и <b>Отзыв</b>.\n\nВсе пожелания и отзывы касаемо бота и развития функционала можете предлагать в тг <b>@jophonk</b>",
        parse_mode="HTML",
        reply_markup=start_buttons
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
