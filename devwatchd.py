#!/usr/bin/env python

from daemonbase import Daemon
import subprocess
import sys, time
import re

class NWDaemon(Daemon):
	
	WIRED = 'wired'
	WIRELESS = 'wireless'
	
	DEV_WIRED = 'eth0'
	#DEV_WIRELESS = 'eth2'
	DEV_WIRELESS = 'wlan0'
	
	connection = None
	ap_mode = None
	
	def stateWrite(self, statestring):
		with open('/tmp/nwstate', 'w+') as f:
			f.write(statestring + '\n')
	
	def isConnected(self, devstring):
		state = ''
		try:
			state = subprocess.check_output(['cat', '/sys/class/net/'+devstring+'/operstate'],
											  stderr=subprocess.STDOUT)
			state = state.strip()
			if state == 'up':
				return True
			else:
				return False
		except subprocess.CalledProcessError:
			print 'Error: can\'t get state of device '+devstring+' - check dev config'
			return False
			
	def setApMode(self, active):
		# replace by actual commands
		command = ''
		if active:
			command = 'restart'
		else:
			command = 'stop'
		print 'sudo service hostapd ' + command
		print 'sudo service  ' + command
			
	def disableWireless(self):
		print 'disabling wireless'
		self.setApMode(False)
		self.ap_mode == None
		
	def ipToLcd(self, devicename):
		ipout = subprocess.check_output(['sudo','ip', 'addr', 'show', devicename],
											  stderr=subprocess.STDOUT)
		
		m = re.search(r'inet\s([\d\.]+)/\d+', ipout, re.MULTILINE)
		if m:
			ipaddr = m.group(1)
			subprocess.call(['sudo','python', '/home/pi/mrbeam_lcd/message_shot.py', 'Got to', ipaddr])
		
	def enableWireless(self, is_connected):
		print 'enabling wireless'
		
		state = subprocess.check_output(['cat', '/etc/network/interfaces'],
											  stderr=subprocess.STDOUT)
											  
		m = re.search(r'iface\s+'+re.escape(self.DEV_WIRELESS)+r'\s+inet\s+(.*)$', state, re.MULTILINE)
		print m.group(0)
		mode = m.group(1)
		
		if mode == 'static':
			if self.ap_mode == None or self.ap_mode == False:
				self.ap_mode = True
				print 'activating ap mode'
				self.setApMode(True)
			else:
				print 'ap mode already active'
			
		elif mode == 'manual':
			if self.ap_mode:
				self.ap_mode = False
				print 'deactivating ap mode'
				self.setApMode(False)
			else:
				# now check if the wifi is connected
				m = re.search(r'wpa-ssid\s+\"(.*)\"$', state, re.MULTILINE)
				ssid = m.group(1)
				
				link = subprocess.check_output(['sudo', 'iw', self.DEV_WIRELESS, 'link'],
													  stderr=subprocess.STDOUT)
				
				print 'wifi client mode active'
				m = re.search(r'Connected to', link, re.MULTILINE)
				if m:
					print 'wifi connected as client'
					self.ipToLcd(self.DEV_WIRELESS)
				else:
					print 'wifi not yet connected, scanning for wifi'
					scan = subprocess.check_output(['sudo', 'iw', self.DEV_WIRELESS, 'scan'],
														  stderr=subprocess.STDOUT)
					m = re.search(r'SSID:\s+(.*)$', scan, re.MULTILINE)
					if m:
						print 'wifi could not be found'
					else:
						print 'wifi scan successfull, waiting for connection'
					
		else:
			print 'unsupported device config: ' + mode
		
	
	def run(self):
		while True:
			wired_connected = self.isConnected(self.DEV_WIRED)
			wireless_connected = self.isConnected(self.DEV_WIRELESS)
			
			if wired_connected:
				if self.connection != self.WIRED:
					print 'wired connected'
					self.connection = self.WIRED
					self.disableWireless()
				else:
					print 'still wired'
				self.ipToLcd(self.DEV_WIRED)
			else:
				if self.connection != self.WIRELESS:
					print 'wireless connected'
					self.connection = self.WIRELESS
					self.enableWireless(wireless_connected)
				else:
					print 'still wireless'
				
			time.sleep(2)
	
