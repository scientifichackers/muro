import subprocess
from pprint import pprint
from time import sleep
from typing import Iterable, Union
import pulsectl
import numpy as np
import zproc

from muro.common import settings, unetwork
from muro.util import Logger

log = Logger()


def send_command_to_player(*cmd):
    cmd = ["playerctl", *cmd]
    log.cmd_info(cmd)
    return subprocess.Popen(cmd)


def set_volume(pulse, value: Union[float, int]):
    for source in pulse.sink_input_list():
        try:
            pulse.volume_set_all_chans(source, value / 100)
        except pulsectl.PulseOperationFailed as e:
            print(e)
    log.info(f"Set volume: {value}%")


def set_brightness(value: Union[float, int]):
    cmd = ["xbacklight", "-set", str(value)]
    log.cmd_info(cmd)
    subprocess.Popen(cmd)


class LastValueIterator:
    def __init__(self, seq: Iterable):
        super().__init__()
        self._iter = iter(seq)
        self._last_val = None

    def __next__(self):
        try:
            self._last_val = next(self._iter)
        except StopIteration:
            pass

        return self._last_val


def mainloop():
    ctx = zproc.Context(wait=True, retry_for=(Exception,))

    ctx.state.setdefault("volume", 100)
    ctx.state.setdefault("brightness", 100)

    @ctx.process
    def network(state):
        with unetwork.Peer(settings.udp_port) as peer:
            while True:
                data = peer.recv_json()[0]
                state.update(data)

    @ctx.process
    def update_volume(state):

        with pulsectl.Pulse("muro-volume") as pulse:
            while True:
                set_volume(pulse, state.get_when_change("volume"))

    @ctx.call_when_change("pause", stateful=False, live=False)
    def play_pause():
        send_command_to_player("play-pause")

    @ctx.call_when_change("brightness")
    def update_brightness(state):
        set_brightness(state["brightness"])

    def seek_btn_process_gen(key, cmd, seek_range):
        if cmd == "next":
            seek_cmds = [
                f"{i:.2f}+" for i in np.geomspace(seek_range[0], seek_range[1], 50)
            ]
        elif cmd == "previous":
            seek_cmds = [
                f"{i:.2f}-" for i in np.geomspace(seek_range[0], seek_range[1], 50)
            ]
        else:
            raise ValueError(
                f'"cmd" must be one of "next" or "previous", not {repr(cmd)}'
            )

        @ctx.call_when_equal(key, True)
        def seek_btn_process(state):
            log.debug(f"{key} btn pressed")
            try:
                state.get_when_equal(key, False, timeout=settings.Buttons.seek_timeout)
                send_command_to_player(cmd)
            except TimeoutError as e:
                log.debug(e)
                log.info("seek forward...")

                seek_cmd_it = LastValueIterator(seek_cmds)
                while state[key]:
                    send_command_to_player("position", next(seek_cmd_it))
                    sleep(0.1)

            log.debug(f"{key} btn released")

    seek_btn_process_gen("next", "next", (2, 10))
    seek_btn_process_gen("prev", "previous", (3, 10))

    pprint(ctx.process_list)
