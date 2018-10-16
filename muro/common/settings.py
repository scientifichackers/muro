udp_port = 45123


class Wifi:
    ssid = "Here"
    password = "fevistick"

    enable_ap = False


class Buttons:
    seek_timeout = 0.25  # timeout for switching to seek mode

    next = 14  # D5
    prev = 12  # D6
    pause = 13  # D7


class Dials:
    read_speed = 3  # between 1 and 7 (3 seems to be a sweet spot)

    # The deadzone for the dial in %.
    deadzone = 25

    # sda/scl for I2C
    sda = 4  # D2
    scl = 5  # D1

    # ADC pin number
    volume = 3
    brigtness = 0

    volume_range = range(15, 181)
    brightness_range = range(0, 101)
