import ustruct as struct
from machine import I2C, Pin

from muro.common import settings, unetwork
from muro.micropython import ads1x15, dialmap


def main():
    # init Dials
    i2c = I2C(scl=Pin(settings.Dials.scl), sda=Pin(settings.Dials.sda), freq=40000)
    adc = ads1x15.ADS1115(i2c, address=72, gain=1)

    # init buttons
    get_pause_btn = Pin(settings.Buttons.pause, Pin.IN, Pin.PULL_UP).value
    get_next_btn = Pin(settings.Buttons.next, Pin.IN, Pin.PULL_UP).value
    get_prev_btn = Pin(settings.Buttons.prev, Pin.IN, Pin.PULL_UP).value

    _tf_vol = dialmap.DialMap(
        settings.Dials.volume_range, settings.Dials.deadzone
    ).__getitem__

    def tf_vol(raw):
        volume = _tf_vol(raw)
        if volume <= settings.Dials.volume_range[0]:
            volume = 0
        return volume

    tf_bright = dialmap.DialMap(
        settings.Dials.brightness_range, settings.Dials.deadzone
    ).__getitem__
    adcread = adc.read

    structfmt = ">" + "i" * 2 + "B" * 3

    def read():
        return struct.pack(
            structfmt,
            tf_vol(adcread(settings.Dials.read_speed, settings.Dials.volume)),
            tf_bright(adcread(settings.Dials.read_speed, settings.Dials.brigtness)),
            not get_pause_btn(),
            not get_next_btn(),
            not get_prev_btn(),
        )

    with unetwork.Peer(
        settings.udp_port,
        ssid=settings.Wifi.ssid,
        passwd=settings.Wifi.password,
        enable_ap=settings.Wifi.enable_ap,
        retry_for=(OSError,),
    ) as peer:
        send = peer.send

        old = None
        while True:
            new = read()
            if old != new:
                send(new)
                old = new
