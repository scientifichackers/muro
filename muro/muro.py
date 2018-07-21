import subprocess
from sys import platform
from time import sleep

import zproc
from pulsectl import Pulse

from muro.common import config, unetwork

if platform != "linux":
    raise NotImplemented(f"muro doesn't support {platform.system()} yet!")


def list_players():
    return subprocess.check_output(
        ["playerctl", "--list-all"], encoding="utf-8"
    ).splitlines()


def separate_sources(sources):
    """separates sources into primary and secondary"""

    secondary_sources, primary_sources = [], []

    if len(sources):
        # separate sources based on music app
        for source in sources:
            if source.name == config.MUSIC_APP["pulseaudio"]:
                primary_sources.append(source)
            else:
                secondary_sources.append(source)

        # If music app is not in sources, and there are more than 1 audio sources, split the sources
        if not len(primary_sources) and len(secondary_sources) > 1:
            primary_sources = sources[-1:]
            secondary_sources = sources[:-1]

    return {"primary_vol": secondary_sources, "secondary_vol": primary_sources}


def set_vol(pulse, source, volume):
    vol = source.volume
    vol.value_flat = volume / 100
    pulse.volume_set(source, vol)

    print(f"{source.name} - {volume} %")


def send_command_to_player(*cmd):
    if config.MUSIC_APP["playerctl"] in list_players():
        cmd += ("--player", config.MUSIC_APP["playerctl"])

    subprocess.Popen(["playerctl", *cmd])


def mainloop():
    ctx = zproc.Context(wait=True, retry_for=(Exception,))

    ctx.state.setdefault("sources", {"primary_vol": [], "secondary_vol": []})
    ctx.state.setdefault("primary_vol", 100)
    ctx.state.setdefault("secondary_vol", 100)

    @ctx.process
    def communication_process(state):
        with unetwork.Peer(config.UDP_PORT) as peer:
            while True:
                x = peer.recv_json()[0]
                # print(x)
                state.update(x)

    def hash_pulse_sources(sources):
        return (
            ",".join(str(i.index) for i in sources["primary_vol"])
            + "::"
            + ",".join(str(i.index) for i in sources["secondary_vol"])
        )

    @ctx.process
    def source_selection_process(state):
        with Pulse("muro-source-selector") as pulse:
            old_sources_hash = None

            while True:
                sources = separate_sources(pulse.sink_input_list())
                state["sources"] = sources

                sleep(0.5)

                new_sources_hash = hash_pulse_sources(sources)
                if new_sources_hash != old_sources_hash:
                    old_sources_hash = new_sources_hash

                    for key in sources.keys():
                        for source in sources[key]:
                            set_vol(pulse, source, state[key])

                sleep(0.5)

    def start_seek_btn_process(key, cmd, seek_cmd):
        @ctx.call_when_equal(key, True, live=True)
        def seek_btn_process(state):
            print(f"{key} btn pressed")

            try:
                state.get_when_equal(key, False, timeout=0.5)

                print(f"skip to {key} track")
                send_command_to_player(cmd)

            except TimeoutError as e:
                print(e)
                print("seek forward...")

                while state[key]:
                    send_command_to_player("position", seek_cmd)
                    sleep(0.1)

            print(f"{key} btn released\n")

    start_seek_btn_process("next", "next", "3+")
    start_seek_btn_process("previous", "previous", "3-")

    def start_vol_update_proces(key):
        @ctx.call_when_change(key, live=True)
        def call_update_volume(state):
            with Pulse(f"muro-{key}") as pulse:
                for source in state["sources"][key]:
                    set_vol(pulse, source, state[key])

    start_vol_update_proces("primary_vol")
    start_vol_update_proces("secondary_vol")

    @ctx.call_when_change("pause")
    def play_pause(state):
        print("play-pause playback\n")
        send_command_to_player("play-pause")
