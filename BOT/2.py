import pandas as pd
import os
import telebot
from telebot import types
df = pd.read_excel('database.xlsx')
# Создаем словарь для хранения выбранных жанров пользователей
user_genres = {}
user_movie_info = {}
bot = telebot.TeleBot("") #Записать API тг бота
@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    keyboard.add(*[types.KeyboardButton(genre) for genre in ['Комедия', 'Драма', 'Боевик', 'Фантастика', 'Мелодрама', 'Триллер', 'Ужасы', 'Фэнтези']])
    keyboard.add(types.KeyboardButton('Рекомендовать'))  # Добавляем кнопку "Рекомендовать"
    bot.send_message(message.chat.id, '🎬🎬🎬🎬🎬🎬🎬\n 1)Выберите жанры (повторное нажатие на жанр удаляет его из списка) \n 🎞📽🎥😻🙀😺 \n 2)Нажмите кнопку "Рекомендовать" \n ✅✅✅✅✅✅ \n Если нажать на "Рекомендовать" без выбора жанров, то он выведет случайный фильм', reply_markup=keyboard)
@bot.message_handler(func=lambda message: message.text in ['Комедия', 'Драма', 'Боевик', 'Фантастика', 'Мелодрама', 'Триллер', 'Ужасы', 'Фэнтези'])
def handle_genre(message):
    genre = message.text
    user_id = message.from_user.id
    # Проверяем, выбран ли уже данный жанр пользователем
    if genre in user_genres.get(user_id, []):
        # Если жанр уже выбран, удаляем его из выбора пользователя
        user_genres[user_id].remove(genre)
        bot.send_message(message.chat.id, f"Жанр {genre} удален из выбора.")
    else:
        # Если жанр еще не выбран, добавляем его в выбор пользователя
        user_genres.setdefault(user_id, []).append(genre)
        bot.send_message(message.chat.id, f"Жанр {genre} добавлен в выбор.")
    # Выводим список выбранных жанров
    selected_genres = user_genres.get(user_id, [])
    if selected_genres:
        bot.send_message(message.chat.id, f"Выбранные жанры: {', '.join(selected_genres)}")
@bot.message_handler(func=lambda message: message.text == 'Рекомендовать')
def recommend_movie(message):
    user_id = message.from_user.id
    genres = [genre.lower() for genre in user_genres.get(user_id, [])]  # преобразуем выбранные жанры в нижний регистр
    if genres:
        # Используем функцию all для проверки, что все выбранные жанры присутствуют в списке жанров фильма
        recommendations = df[df['genre'].apply(lambda x: all(genre in x.lower().split(',') for genre in genres))]
        if not recommendations.empty:
            random_movie = recommendations.sample(1).iloc[0]
            bot.send_message(message.chat.id, f"Фильм: {random_movie['title']} \n Год выпуска: {random_movie['year']} \n Режиссер: {random_movie['director']}")
            # Открываем файл изображения из папки 'photo' и отправляем его
            with open(f"photo/{random_movie['photo']}", 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
        else:
            bot.send_message(message.chat.id, 'Извините, фильмов с выбранными жанрами нет в базе данных.')
    else:
        # Если пользователь не выбрал жанры, рекомендуем случайный фильм
        random_movie = df.sample(1).iloc[0]
        bot.send_message(message.chat.id, f"Фильм: {random_movie['title']} \n Год выпуска: {random_movie['year']} \n Режиссер: {random_movie['director']}")
        # Открываем файл изображения из папки 'photo' и отправляем его
        with open(f"photo/{random_movie['photo']}", 'rb') as photo:
            bot.send_photo(message.chat.id, photo)
    # Очищаем список выбранных жанров после рекомендации
    user_genres[user_id] = []
# Список ID администраторов
admin_ids = [] # Записать id админа

@bot.message_handler(commands=['add_movie'])
def add_movie(message):
    if message.from_user.id not in admin_ids:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
        return
    bot.send_message(message.chat.id, "Введите информацию о фильме в формате: Название, Год выпуска, Режиссер, Жанры (разделенные запятыми)")
    bot.register_next_step_handler(message, process_movie_info)

def process_movie_info(message):
    global user_movie_info
    movie_info = message.text.split(',')
    if len(movie_info) < 3:
        bot.send_message(message.chat.id, "Вы ввели недостаточно данных. Пожалуйста, следуйте формату: Название, Год выпуска, Режиссер, Жанры")
        return
    title, year, director = movie_info[:3]  # Название, год, режиссер
    genres = [genre.strip() for genre in movie_info[3:]]  # Жанры (удаляем лишние пробелы)
    user_movie_info[message.from_user.id] = {'title': title, 'year': year, 'director': director, 'genres': genres}
    bot.send_message(message.chat.id, "Фильм успешно добавлен. Теперь отправьте фото фильма.")
    bot.register_next_step_handler(message, process_movie_photo)

def process_movie_photo(message):
    global user_movie_info
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    title = user_movie_info[message.from_user.id]['title']
    photo_name = f"{title}.jpg"
    with open(f"photo/{photo_name}", 'wb') as new_file:
        new_file.write(downloaded_file)

    user_movie_info[message.from_user.id]['photo'] = photo_name
    save_movie_to_database(user_movie_info[message.from_user.id])  # Сохранение фильма в базу данных
    bot.send_message(message.chat.id, "Фильм успешно добавлен в базу данных.")

def save_movie_to_database(movie_info):
    global df
    genres = ','.join(movie_info['genres'])  # Преобразование списка жанров в строку с разделителем ","
    movie_info['genre'] = genres.lower()  # Присвоение строки жанров столбцу "genre" в нижнем регистре
    df = df._append(movie_info, ignore_index=True)
    df.to_excel('database.xlsx', index=False)

bot.polling()
