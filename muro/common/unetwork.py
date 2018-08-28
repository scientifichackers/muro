import sys

try:
    import ujson as json
except ImportError:
    import json

if sys.implementation.name == "micropython":
    import usocket as socket
    import network
    from utime import sleep

    MICROPYTHON = True
    ap_if = network.WLAN(network.AP_IF)
    sta_if = network.WLAN(network.STA_IF)
else:
    import traceback
    import socket
    from time import sleep

    MICROPYTHON = False

BCAST_HOST = "255.255.255.255"
LOCAL_HOST = "0.0.0.0"


def micropython_only(fn):
    def wrapper(*args, **kwargs):
        if MICROPYTHON:
            return fn(*args, **kwargs)

    return wrapper


class Peer:
    def __init__(
        self,
        port,
        *,
        ssid: str = None,
        passwd: str = None,
        enable_ap: bool = False,
        buffer_size: int = 1024,
        namespace: str = ":)",
        retry_for: tuple = (),
        retry_delay: float = 5.0,
    ):
        """
        :param ssid: (Optional) SSID of a WIFI connection.
        :param passwd: (Optional) Password for WIFI connection.
        :param enable_ap: (Optional) Enable ESP's own Access Point.
        :param network_wait: (Optional) Time in sec to wait for a network connection.
        :param retry_for: (Optional) Retry if any of these Exceptions occur.
        :param retry_delay: (Optional) Time in sec to wait for, before retrying.
        """

        self.port = port
        self.latency = 5
        self.enable_ap = enable_ap
        self.buffer_size = buffer_size
        self.ssid = ssid
        self.passwd = passwd
        self.retry_for = retry_for
        self.retry_delay = retry_delay
        self.namespace_bytes = namespace.encode("utf-8")
        self.namespace_size = len(self.namespace_bytes)
        self.send_sock, self.recv_sock = None, None
        self.connect()

    def _handle_error(self, exc=None):
        print()
        print(print("Crash report:"))

        if MICROPYTHON:
            sys.print_exception(exc)
        else:
            traceback.print_exc()

        print("Retrying in {} sec…".format(self.retry_delay))
        print()

        sleep(self.retry_delay)

    @property
    @micropython_only
    def connected(self):
        return ap_if.isconnected() or sta_if.isconnected()

    @micropython_only
    def _configure_network(self):
        if self.enable_ap:
            ap_if.active(True)
        if self.ssid is not None:
            sta_if.active(True)
            sta_if.scan()
            sta_if.disconnect()
            sta_if.connect(self.ssid, self.passwd)

    @micropython_only
    def wait_for_network(self, *, max_tries=None, refresh_freq_hz=1):
        wait_sec = 1 / refresh_freq_hz
        print("Waiting for network...", end="")

        count = 0
        while not self.connected:
            count += 1
            sleep(wait_sec)

            if max_tries is not None and count > max_tries:
                print()
                if not self.connected:
                    raise OSError(
                        "Couldn't establish a connection even after {} tries.".format(
                            max_tries
                        )
                    )
                return
            else:
                print("{}...".format(count), end="")

    @micropython_only
    def _connect_network(self):
        print(
            "Connecting to network… (ssid: {} passwd: {} AP: {})".format(
                repr(self.ssid), repr(self.passwd), self.enable_ap
            )
        )

        while True:
            try:
                self._configure_network()
                self.wait_for_network(max_tries=50)
            except self.retry_for as e:
                self._handle_error(e)
                self._disconnect_network()
            else:
                print("Connected to network!")
                return

    @micropython_only
    def _disconnect_network(self):
        ap_if.active(False)
        sta_if.active(False)

    def connect(self):
        self.disconnect()
        self._connect_network()

        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind((LOCAL_HOST, self.port))

        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if not MICROPYTHON:
            self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def disconnect(self):
        self._disconnect_network()

        if self.send_sock is not None:
            self.send_sock.close()

        if self.recv_sock is not None:
            self.recv_sock.close()

    def _send(self, msg, host, insurance):
        msg = self.namespace_bytes + msg

        if host is None:
            host = BCAST_HOST

        if insurance:
            while True:
                val = self.send_sock.sendto(msg, (host, self.port))

                try:
                    self.send_sock.settimeout(self.latency)
                    _msg, _address = self.send_sock.recvfrom(self.buffer_size)
                except OSError:
                    pass
                else:
                    if _msg == msg:
                        return val
                finally:
                    self.send_sock.settimeout(None)
        else:
            return self.send_sock.sendto(msg, (host, self.port))

    def send(self, msg_bytes, host=None, *, insurance=False):
        while True:
            try:
                return self._send(msg_bytes, host, insurance)
            except self.retry_for as e:
                self._handle_error(e)
                self.connect()

    def _recv(self, insurance):
        while True:
            msg, address = self.recv_sock.recvfrom(self.buffer_size)

            if msg.startswith(self.namespace_bytes):
                if insurance:
                    self.recv_sock.sendto(msg, address)
                return msg[self.namespace_size :], address

    def recv(self, *, insurance=False):
        while True:
            try:
                return self._recv(insurance)
            except self.retry_for as e:
                self._handle_error(e)
                self.connect()

    def send_str(self, msg_str, *args, **kwargs):
        return self.send(msg_str.encode("utf-8"), *args, **kwargs)

    def recv_str(self):
        msg, address = self.recv()
        return msg.decode("utf-8"), address

    def send_json(self, msg_json, *args, **kwargs):
        return self.send(json.dumps(msg_json), *args, **kwargs)

    def recv_json(self):
        msg, address = self.recv()
        return json.loads(msg), address

    def __enter__(self):
        return self

    def __exit__(self, e, *args, **kwargs):
        if e in self.retry_for:
            self._handle_error(e)
            self.connect()
            return True  # bypass normal exception mechanism
        else:
            self.disconnect()
