import flask
import music_api
from Stuff import history
from flask_sslify import SSLify
from telebot import types
from config import *
from bot import bot


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

    resp = flask.make_response(t.data)

    resp.headers['Content-Transfer-Encoding'] = 'binary'
    resp.headers['Content-Type'] = 'audio/mpeg'
    resp.headers['Content-Disposition'] = 'inline;filename="music.mp3"'
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Content-Length'] = len(t.data)
    return resp


@app.route("/history", methods=['GET', 'POST'], host=WEB_DOMAIN)
def history():
    f = open('Stuff/history.html', encoding='UTF-8')
    m = f.read()
    f.close()
    return m


@app.route("/history/get", methods=['POST'], host=WEB_DOMAIN)
def history_get():
    date = flask.request.data.decode('utf-8')
    return history.get(date)


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
