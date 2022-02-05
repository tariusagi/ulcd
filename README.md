# Uzi's LCD library

Most of the programs and modules work with Raspberry Pi boards, which requires the `RPi.GPIO` package. Install it with `pip install rpi.gpio`.

Visit https://pinout.xyz/, or run `gpio readall` to view the Raspberry GPIO pinout.

## lcd

This Python 3 program controll various LCDs using code from the various modules in this project. 

Usage:

```txt
Syntax: lcd [OPTION] [TEXT]
Common options:
-h           Display this help and exit.
-L host:port Listen on "host:port" for client connections (the daemon mode).
Device options:
-t           LCD type (required). See supported types below.
-i           Initialize/reset LCD (effectively clear the screen).
-x           Clear the screen.
-r           Restore/cleanup GPIO settings (default is not) upon termination..
-B           Turn backlight on.
-b           Turn backlight off.
-d opt       Run a demo name "opt" (default "all") and ignore all other options.
-g           Use graphic mode (if supported).
-z freq      Set LCD communication speed in Hz (if supported) or "-" to revert
             to default value (1953000, 1.95Mhz). A 39.9Mhz (39900000Hz)
             frequency was tested working well on a Raspberry Pi Zero W.
-w usec      Set delay in microsecond between writes to LCD (if supported) or
             "-" to revert to default value (72).
-p           Print LCD parameters.
-s           Show LCD server showStat at the last line.
-v n         Verbose/debug level. Debug messages will be sent to stderr.
Text options:
-f font      Use given font named "font" (if supported).
-l line      Set text line before printing (start from 1, default 1).
-c column    Set text column before printing (start from 1, default 1).
Supported LCD types:
- st7920: 128x64 graphic LCD, ST7920 chip, 8 lines 21 characters, 6x8 font.
- hd44780: 16x2 character LCD, HD44780 chip, 2 lines 16 characters, 5x8 font.
- hd44780opi: it is hd44780 written for Orange Pi boards.
Supported fonts:
- st7920: 4x6, 5x6, 6x8 (default).
```

To run this program as a daemon at boot, use `/etc/rc.local` or create a service file `/etc/systemd/system/lcd.service` like this (assumming path to this program is at `/usr/local/bin/lcd`):

```systemd
[Unit]
Description=Listen and display on attached LCD
Wants=network-online.target
After=network-online.target

[Service]
User=peter
Group=peter
ExecStart=/usr/local/bin/lcd -t st7920 -L 0.0.0.0:1234
ExecReload=/bin/bash -c 'echo clear | nc -w1 127.0.0.1 1234'
Restart=on-failure
RestartSec=60

[Install]
WantedBy=default.target
```

Then run:

```sh
sudo systemctl daemon-reload
sudo systemctl enable lcd
sudo systemctl start lcd
```

To start the daemon as a service.

To send command to this server, use `nc`, `ncat` or nay network client. For example, the following commands tell the server to clear the LCD and then print "Hello World" in line 2:

```sh
echo clear | nc -w1 127.0.0.1 1234
echo line2 Hello World | nc -w1 127.0.0.1 1234
```

Supported commands are:

- `quit`: terminate the daemon.
- `clear`: Clear the LCD.
- `lineN text`: Show the "text" on the LCD's line N.
- `backlight on|off`: turn on or off the LCD's backlight.
- `font name`: Set the LCD font. Use "?" to list the supported fonts.
- `freq N`: set communication speed to N hertz. Use "-" to set the default value.
- `delay N`: set delay time between writes to LCD in microseconds. Use "-" to set the default value.

## lcdserver

*This program is obsolete. I keep it here as an example of how to write a network server in Bash using `ncat`. Use `lcd` in daemon mode instead (see above).*

A Bash script to run a network server and serve requests from clients to control the attached LCD. Requires root priviledge.

This program need `ncat`, and this project's `lcd` program on PATH.

Usage:

```txt
Syntax: lcdserver -h -l file <-t type> <ip> <port>
where:
-h      Print this usage.
-l      Log to the given file.
-t type Set the LCD type for "lcd" command. Run "lcd -h" for help.
```

How to send them to this server please refer to `lcd` daemon mode section above. This program may not support all commands that `lcd` daemon can. The current supported commands are:

- `clear`: Clear the LCD.
- `lineN text`: Show the text on the LCD's line N.

To run this server at boot, use `/etc/rc.local` or create a service file `/etc/systemd/system/lcdserver.service` like this (assumming path to this server is at `/usr/local/bin/lcdserver`):

```systemd
[Unit]
Description=Listen and display on attached LCD
Wants=network-online.target
After=network-online.target

[Service]
User=peter
Group=peter
ExecStart=/usr/local/bin/lcdserver -t st7920 0.0.0.0 1234
ExecReload=/bin/bash -c 'echo clear | nc -w1 127.0.0.1 1234'
Restart=on-failure
RestartSec=60

[Install]
WantedBy=default.target
```

