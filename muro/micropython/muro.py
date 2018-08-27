from muro.micropython import ads1x15
from muro.common import settings, unetwork

from machine import I2C, Pin

# init ADC
i2c = I2C(scl=Pin(settings.PINS["SCL"]), sda=Pin(settings.PINS["SDA"]), freq=40000)
adc = ads1x15.ADS1115(i2c, address=72, gain=1)
irq_pin = Pin(settings.PINS["ALERT"], Pin.IN, Pin.PULL_UP)

# init buttons
buttons = {}
pause = Pin(settings.PINS["PAUSE"], Pin.IN, Pin.PULL_UP)
next = Pin(settings.PINS["NEXT"], Pin.IN, Pin.PULL_UP)
prev = Pin(settings.PINS["PREV"], Pin.IN, Pin.PULL_UP)

# pre-compute some stuff
MIN_VOL = settings.MIN_VOL / 100
MAX_VOL = settings.MAX_VOL / 100
ADJUSTED_VOL = MIN_VOL / settings.VOL_MIN_STEP
POT_FACTOR = (MAX_VOL - MIN_VOL) / (settings.MAX_POTENTIOMETER * settings.VOL_MIN_STEP)


def potentiometer_to_vol(potentiometer_reading):
    vol = (potentiometer_reading * POT_FACTOR) + ADJUSTED_VOL
    vol = int(vol * 100) * settings.VOL_MIN_STEP

    vol = 0 if vol < settings.MIN_VOL else vol
    vol = settings.MAX_VOL if vol > settings.MAX_VOL else vol

    return int(vol)


def read():
    return {
        "primary_vol": potentiometer_to_vol(
            adc.read(settings.SPEED, settings.PINS["PRIMARY"])
        ),
        "secondary_vol": potentiometer_to_vol(
            adc.read(settings.SPEED, settings.PINS["SECONDARY"])
        ),
        "pause": not pause.value(),
        "next": not next.value(),
        "previous": not prev.value(),
    }


def mainloop():
    old = None
    with unetwork.Peer(
        settings.UDP_PORT, ssid=settings.SSID, passwd=settings.PASSWD, retry_for=(OSError,)
    ) as peer:
        while True:
            new = read()

            if old != new:
                peer.send_json(new)
                print(new)
                old = new
