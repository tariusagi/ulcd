# Uzi's LCD library

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

## lcdserver
Run a network server and serve requests from clients to control the attached LCD. Requires root priviledge.

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

To run this server at boot, use `/etc/rc.local` or create a service file `/etc/systemd/system/lcd.service` like this (assumming path to this server is at `/usr/local/bin/lcdserver`):
```systemd
[Unit]
Description=Display various info on the attached LCD screen
After=network.service

[Service]
User=root
WorkingDirectory=/home/pi/
ExecStart=/usr/local/bin/lcdserver server 0.0.0.0 1234 log
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```
Then run:
```sh
sudo systemctl daemon-reload
sudo systemctl enable lcd
sudo systemctl start lcd
```
To start the server as a service.
