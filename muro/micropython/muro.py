from machine import I2C, Pin

from muro.common import settings, unetwork
from muro.micropython import ads1x15

# init Dials
i2c = I2C(scl=Pin(settings.Dials.scl), sda=Pin(settings.Dials.sda), freq=40000)
adc = ads1x15.ADS1115(i2c, address=72, gain=1)

# init buttons
pause_btn = Pin(settings.Buttons.pause, Pin.IN, Pin.PULL_UP)
next_btn = Pin(settings.Buttons.next, Pin.IN, Pin.PULL_UP)
prev_btn = Pin(settings.Buttons.prev, Pin.IN, Pin.PULL_UP)


class Normalizer:
    def __init__(self, output_range: tuple = (0, 1)):
        self._input_min = 0
        self._input_max = 0

        self._output_min, self._output_max = output_range
        self._output_diff = self._output_max - self._output_min

        self._norm_factor = 0

    def _refresh_norm_factor(self):
        self._norm_factor = 1 / (self._input_max - self._input_min) * self._output_diff

    def _check_bounds(self, input_value):
        if input_value < self._input_min:
            self._input_min = input_value
            self._refresh_norm_factor()
        elif input_value > self._input_max:
            self._input_max = input_value
            self._refresh_norm_factor()

    def _norm(self, input_value):
        return (input_value - self._input_min) * self._norm_factor + self._output_min

    def norm(self, input_value):
        self._check_bounds(input_value)
        return self._norm(input_value)


volume_normalizer = Normalizer(settings.Dials.volume_range)
brightness_normalizer = Normalizer(settings.Dials.brightness_range)


def mainloop():
    old = None
    with unetwork.Peer(
        settings.udp_port,
        ssid=settings.Wifi.ssid,
        passwd=settings.Wifi.password,
        enable_ap=settings.Wifi.enable_ap,
        retry_for=(OSError,),
    ) as peer:
        while True:
            volume = int(
                volume_normalizer.norm(
                    adc.read(settings.Dials.read_speed, settings.Dials.volume)
                )
            )
            if volume <= settings.Dials.volume_range[0]:
                volume = 0

            new = {
                "brightness": int(
                    brightness_normalizer.norm(
                        adc.read(settings.Dials.read_speed, settings.Dials.brigtness)
                    )
                ),
                "volume": volume,
                "pause": not pause_btn.value(),
                "next": not next_btn.value(),
                "prev": not prev_btn.value(),
            }

            if old != new:
                peer.send_json(new)
                print(new)
                old = new
