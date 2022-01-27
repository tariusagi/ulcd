# Uzi's LCD library

Most of the programs and modules work with Raspberry Pi boards, which requires the `RPi.GPIO` package. Install it with `pip install rpi.gpio`.

Visit https://pinout.xyz/, or run `gpio readall` to view the Raspberry GPIO pinout.

## lcd

This Python 3 program controll various LCDs using code from the various modules in this project. 

Usage:

```txt
Syntax: lcd [OPTION] [TEXT]
OPTION:
-B      Turn backlight on.
-b      Turn backlight off.
-d op   Run a demo with option op (default "all") and ignore all other options.
-h      Display this help and exit.
-i      Initialize/reset LCD (effectively clear the screen).
-p      Print LCD parameters.
-t      LCD type (required). See supported types below.
-x      Clear the LCD screen.
-r      Restore GPIO settings (default is not).
-l n    Move text cursor to line n (start from 1, default 1).
-c n    Move text cursor to column n (if supported, start from 1, default 1).

Supported LCD are:
- st7920: 128x64 graphic LCD, ST7920 chip, 10 lines 32 characters, 3x5 font.
- hd44780: 16x2 character LCD, HD44780 chip, 2 lines 16 characters, 5x8 font.
- hd44780opi: it is hd44780 written for Orange Pi boards.
```

## lcdserver

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

To send command to this server, use `nc`, `ncat` or nay network client. For example, the following command tell the server to clear the LCD:

```sh
echo clear | nc -w1 127.0.0.1 1234
```

or create a text file containing commands and send it over. For example, with this `cmd.txt`:

```
clear
line1 First line
line2 Second line
display
```

Run this command to send the commands in that file to the server:

```sh
nc -w1 127.0.0.1 1234 < cmd.txt
```

And the server will do the following:

- Clear the LCD.
- Put "First line" to line 1 buffer.
- Put "Second line" to line 2 buffer.
- Display the buffer on the LCD.

Supported commands are:

- `clear`: Clear the LCD.
- `line1` text: Show the text on the LCD's first line.
- `line2` text: Show the text on the LCD's second line.
- `display`: display line 1 and line 2 on the LCD.

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

A Python 3 module to control the 128x64 LCD with ST7290 driver. Bases on [RPi-12864-LCD-ST7920-lib](https://github.com/SrBrahma/RPi-12864-LCD-ST7920-lib).

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

## st7920hwspi

A Python 3 program to test the 128x64 ST7920 LCD in hardware SPI mode using spidev module. It just displays some texts in LCD's text mode.

## st7920-demo

A Python 3 program to demonstrate the 128x64 ST7920 LCD in soft clock SPI mode. Running without argument to display a simple test or "all" to perform a full demonstration with texts, custom fonts and graphics.

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
