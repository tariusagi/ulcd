# Uzi's LCD library

Display messages and media on various LCD screens via GPIO.

## lcd-16x2-mono-simple

Display text onto a 16x2 monochrome LCD screen. Based on this [Interfacing 16x2 LCD with Raspberry Pi](https://www.electronicshub.org/interfacing-16x2-lcd-with-raspberry-pi/). Tested on a Raspberry Pi Zero W.

This is a Python 3 program. It requires the `RPi.GPIO` package. Install it with `pip install rpi.gpio`.

For the Raspbery Pi pinout, visit https://pinout.xyz/, or run `gpio readall` to get that pinout, like mine below:

```txt
 +-----+-----+---------+------+---+-Pi ZeroW-+---+------+---------+-----+-----+
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
 |     |     |    3.3v |      |   |  1 || 2  |   |      | 5v      |     |     |
 |   2 |   8 |   SDA.1 |   IN | 1 |  3 || 4  |   |      | 5v      |     |     |
 |   3 |   9 |   SCL.1 |   IN | 1 |  5 || 6  |   |      | 0v      |     |     |
 |   4 |   7 | GPIO. 7 |   IN | 1 |  7 || 8  | 0 | IN   | TxD     | 15  | 14  |
 |     |     |      0v |      |   |  9 || 10 | 1 | IN   | RxD     | 16  | 15  |
 |  17 |   0 | GPIO. 0 |   IN | 0 | 11 || 12 | 0 | IN   | GPIO. 1 | 1   | 18  |
 |  27 |   2 | GPIO. 2 |   IN | 0 | 13 || 14 |   |      | 0v      |     |     |
 |  22 |   3 | GPIO. 3 |   IN | 0 | 15 || 16 | 0 | IN   | GPIO. 4 | 4   | 23  |
 |     |     |    3.3v |      |   | 17 || 18 | 1 | OUT  | GPIO. 5 | 5   | 24  |
 |  10 |  12 |    MOSI |  OUT | 0 | 19 || 20 |   |      | 0v      |     |     |
 |   9 |  13 |    MISO | ALT0 | 0 | 21 || 22 | 1 | OUT  | GPIO. 6 | 6   | 25  |
 |  11 |  14 |    SCLK |  OUT | 0 | 23 || 24 | 1 | OUT  | CE0     | 10  | 8   |
 |     |     |      0v |      |   | 25 || 26 | 1 | OUT  | CE1     | 11  | 7   |
 |   0 |  30 |   SDA.0 |   IN | 1 | 27 || 28 | 1 | IN   | SCL.0   | 31  | 1   |
 |   5 |  21 | GPIO.21 |   IN | 1 | 29 || 30 |   |      | 0v      |     |     |
 |   6 |  22 | GPIO.22 |   IN | 1 | 31 || 32 | 0 | IN   | GPIO.26 | 26  | 12  |
 |  13 |  23 | GPIO.23 |   IN | 0 | 33 || 34 |   |      | 0v      |     |     |
 |  19 |  24 | GPIO.24 |   IN | 0 | 35 || 36 | 0 | IN   | GPIO.27 | 27  | 16  |
 |  26 |  25 | GPIO.25 |   IN | 0 | 37 || 38 | 0 | IN   | GPIO.28 | 28  | 20  |
 |     |     |      0v |      |   | 39 || 40 | 0 | IN   | GPIO.29 | 29  | 21  |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 +-----+-----+---------+------+---+-Pi ZeroW-+---+------+---------+-----+-----+
```

### Power supply

Connect GPIO pin 4 (+5V) to the LCD's VDD pin and GPIO pin 6 (GND) to the LCD's VSS pin.

### Pins connections

Folows this scheme (using physical pin numbering on Raspberry Pi GPIO):

```python
LCD_D4 = 15
LCD_D5 = 16
LCD_D6 = 18
LCD_D7 = 22
LCD_E  = 11
LCD_RS = 13
```

### Contrast adjustment

Althought optional, a 10kΩ potentionmeter might be needed to adjust the contrast of the LCD (in Hanoi, get the 3362P square potentionmeter in any shop). Connect pin 1 of the potentionmeter to the +5V power supply, pin 3 to the ground, and pin 2 to the V0 (contrast) pin of the LCD.

### Usage

```sh
Syntax: lcd-16x2-mono-simple [OPTION] [LINE1] [LINE2]
OPTION:
-h                      Display this help and exit.
-c                      Clear the LCD.
-d                      Run a demo.
-1 text Text to display on line 1.
-2 text Text to display on line 2.
```

## lcd-16x2-mono

Display text onto a 16x2 monochrome LCD screen. Based on this [Drive a 16x2 LCD with the Raspberry Pi](https://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi/overview). Tested on a Raspberry Pi Zero W.

Use the same wiring scheme as `lcd-16x2-mono-simple` above.

This program requires Python 3 and `adafruit-circuitpython-charlcd` package. Install it with `pip3 install adafruit-circuitpython-charlcd`.

Usage:

```
Syntax: lcd-16x2-mono [OPTION] [LINE1] [LINE2]
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

## lcdserver

Run a network server and serve requests from clients to control the attached LCD. Requires root priviledge.

This program need `ncat`, and `lcd-16x2-mono-simple` symlinked or renamed as `lcd` on system PATH.

Usage:

```sh
sudo ./lcdserver server 127.0.0.1 1234
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

To enable logging, add "log" at the end of command. The server's log is at `/var/log/lcdserver.log`.

To run this server at boot, use `/etc/rc.local` or create a service file `/etc/systemd/system/lcdserver.service` like this (assumming path to this server is at `/usr/local/bin/lcdserver`):

```systemd
[Unit]
Description=Listen and display on attached LCD
Wants=network-online.target
After=network-online.target

[Service]
User=peter
Group=peter
ExecStart=/usr/local/bin/lcdserver server 0.0.0.0 1234
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

## lcd-128x64-ST7920

Control the 128x64 LCD with ST7290 driver. Bases on [RPi-12864-LCD-ST7920-lib](https://github.com/SrBrahma/RPi-12864-LCD-ST7920-lib).

### Pins connections

Folows this scheme (using physical pin numbering on Raspberry Pi GPIO):

```python
# 1  GND -> Ground
# 2  VCC -> +5V
# 3  VO  -> +5V with 10K potentionmeter to adjust contrast
# 4  RS  -> GPIO8 (SPI0 CE0)
# 5  R/W -> GPIO10 (SPI0 MOSI)
# 6  E   -> GPIO11 (SPI0 SCLK)
# 7  PSB -> Ground (set SPI mode)
# 8  RST -> GPIO25
# 9  A   -> +5V 60mA for backlight anode
# 10 K   -> Ground for backlight kathode

```

