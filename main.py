from aiogram import Dispatcher, Bot, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import  MemoryStorage
from telebot.asyncio_filters import StateFilter

BOT_TOKEN = '7595069887:AAFAK9yJIk7P_YEtJf9V-oc_8dwQDGwgqMY'

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

user_dict: dict[int , dict[str | int]] = {}

class FSMFillFrom(StatesGroup):
    fill_fio = State()
    fill_num_group = State()
    fill_count = State()
    fill_date = State()


# Этот хэндлер будет срабатывать на команду /start вне состояний
# и предлагать перейти к заполнению анкеты, отправив команду /fillform




@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(
        text = 'Здравствуйте! Это чат-бот для воспитателей детского сада 380 и так далее /n/n'
               'Чтобы перейти к заполнению, нажмите /fillform'
    ) #Здесь в text будет размещен алгоритм взаимодействия с ботом и кнопка для создания отчета



# Этот хэндлер будет срабатывать на команду "/cancel" в состоянии
# по умолчанию и сообщать, что эта команда работает внутри машины состояний
@dp.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(
        text='Отменять нечего. Вы вне машины состояний\n\n'
             'Чтобы перейти к заполнению анкеты - '
             'отправьте команду /fillform'
    )

#Этот хэндлэр для сброса всех веденных данных в случае ошибки ввода
@dp.message(Command(commands=['cancel']), ~StateFilter(default_state))
async def process_cancel_command(message: Message, state: FSMContext):
    await message.answer(
        text= 'Вы сбросили введенные данные./n/n'
              'Нажмите /fillform для повторного создания отчета'
    )
    await state.clear()

#Этот хэндлэр срабатывает на fillform и переводит бота в ожидание ввода
@dp.message(Command(commands=['fillform']), StateFilter(default_state))
async def process_fillform_command(message: Message, state: FSMContext):
    await message.answer(
        text = 'Пожалуйста, введите ваше ФИО'
    )
    await state.set_state(FSMFillFrom.fill_fio)

#Этот хэндлэр сработает, если Фио введено верно
@dp.message(StateFilter(FSMFillFrom.fill_fio), F.text.isalpha())
async def process_fio_sent(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        text = 'Спасибо! Теперь введите номер группы.'
    )
    await state.set_state(FSMFillFrom.fill_num_group)

#Хэндлэр, если ФИО введено некорректно
@dp.message(StateFilter(FSMFillFrom.fill_fio))
async def warning_not_name(message: Message):
    await message.answer(
        text = 'ФИО введено некорректно. ФИО должно содержать только буквы. Введите заново./n/n'
               'Если вы хотите прервать заполнение, нажмите /cancel'
    )

#Хэндлэр на ввод номера группы
@dp.message(StateFilter(FSMFillFrom.fill_num_group), lambda x: x.text.isdigit())
async def process_numgroup_cmd(message: Message, state: FSMContext):
    await state.update_data(num=message.text)
    await message.answer(
        text = 'Спасибо!/n/n'
               'Теперь введите, пожалуйста, количество детей в группе.'
    )
    await state.set_state(FSMFillFrom.fill_count)

#Хэндлэр сработает, если номер группы введен некорректно
@dp.message(StateFilter(FSMFillFrom.fill_num_group))
async def warning_not_num(message: Message):
    await message.answer(
        text = 'Номер группы введен некорректно. Номер группы должен содержать только число./n/n'
               'Если вы хотите прервать заполнение нажмите /cancel'
    )

#Хэндлэр на ввод количества детей
@dp.message(StateFilter(FSMFillFrom.fill_count), lambda x: x.text.isdigit())
async def process_count_cmd(message: Message, state: FSMContext):
    await state.update_data(count=message.text)
    await message.answer(
        text='Отлично!/n/n'
             'Теперь введите, пожалуйста, сегодняшную дату.'
    )
    await state.set_state(FSMFillFrom.fill_date)

#Хэндлэр сработает, если количество детей введено некорректно
@dp.message(StateFilter(FSMFillFrom.fill_num_group))
async def warning_not_num(message: Message):
    await message.answer(
        text = 'Число детей введено некорректно. Сообщение должено содержать только число./n/n'
               'Если вы хотите прервать заполнение, нажмите /cancel'
    )

#Хэндлэр на ввод даты
@dp.message(StateFilter(FSMFillFrom.fill_date))
async def process_date_command(message: Message, callback: CallbackQuery, state: FSMContext):
    await state.update_data(date=message.text)
    user_dict[callback.from_user.id] = await state.get_data()
    await state.clear()
    await callback.message.edit_text(
        text='Спасибо! Ваши данные сохранены!/n/n'
             'Вы вышли из машины состояний.'
    )
    await callback.message.answer(
        text='Чтобы посмотреть данные Вашего отчета, нажмите /showdata.'
    )



# Этот хэндлер будет срабатывать на отправку команды /showdata
# и отправлять в чат данные анкеты, либо сообщение об отсутствии данных
@dp.message(Command(commands='showdata'), StateFilter(default_state))
async def process_showdata_command(message: Message):
    # Отправляем пользователю анкету, если она есть в "базе данных"
    if message.from_user.id in user_dict:
        await message.answer_(
            caption=f'ФИО: {user_dict[message.from_user.id]["name"]}\n'
                    f'Номер группы: {user_dict[message.from_user.id]["num"]}\n'
                    f'Количество детей: {user_dict[message.from_user.id]["count"]}\n'
                    f'Дата: {user_dict[message.from_user.id]["date"]}\n'
        )
    else:
        # Если анкеты пользователя в базе нет - предлагаем заполнить
        await message.answer(
            text='Вы еще не заполняли анкету. Чтобы приступить - '
            'отправьте команду /fillform'
        )






if __name__ == '__main__':
    dp.run_polling(bot)