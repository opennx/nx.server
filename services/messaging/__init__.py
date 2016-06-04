import socket
import thread
import time

from urllib2 import urlopen

from nx import *
from nx.services import BaseService


class SeismicMessage():
    def __init__(self, packet):
        self.timestamp, self.site_name, self.host, self.method, self.data = packet

    @property
    def json(self):
        return json.dumps(self.timestamp, self.site_name, self.host, self.method, self.data)


class Service(BaseService):
    def on_init(self):

        self.site_name = config["site_name"]

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0",int(config["seismic_port"])))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        status = self.sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,socket.inet_aton(config["seismic_addr"]) + socket.inet_aton("0.0.0.0"));
        self.sock.settimeout(1)

        self.message_queue = []

        #
        # Message relaying
        #

        self.relays = []
        for relay in self.settings.findall("relay"):
            host = relay.text
            port = int(relay.attrib.get("port", 443))
            ssl = int(relay.attrib.get("ssl", True))
            if not host:
                continue
            url = "{protocol}://{host}:{port}/msg_publish?id={site_name}".format(
                    protocol=["http","https"][ssl],
                    host=host,
                    port=port,
                    site_name=config["site_name"]
                )
            self.relays.append(url)

        #
        # Logging
        #

        try:
            self.log_path = self.settings.find("log_path").text
        except:
            self.log_path = False

        if self.log_path and not os.path.exists(self.log_path):
            try:
                os.makedirs(self.log_path)
            except:
                self.log_path = False

        thread.start_new_thread(self.listen, ())
        thread.start_new_thread(self.process, ())


    def listen(self):
        while True:
            try:
                message, addr = self.sock.recvfrom(1024)
            except (socket.error):
                continue
            try:
                message = SeismicMessage(json.loads(message))
            except:
                logging.warning("Malformed seismic message detected")
                continue
            if message.site_name != config["site_name"]:
                continue
            self.message_queue.append(message)


    def process(self):
        while True:
            if not self.message_queue:
                time.sleep(.01)
                continue

            message = self.message_queue.pop(0)

            #TODO: Message deduplication (playout_status etc)

            self.relay_message(message.json)
            if self.log_path and message.method == "log":
                try:
                    log = "{}\t{}\t{}@{}\t{}\n".format(
                            time.strftime("%H:%M:%S"),

                            {DEBUG      : "DEBUG    ",
                            INFO       : "INFO     ",
                            WARNING    : "WARNING  ",
                            ERROR      : "ERROR    ",
                            GOOD_NEWS  : "GOOD NEWS"}[message.data["msg_type"]],

                            message.data["user"],
                            message.host,
                            message.data["message"]
                        )
                except:
                    continue
                fn = os.path.join(self.log_path, time.strftime("%Y-%m-%d.txt"))
                f = open(fn, "a")
                f.write(log)
                f.close()

    def relay_message(self, message):
        message = message.replace("\n", "") + "\n" # one message per line
        for relay in self.relays:
            result = urlopen(relay, message.encode("ascii"), timeout=1)

