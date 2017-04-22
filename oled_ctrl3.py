#!/usr/bin/python
#-*- coding: utf-8 -*-
u'''
http://nw-electric.way-nifty.com/blog/2016/08/volumio2i2coled.html
http://www.rpiblog.com/2012/09/using-gpio-of-raspberry-pi-to-blink-led.html
https://github.com/if1live/rpi-mpd-controller
http://nw-electric.way-nifty.com/blog/2014/10/raspberrypi-vol.html
http://akizukidenshi.com/catalog/c/coled/
'''

''' for volumio2   Pi2   OLED SO1602AW  3.3V I2C 16x2
sudo apt-get update
sudo apt-get install python-smbus kakasi
'''
import time
import commands
import smbus
import sys
import re

STOP = 0
PLAY = 1
PAUSE = 2
MSTOP = 1    # Scroll motion stop time 

class i2c(object):
    def __init__(self):
        self.bus = smbus.SMBus(1)
        self.addr = 0x3c          # OLED i2s address
        self.state = STOP         # state
        self.shift = 0            # Scroll shift value
        self.retry = 20           # retry for initialize
        self.old_line1 = " "      # old str 1
        self.old_line2 = " "      # old str 2
        self.old_vol = " "        # old volume
        self.init()

# initialize OLED 
    def init(self):
        while self.retry > 0:
            try:
                self.bus.write_byte_data(self.addr, 0, 0x0c) # Display ON
                self.line1("Music           ")
                self.line2("  Player Daemon ",0)
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
        st = commands.getoutput('mpc | kakasi -Jk -Hk -Kk -Ea -s -i utf-8 -o sjis')
        #st = commands.getoutput('mpc | kakasi -Ja -Ha -Ka -Ea -s -i utf-8 -o utf-8')
        line_list = st.splitlines()
        
        # stop
        if (len(line_list)==1) and line_list[0].startswith(r"error:") \
            or (len(line_list)==2) and line_list[1].startswith(r"ERROR:"):
            self.line1("MPD Status Error")
            self.line2("                ",0)
            time.sleep(1)
            return -1
        else:
            self.state = STOP
            # get IP address
            ad = commands.getoutput('ip route')
            ad_list = ad.splitlines()
            addr_line = re.search('\d+\.\d+\.\d+\.\d+.$', ad_list[1])
            addr_str = addr_line.group()

        # play pause 
        for line in range(0,len(line_list)):
            if line_list[line].startswith(r"[playing]"):
                self.state = PLAY
            elif line_list[line].startswith(r"[paused]"):
                self.state = PAUSE

        # Volume string
        if self.state is not STOP:
            try:
                vvv = line_list[2][7:11]
            except IOError:
                return -1
        else:
            vvv = line_list[0][7:11]
            if len(vvv) > 3:
                vvv = '0 '
        if self.old_vol != vvv+" ":
            self.old_vol = vvv+" "
            self.vol_disp = 5
        else:
            if self.vol_disp != 0:
                self.vol_disp = self.vol_disp -1

        # Plaing time
        if self.state is not STOP:
            ti_line = re.search('\d+:\d\d' , line_list[1])
            ti_str  = ti_line.group()
        
        # Volume and status for Line1 
        if self.state == STOP:
            if self.vol_disp != 0:
                self.line1("STOP    Vol:"+vvv)
            else:
                self.line1("STOP             ")
            
            self.line2(addr_str+"        ",0)
            self.old_line2 = " "
        elif self.state == PLAY:
            if self.vol_disp != 0:
                self.line1("PLAY    Vol:"+vvv)
            else:
                self.line1("PLAY      "+ti_str+"  ")
        elif self.state == PAUSE:
            if self.vol_disp != 0:
                self.line1("PAUSE   Vol:"+vvv)
            else:
                self.line1("PAUSE     "+ti_str+"  ")
        
        # music name for Line2 
        if self.state is not STOP:
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
    netlink = False
    
    while netlink is False:
        ip = commands.getoutput('ip route')
        ip_list = ip.splitlines()
        if len(ip_list) >= 1:
            netlink = True
        else:
            time.sleep(1)

    while True:
        oled.disp()
        time.sleep(0.25)

if __name__ == '__main__':
        main()