Then run:

```sh
sudo systemctl daemon-reload
sudo systemctl enable lcdserver
sudo systemctl start lcdserver
```

To start the server as a service.

## st7920.py

A Python 3 module to control the 128x64 LCD with ST7290 driver.

Wiring scheme:

```txt
LCD   GPIO (BCM)
---   ----------
GND - GND
VCC - +5V
VO  - (Optional) +5V with 10K potentionmeter to adjust contrast.
RS  - 8  (SPI0 CE0)
R/W - 10 (SPI0 MOSI)
E   - 11 (SPI0 SCLK)
PSB - GND (set SPI mode)
BLA - +5V or default 24 to control blacklight
BLK - Ground for backlight kathode
```

Note that pin 10, 11 (MOSI, SCLK) pins MUST be set to ALT0 mode, and pin 8 (SPI0 CE0) must be set to ether ALT0 or OUT HIGH to use hardware clock SPI mode. The commands to set them are:

```sh
gpio -g mode 8 alt0
gpio -g mode 10 alt0
gpio -g mode 11 alt0
```

or

```sh
gpio -g mode 8 out
gpio -g write 8 1
gpio -g mode 10 alt0
gpio -g mode 11 alt0
```

The later is what Raspberry Pi boot up with, so this module will just work.

And if you don't want to control the backlight, just connect the BLA pin to a +5V (~60mA), which let the backlight on all the time, or leave both BLA and BLK out to disable the backlight.

## hd44780.py

A Python 3 module to control a 16x2 monochrome LCD screen. Based on this [Interfacing 16x2 LCD with Raspberry Pi](https://www.electronicshub.org/interfacing-16x2-lcd-with-raspberry-pi/). Tested on a Raspberry Pi Zero W.

Connect LCD's VDD and VSS pins to +5V and ground to power the LCD.

A 10kΩ potentionmeter MUST BE NEEDED to adjust the contrast of the LCD, such as the 3362P square potentionmeter. Connect pin 1 of the potentionmeter to the +5V power supply, pin 3 to the ground, and pin 2 to the V0 (contrast) pin of the LCD. Then adjust the potentionmeter until the contrast is right.

Wiring scheme:

```txt
LCD   GPIO (BCM)
---   ----------
VDD - +5V
VSS - Ground
V0  - Pin 3 (possitive) of a 10kΩ potentionmeter 
RS  - 17
RW  - Ground (to write data)
E   - 27
D4  - 22
D5  - 5
D6  - 6
D7  - 26
A   - 16 (backlight anode) 
K   - Ground (backlight kathode)
```

Note that this wiring avoid pins used in the ST7920 scheme, so both LCD can be
installed on one single Pi board.

## hd44780opi.py

This module is similar to hd44780.py, specifically crafted for Orange Pi Zero2 board. It need the [OPi.GPIO](https://opi-gpio.readthedocs.io/en/latest/) module, which can be installed with `sudo pip install --upgrade OPi.GPIO`.

Wiring scheme (physical pin number):

```txt
LCD   GPIO (Physical)
---   ---------------
VDD - +5V
VSS - Ground
V0  - Pin 3 (possitive) of a 10kΩ potentionmeter 
RS  - 26
RW  - Ground (to write data)
E   - 24
D4  - 22
D5  - 18
D6  - 16
D7  - 12
A   - 10 (backlight anode) 
K   - Ground (backlight kathode)
```

## font2py

A Python 3 program to convert a font files into a Python module, to be used by LCD module like st7920.py. Currently supports monospaced, 1-8 bits PNG font sheet. The font4x6.py, font5x6.py and font6x8.py were generated by this program.

Usage:

```txt
Syntax: font2py [OPTION] <file>
Convert a monospace, bitmap font file to a Python object.

OPTION:
  -h, --help                  Print this usage.
  -d, --debug                 Enable debug messages to stderr.
  -n, --name=string           Name of the Python font object (default "font").
  -W, --width=num             (Required) Width of a character in pixels.
  -H, --height=num            (Required) Height of a character in pixels.
  -f, --first=num             (Required) First character code (ASCII).
  -s, --size=num              Size of font table (number of characters). Default
                              to maximum available from the input file.
  -k, --skip=num              Skip first num of characters.
  -b, --background=num        Set the value of the background pixels.

This program will print to stdout a Python source module, with comments telling
the font's attributes, the font object itself, and a small code to pretty print
the font object itself should the module be executed as a standalone program.
The font object is a Python dict, which consists of:
- width: character width.
- height: character height.
- first: the first character (ASCII) code in the bitmap.
- size: total number of characters in the bitmap.
- bitmap: a dict of characters' bitmaps, with keys are the characters' ASCII
code itself. Each value is a list of imgRows, each row is a list of bytes,
each byte represent 8 bits of that character's bitmap, up to "width" number
of bits.
```
