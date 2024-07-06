import telebot

bot = telebot.TeleBot('6648336138:AAGnepVO0YltsPkym3Dy74McpEoyk7jVjHg')

from telebot import types
from vacancyDAO import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

selectedCity = ''
selectedTitle = ''
selectedExpirience = ''

CITY_BTN = {
    '1': 'Москва',
    '2': 'Санкт-Петербург'
}

TITLE_BTN = {
   '1': 'разработчик bi',
   '2': 'BI Developer',
   '3': 'Machine Learning Engineer',
   '4': 'Business Development Manager'
}

EXP_BTN = {
   '1': 'Без опыта',
   '2': 'От 1 года до 3 лет',
   '3': 'От 3 до 6 лет'
}

@bot.message_handler(commands=['start'])
def startBot(message):
  global selectedCity
  global selectedTitle
  global selectedExpirience
  selectedCity = ''
  selectedTitle = ''
  selectedExpirience = ''

  first_mess = f"<b>{message.from_user.first_name} {message.from_user.last_name}</b>, привет!\nЭтот бот поможет найти тебе подходящую вакансию.Приступим?"
  markup = types.InlineKeyboardMarkup()
  button_yes = types.InlineKeyboardButton(text = 'Да', callback_data='yes')
  markup.add(button_yes)
  bot.send_message(message.chat.id, first_mess, parse_mode='html', reply_markup=markup)

@bot.callback_query_handler(func=lambda call:True)
def response(function_call):
   logging.info("сообщение от бота: " + function_call.message.text)
   if function_call.message:
      btnParams = function_call.data.split(':')
      btnPrefix = btnParams[0] if len(btnParams) > 0 else ""
      btnId = btnParams[1] if len(btnParams) > 1 else ""
      logging.info("btnPrefix: " + btnPrefix + ", btnId: " + str(btnId))

      if btnPrefix == "yes":
        onYes(function_call)
      elif btnPrefix == "city":
        global selectedCity
        selectedCity = CITY_BTN.get(btnId) 
        onVacancy(function_call)
      elif btnPrefix == "vacancy":
        global selectedTitle
        selectedTitle = TITLE_BTN.get(btnId) 
        onExp(function_call)
      elif btnPrefix == "exp":
        global selectedExpirience
        selectedExpirience = EXP_BTN.get(btnId) 
        onGetVacancies(function_call)

@bot.chosen_inline_handler(func=lambda call:True)
def response2(function_call):
   logging.info("chosen: " + function_call.query)

def onYes(function_call):
   second_mess = "Выбери свой город"
   keyboard = types.InlineKeyboardMarkup()
   for buttonId, buttonText in CITY_BTN.items():
      key = types.InlineKeyboardButton(text = buttonText, callback_data = f'city:{buttonId}')
      keyboard.add(key)

   bot.send_message(function_call.message.chat.id, second_mess, reply_markup=keyboard)
   bot.answer_callback_query(function_call.id)                  

def onVacancy(call):
    three_mess = "Выбери специальность "
    keyboard = types.InlineKeyboardMarkup()
    for buttonId, buttonText in TITLE_BTN.items():
      key = types.InlineKeyboardButton(text = buttonText, callback_data = f'vacancy:{buttonId}')
      keyboard.add(key)

    bot.send_message(call.message.chat.id, three_mess, reply_markup=keyboard)
    bot.answer_callback_query(call.id)

def onExp(call):
    four_mess = "Выбери опыт работы "
    keyboard = types.InlineKeyboardMarkup()
    for buttonId, buttonText in EXP_BTN.items():
      key = types.InlineKeyboardButton(text = buttonText, callback_data = f'exp:{buttonId}')
      keyboard.add(key)

    bot.send_message(call.message.chat.id, four_mess, reply_markup=keyboard)
    bot.answer_callback_query(call.id)
    
def onGetVacancies(call):
    message = ''.join(tuple_to_list(getVacancies(selectedCity, selectedTitle, selectedExpirience)))
    if len(message) <= 0:
       message = "Для заданных условий поиска вакансии не найдены" 
    keyboard = types.InlineKeyboardMarkup()
    key_get = types.InlineKeyboardButton(text='Найти', callback_data='getVacancies')
    keyboard.add(key_get)
    if len(message) > 4096:
       for x in range(0, len(message), 4096):
          bot.send_message(call.message.chat.id, message[x:x+4096], reply_markup=keyboard)
    else:
       bot.send_message(call.message.chat.id, message, reply_markup=keyboard)
    bot.answer_callback_query(call.id)

def tuple_to_list(t):
    new_list = []
    for row in t:
        row_list = []
        for col in row:
           row_list.append(str(col))
        row_list.append('\n')
        new_list.append(''.join(row_list))

    logging.info(new_list)
    return new_list

bot.polling(none_stop=True, interval=0)