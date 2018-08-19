import flask
import music_api
from flask_sslify import SSLify
from telebot import types
from config import *
from bot import bot
from io import BytesIO

app = flask.Flask(__name__)
sslify = SSLify(app)


@app.route("/gettext/<path:name>", methods=['GET', 'POST'], host=WEB_DOMAIN)
def gettext(name):
    if not name:
        return ""
    return "<pre>" + music_api.search_text(name)


@app.route("/download/<path:path>", methods=['GET', 'POST'], host=WEB_DOMAIN)
def download(path):
    if not path:
        return ""
    t = music_api.download(path, short=True)
    if not t:
        return ""

    byte_io = BytesIO(t.read())
    return flask.send_file(byte_io, mimetype='audio/mpeg')


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
