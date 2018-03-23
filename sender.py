from db import db
from bot import bot
from threading import Thread

threads = {}


class Sender:
    def __init__(self, msg, file, id, filename):
        self.msg = msg.replace("**", "*")
        self.file = file
        self.id = id
        self.filename = filename
        self.count = 0

    def sender(self):
        Thread(target=self.start).start()

    def start(self):
        for user in db.find():
            user = user["usr"]
            try:
                if self.file is not None:
                    if self.filename.split(".")[-1] == "mp4":
                        while True:
                            try:
                                self.file = bot.send_video(chat_id=user, data=self.file).video.file_id
                                break
                            except Exception as e:
                                if "Forbidden: bot was blocked by the user" in str(e):
                                    break
                                if "chat not found" in str(e):
                                    break
                    else:
                        self.file = bot.send_photo(chat_id=user, photo=self.file).photo[-1].file_id
                bot.send_message(user, self.msg, parse_mode="markdown")
            except Exception as e:
                print(e)
            self.count += 1
