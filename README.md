# MuRo

#### muro _fades_ away the technology from music.

It gives you back the control of your music from clunky UIs, back to the simple, Radio tuner days.

> You know technology is good when you can't see it.

[![Image](https://i.ytimg.com/vi/CCR-VEiEPvM/hqdefault.jpg?sqp=-oaymwEZCPYBEIoBSFXyq4qpAwsIARUAAIhCGAFwAQ==&rs=AOn4CLATrtLlBf9mHIXqsxjK2pERERwJBg)](https://www.youtube.com/watch?v=CCR-VEiEPvM)

## Features

- Peer discovery (The device will automatically find your computer on the network).
- Play / pause track.
- Skip to next / previous track.
- Seek forward / backward. 
    (by pressing next / previous track button for more than some timeout value)
- Volume control.  
- Brightness (backlight) control.
- Extremely minimal (close to 0) CPU usage
- Leave it in auto-start and forget!

## Requirements

Software:
- `amixer`
- `playerctl`
- `xbacklight` 
- Python >= 3.6

Hardware:
- A Linux Desktop
- 1 Wemos D1 mini (or any other micropython board)
- 1 ADS1115 ADC
- 2 buttons
- 1 Flip switch
- 2 Potentiometers

## Install

```
$ git clone https://github.com/pycampers/muro
$ cd muro
$ pip install -e .
```

*Edit [settings.py](muro/common/settings.py) as per your setup.*

```
$ muro install
$ muro run
```

_muro stands **Mu**sic **R**em**o**te._
