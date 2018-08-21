from threading import Thread

from web_hook import start as hook
from web_site import start as site

Thread(target=hook).start()
Thread(target=site).start()

