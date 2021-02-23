import config
from utils import VKbot
import telebot

app = VKbot(login=config.login, password=config.password, two_factor=False, cookies_save_path='sessions/')
bot = telebot.TeleBot(config.Bot_token)

if __name__ == '__main__':
    app.LongPolling(bot,wait=25)