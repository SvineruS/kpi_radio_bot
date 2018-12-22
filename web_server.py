import flask
import playlist_api
import music_api
from telebot import types
from config import *
import bot
from threading import Thread
from json import dumps

app = flask.Flask(__name__)


@app.route("/gettext/<path:name>", methods=['GET', 'POST'], host=WEB_DOMAIN)
def gettext(name):
    if not name:
        return ""
    return "<pre>" + music_api.search_text(name)


@app.route("/playlist/prev/get/<path:date>", methods=['GET'], host=WEB_DOMAIN)
def history_get(date):
    return playlist_api.get_history(date)


@app.route("/playlist/prev/save", methods=['GET'])
def history_save():
    # https://WEBHOOK_LISTEN:WEBHOOK_PORT /history/save?artist=%artist%&title%title%&casttitle=%casttitle%&len=%seconds%&path=%path%&pass=pass
    args = flask.request.args
    fields = {
        'artist': args.get('artist'),
        'title': args.get('title'),
        'casttitle': args.get('casttitle'),
        'path': args.get('path'),
    }
    bot.send_history(fields)
    return 'ok'


@app.route("/playlist/next", methods=['GET', 'POST'])
def playlist_next_html():
    f = open('Stuff/moving.html', encoding='utf-8')
    h = f.read()
    f.close()
    return h


@app.route("/playlist/next/get", methods=['GET', 'POST'])
def playlist_next_get():
    return dumps(playlist_api.next_get(True))


@app.route("/playlist/next/move/<path:n1>/<path:n2>", methods=['GET', 'POST'])
def playlist_next_move(n1, n2):
    playlist_api.next_move(n1, n2)
    return playlist_next_get()


# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


def start():
    # Remove webhook, it fails sometimes the set if there is a previous webhook

    webhook = bot.bot.get_webhook_info()
    if webhook.url != WEBHOOK_URL_BASE+WEBHOOK_URL_PATH:
        if not webhook.url:
            bot.bot.delete_webhook()
        bot.bot.set_webhook(WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, certificate=open(WEBHOOK_SSL_CERT, 'rb'))

    # Start flask server
    https = lambda: app.run(host=WEBHOOK_LISTEN,
                            port=WEBHOOK_PORT,
                            ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
                            threaded=True)

    http = lambda: app.run(host=WEBHOOK_LISTEN,
                           port=80,
                           threaded=True)

    Thread(target=https).start()
    Thread(target=http).start()
