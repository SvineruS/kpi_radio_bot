import flask
import music_api
from Stuff import history
from config import *


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

    resp = flask.make_response(t.data)

    resp.headers['Content-Transfer-Encoding'] = 'binary'
    resp.headers['Content-Type'] = 'audio/mpeg'
    resp.headers['Content-Disposition'] = 'inline;filename="music.mp3"'
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Content-Length'] = len(t.data)
    return resp


@app.route("/history", methods=['GET', 'POST'], host=WEB_DOMAIN)
def history_html():
    return history.html()


@app.route("/history/getday", methods=['POST'], host=WEB_DOMAIN)
def history_get():
    date = flask.request.data.decode('utf-8')
    a = history.get(date)
    print(a)
    return a


@app.route("/history/save", methods=['GET'])
def history_save():
    # http://WEBHOOK_LISTEN:WEBHOOK_PORT /history/save?artist=%artist%&title%title%&casttitle=%casttitle%&len=%seconds%&path=%path%&pass=pass
    history.save(flask.request.args)
    return ''


def start():
    app.run(host=WEBHOOK_LISTEN,
            port=80,
            threaded=True)
