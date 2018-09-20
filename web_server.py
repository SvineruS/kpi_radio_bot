import flask
import playlist_api
import music_api
from telebot import types
from config import *
from bot import bot
from threading import Thread
from json import dumps

app = flask.Flask(__name__)


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

    return resp_audio(t.data)


@app.route("/search/<path:path>", methods=['GET', 'POST'], host=WEB_DOMAIN)
def search(path):
    if not path:
        return ""
    res = music_api.search(path)
    if not res:
        return ""
    ans = []
    for t in res:
        id = '/'.join(t['download'].split('/')[-2:])
        ans.append({
            'id': id,
            'artist': t['artist'],
            'title': t['title'],
            'duration': t['duration']
        })
    return dumps(ans)


# сайтик

@app.route("/playlist/prev/get/<path:date>", methods=['GET'], host=WEB_DOMAIN)
def history_get(date):
    return playlist_api.get_history(date)


@app.route("/playlist/prev/save", methods=['GET'])
def history_save():
    # https://WEBHOOK_LISTEN:WEBHOOK_PORT /history/save?artist=%artist%&title%title%&casttitle=%casttitle%&len=%seconds%&path=%path%&pass=pass
    playlist_api.history_save(flask.request.args)
    return 'ok'


@app.route("/playlist/prev/play/<path:path>", methods=['GET', 'POST'], host=WEB_DOMAIN)
def history_play2(path):
    return resp_audio(playlist_api.history_play(path))


@app.route("/playlist/next", methods=['GET', 'POST'])
def playlist_next_html():
    f = open('Stuff/moving.html')
    h = f.read()
    f.close()
    return h


@app.route("/playlist/next/get", methods=['GET', 'POST'])
def playlist_next_get():
    return dumps(playlist_api.next_get_full())


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
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


def resp_audio(t):
    resp = flask.make_response(t)
    resp.headers['Content-Transfer-Encoding'] = 'binary'
    resp.headers['Content-Type'] = 'audio/mpeg'
    resp.headers['Content-Disposition'] = 'inline;filename="music.mp3"'
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Accept-Ranges'] = 'bytes'
    resp.headers['Content-Range'] = 'bytes */' + str(len(t))
    resp.headers['Content-Length'] = str(len(t))
    return resp


def start():
    # Remove webhook, it fails sometimes the set if there is a previous webhook
    bot.remove_webhook()
    # Set webhook
    bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                    certificate=open(WEBHOOK_SSL_CERT, 'r'))
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