#!/usr/bin/python2
#-*- coding: utf-8 -*-
u'''
http://www.rpiblog.com/2012/09/using-gpio-of-raspberry-pi-to-blink-led.html
https://github.com/if1live/rpi-mpd-controller
http://nw-electric.way-nifty.com/blog/2014/10/raspberrypi-vol.html
http://akizukidenshi.com/catalog/c/coled/
'''

''' for volumio 1.55  Pi2    OLED SO1602AW  3.3V I2C 16x2
sudo apt-get update
sudo apt-get -y install python-smbus
echo "i2c-dev" >> /etc/modules
echo "dtparam=i2c_arm=on" >> /boot/config.txt
'''

#import RPi.GPIO as GPIO
import time
import commands
import smbus
import sys
#from daemon import daemon 
#from daemon.pidlockfile import PIDLockFile  

STOP = 0
PLAY = 1
PAUSE = 2
ERROR = 3
MSTOP = 3    # Scroll motion stop time 

class i2c(object):
    def __init__(self):
        self.bus = smbus.SMBus(1)
        self.addr = 0x3c          # i2s address
        self.state = STOP         # state
        self.shift = 0            # Scroll shift value
        self.retry = 20           # retry for init
        self.old_line1 = " "      # old str 1
        self.old_line2 = " "      # old str 2
        self.init()

# initialize OLED 
    def init(self):
        while self.retry > 0:
            try:
                self.bus.write_byte_data(self.addr, 0, 0x0c) # Display ON
            except IOError:
                self.retry = self.retry -1
                time.sleep(0.5)
            else:
                return 0
        else:
            sys.exit()
        
# line1 send ascii data 
    def line1(self, str):
        if str != self.old_line1:
            self.old_line1 = str
        else:
            return 0
        try:
            self.bus.write_byte_data(self.addr, 0, 0x80) 
            vv = map(ord, list(str))
            self.bus.write_i2c_block_data(self.addr, 0x40, vv)
        except IOError:
            return -1

# line2 send ascii data and Scroll 
    def line2(self, str, sp):
        try:
            self.bus.write_byte_data(self.addr, 0, 0xA0) 
            self.maxlen = len(str) +MSTOP
            if sp < MSTOP:
               sp = 0
            else:
               sp = sp -MSTOP -1
            if self.maxlen > sp + 16:
                self.maxlen = sp + 16
        
            moji = str[sp:self.maxlen]
            moji = map(ord, moji)
            self.bus.write_i2c_block_data(self.addr, 0x40, moji) 
        except IOError:
            return -1

# Display Control 
    def disp(self):
        # mpc command Send and Receive
        st = commands.getoutput('mpc | kakasi -Ja -Ha -Ka -Ea -s -i utf-8 -o utf-8')
        line_list = st.splitlines()
        
        # stop
        if len(line_list) <= 1:
            if line_list[0].startswith(r"error:"):
                self.line1("Music           ")
                self.line2("  Player Daemon ", 0)
                time.sleep(0.3)
                self.state = ERROR
                #return 0
            else:
                self.state = STOP
        
        # play pause 
        for line in range(0,len(line_list)):
            if line_list[line].startswith(r"[playing]"):
                self.state = PLAY
            elif line_list[line].startswith(r"[paused]"):
                self.state = PAUSE
        
        # Volume and status for Line1 
        if self.state == STOP:
            vvv = line_list[0][7:11]           # Volume vvv% 
            self.line1("STOP    Vol:"+vvv)
            self.line2("                ", 0)
            self.old_line2 = " "
        elif self.state == PLAY:
            vvv = line_list[2][7:11]
            self.line1("PLAY    Vol:"+vvv)
        elif self.state == PAUSE:
            vvv = line_list[2][7:11]
            self.line1("PAUSE   Vol:"+vvv)
        
        # music name for Line2 
        if self.state is PLAY or self.state is PAUSE:
            if line_list[0]+" " != self.old_line2:
                self.old_line2  = line_list[0]+" "
                self.shift = 0
                self.line2("                ", 0)
            self.line2(self.old_line2, self.shift)
        
        self.shift = self.shift + 1
        if self.shift > (len(self.old_line2) +MSTOP):
            self.shift = 0


def main():
    oled = i2c()

    while True:
        oled.disp()
        time.sleep(0.2)

if __name__ == '__main__':
#    with daemon.DaemonContext(pidfile=PIDLockFile('/var/run/oled_ctrl.pid')):
        main()

