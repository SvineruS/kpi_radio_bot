from threading import Thread
from web_server import start as start_serv
from scheduler import start as start_shed

start_serv()
Thread(name='shed', target=start_shed, daemon=True).start()
