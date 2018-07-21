# Common settings
UDP_PORT = 45123

# CPython
MUSIC_APP = {
    "pulseaudio": "Spotify",  # name as it appears in pulseaudio
    "playerctl": "spotify",  # name as it appears in playerctl
}

# MicroPython
SSID = "Here"
PASSWD = "fevistick"

SPEED = 2  # speed of sensor read from 1 to 7

MAX_POTENTIOMETER = 20000  # max value of the potentiometer reading
MIN_VOL = 15  # min vol in %
MAX_VOL = 150  # max vol in %
VOL_MIN_STEP = 2  # min step of volume

PINS = {
    "SDA": 4,  # D2
    "SCL": 5,  # D1
    "ALERT": 0,  # D3
    "SECONDARY": 0,  # A0
    "PRIMARY": 3,  # A1
    "NEXT": 14,  # D5
    "PREV": 12,  # D6
    "PAUSE": 13,  # D7
}
