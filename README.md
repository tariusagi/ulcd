# uzi-lcd

Display messages and media on various LCD screens via GPIO.

## lcd-16x2-mono
Display text onto a 16x2 monochrome LCD screen. Based on this [Drive a 16x2 LCD with the Raspberry Pi](https://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi/overview). Tested on a Raspberry Pi Zero W.
### Install
This program requires Python3 and adafruit-circuitpython-charlcd package. Install it with:
```sh
sudo pip3 install adafruit-circuitpython-charlcd
```

### Usage
```
Syntax: {PROGRAM} [OPTION] [LINE1] [LINE2]
OPTION:
-h      Display this help and exit.
-c      Clear the LCD.
-1 path File to read first line, imply daemon mode.
-2 path File to read second line, imply daemon mode.
-i n    Set scrolling interval (float). Default is 0.5 (second).
-t n    Terminate after n seconds. Otherwise run indefinitely.
-v      Run verbose.
LINE1   A text to display in line 1. This override -1 and -2 options.
LINE2   A text to display in line 2. This override -1 and -2 options.
In daemon mode, this program keep reading file(s) as specified in -1 and -2 
options to get new textx and update the display accordingly. Also in this mode,
if a text line is longer than the display, it will be scroll back and forth
indefinitely or until time out (as specified by -t option).  
Daemon can be used only with -1 and/or -2 option(s).  If -1 and -2 option are
not used, then this program will just display TEXT and then terminate.
```
