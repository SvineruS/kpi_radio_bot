import flask
from telebot import types
from config import *
from bot import bot
from music_api import search_text

app = flask.Flask(__name__)


@app.route("/gettext/<path:name>", methods=['GET', 'POST'], host=WEB_DOMAIN)
def gettext(name):
    if not name:
        return ""
    return "<pre>" + search_text(name)


# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


def start():
    # Remove webhook, it fails sometimes the set if there is a previous webhook
    bot.remove_webhook()
    # Set webhook
    bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                    certificate=open(WEBHOOK_SSL_CERT, 'r'))
    # Start flask server
    app.run(host=WEBHOOK_LISTEN,
            port=WEBHOOK_PORT,
            ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
            threaded=True)
