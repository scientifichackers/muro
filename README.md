# MuRo

#### muro _fades_ away the technology from music.

It gives you back the control of your music from clunky UIs, back to the simple, Radio tuner days.

> You know technology is good when you can't see it.

[![Image](https://i.ytimg.com/vi/CCR-VEiEPvM/hqdefault.jpg?sqp=-oaymwEZCPYBEIoBSFXyq4qpAwsIARUAAIhCGAFwAQ==&rs=AOn4CLATrtLlBf9mHIXqsxjK2pERERwJBg)](https://www.youtube.com/watch?v=CCR-VEiEPvM)

_muro stands **Mu**sic **R**em**o**te._

## Features

-   play / pause
-   skip to next / previous track
-   seek forward / backward.  
    (by pressing next / previous track button for more than ~0.5 sec)
-   primary and secondary volume control.  
    (using custom primary / secondary selection algorithm)
-   Extremely minimal (close to 0) CPU usage
-   Leave it in auto-start and forget!

## Requirements

Software -

-   Pulse Audio
-   playerctl (`sudo apt install playerctl`)
-   pipenv (`pip3 install pipenv`)

Hardware -

-   1 Wemos D1 mini (or any other micropython board)
-   1 ADS1115 ADC
-   Linux Desktop
-   2 buttons
    -   next
    -   previous
-   1 Flip switch
    -   pause/play
-   2 Potentiometers

## Install

- Edit [config.py](muro/common/config.py), notably:
    - Change `PINS` dict according to your circuit.
    - `SSID` and `PASSWD`.
    - `MUSIC_APP` according to your music player. Spotify by default.

```s
$ git clone https://github.com/pycampers/muro
$ cd muro
$ pip install -e .

$ muro install
$ muro run
```
