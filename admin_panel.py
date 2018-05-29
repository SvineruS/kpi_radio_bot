# -*- coding: utf-8 -*-

import hashlib
import time
import math
from flask import Flask, request, redirect, url_for, abort, render_template, current_app
import flask
from sender import Sender, threads
from telebot import types
from config import *
from db import db
from bot import bot
from datmusic import download

app = Flask(__name__)


def md5(str_h):
    return hashlib.md5(str_h.encode('utf-8')).hexdigest()


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    for admin in admins:
        if request.cookies.get(admin) == md5(admins[admin]):
            return redirect(url_for('admin'))
    error = None
    success = False
    if request.method == 'POST':
        try:           
            if admins[request.form['username']] == request.form['password']:
                success = True
        except:
            pass
        if success:
            redirect_to_admin = redirect(url_for('admin'))
            response = current_app.make_response(redirect_to_admin)  
            response.set_cookie(request.form['username'], value=md5(request.form['password']))
            return response
        else:
            error = "Invalid username or password."
    return render_template('login.html', error=error)


@app.route("/admin")
def admin():
    logged = False
    for admin in admins:
        if request.cookies.get(admin) == md5(admins[admin]):
            logged = True
    if not logged:
        return redirect(url_for('login'))
    return render_template("admin.html")


@app.route("/sendmsg", methods=['GET', 'POST'])
def sendmsg():
    logged = False
    for admin in admins:
        if request.cookies.get(admin) == md5(admins[admin]):
            logged = True
    if not logged:
        return 0
    if request.form['msg'] == "":
        return abort(500)
    try:
        filename = request.files['img'].filename
        file = request.files['img'].read()
    except:
        filename = None
        file = None
    thread_id = str(round(time.time()))
    threads[thread_id] = Sender(request.form['msg'], file, thread_id, filename)
    threads[thread_id].sender()
    return str(thread_id)


@app.route("/getsent", methods=['GET', 'POST'])
def getsent():
    try:
        sent = str(math.ceil(100*threads[str(request.form["id"])].count/int(db.count())))
    except:
        return "100"
    if sent == "100":
        threads.pop(str(request.form["id"]))
    return sent


@app.route("/music/<path:subpath>", methods=['GET', 'POST'])
def getsent(subpath):
    return download(subpath, short=True)


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


if __name__ == "__main__":

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
