from muro.micropython import ads1x15
from muro.common import config, unetwork

from machine import I2C, Pin

# init ADC
i2c = I2C(scl=Pin(config.PINS["SCL"]), sda=Pin(config.PINS["SDA"]), freq=40000)
adc = ads1x15.ADS1115(i2c, address=72, gain=1)
irq_pin = Pin(config.PINS["ALERT"], Pin.IN, Pin.PULL_UP)

# init buttons
buttons = {}
pause = Pin(config.PINS["PAUSE"], Pin.IN, Pin.PULL_UP)
next = Pin(config.PINS["NEXT"], Pin.IN, Pin.PULL_UP)
prev = Pin(config.PINS["PREV"], Pin.IN, Pin.PULL_UP)

# pre-compute some stuff
MIN_VOL = config.MIN_VOL / 100
MAX_VOL = config.MAX_VOL / 100
ADJUSTED_VOL = MIN_VOL / config.VOL_MIN_STEP
POT_FACTOR = (MAX_VOL - MIN_VOL) / (config.MAX_POTENTIOMETER * config.VOL_MIN_STEP)


def potentiometer_to_vol(potentiometer_reading):
    vol = (potentiometer_reading * POT_FACTOR) + ADJUSTED_VOL
    vol = int(vol * 100) * config.VOL_MIN_STEP

    vol = 0 if vol < config.MIN_VOL else vol
    vol = config.MAX_VOL if vol > config.MAX_VOL else vol

    return int(vol)


def read():
    return {
        "primary_vol": potentiometer_to_vol(
            adc.read(config.SPEED, config.PINS["PRIMARY"])
        ),
        "secondary_vol": potentiometer_to_vol(
            adc.read(config.SPEED, config.PINS["SECONDARY"])
        ),
        "pause": not pause.value(),
        "next": not next.value(),
        "previous": not prev.value(),
    }


def mainloop():
    old = None
    with unetwork.Peer(
        config.UDP_PORT, ssid=config.SSID, passwd=config.PASSWD, retry_for=(OSError,)
    ) as peer:
        while True:
            new = read()

            if old != new:
                peer.send_json(new)
                print(new)
                old = new
