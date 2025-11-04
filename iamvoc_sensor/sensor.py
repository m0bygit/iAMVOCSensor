"""Platform for sensor integration."""
from __future__ import print_function
from homeassistant.helpers.entity import Entity
import usb.core
import usb.util
import sys
import signal
import time
import multiprocessing
import logging

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
	"""Set up the sensor platform."""
	_LOGGER.info("setup_platform for iAMVOCSensor")
	dev = iAMVOCSensor()
	dev.setup()
	if (not dev.alive):	
		_LOGGER.critical("iaqstick: not alive?")
	else:
		add_entities([dev])
		_LOGGER.info("iaqstick: running")

class iAMVOCSensor(Entity):
	"""Representation of a Sensor."""

	def __init__(self):
		"""Initialize the sensor."""
		self._ppm = None
		self.alive = False
	
	def xfer_type1(self, msg):
#		_LOGGER.info("xfer_type1")
		in_data = bytes()
		out_data = bytes('@{:04X}{}\n@@@@@@@@@@'.format(self._type1_seq, msg), 'utf-8')
		self._type1_seq = (self._type1_seq + 1) & 0xFFFF
#		_LOGGER.info("xfer_type1(0x02, " + str(out_data[:16]) + ", 1000)")
#		ret = self._dev.write(0x02, out_data[:16], self._intf, 1000)  # remove param _self._intf for other versions of pyusb?
		ret = self._dev.write(0x02, out_data[:16], 1000)  # remove param _self._intf for other versions of pyusb?
#		_LOGGER.info("post self._dev.write()")
		while True:
#			ret = bytes(self._dev.read(0x81, 0x10, self._intf, 1000))
			ret = bytes(self._dev.read(0x81, 0x10, 1000))
			if len(ret) == 0:
				break
			in_data += ret
		return in_data.decode('iso-8859-1')
	
	def xfer_type2(self, msg):
		out_data = bytes('@', 'utf-8') + self._type2_seq.to_bytes(1, byteorder='big') + bytes('{}\n@@@@@@@@@@@@@'.format(msg), 'utf-8')
		self._type2_seq = (self._type2_seq + 1) if (self._type2_seq < 0xFF) else 0x67
#		ret = self._dev.write(0x02, out_data[:16], self._intf, 1000)
		ret = self._dev.write(0x02, out_data[:16], 1000)
		in_data = bytes()
		while True:
#			ret = bytes(self._dev.read(0x81, 0x10, self._intf, 1000))
			ret = bytes(self._dev.read(0x81, 0x10, 1000))
			if len(ret) == 0:
				break
			in_data += ret
		return in_data
	
	def setup(self):
		self._dev = usb.core.find(idVendor=0x03eb, idProduct=0x2013)
		if self._dev is None:
			_LOGGER.critical('iaqstick: iAQ Stick not found')
			return
#		_LOGGER.info("-------------------------test1")
		self._intf = 0
		self._type1_seq = 0x0001
		self._type2_seq = 0x67
		
		try:
#			_LOGGER.info("-------------------------test2")
			if self._dev.is_kernel_driver_active(self._intf):
				self._dev.detach_kernel_driver(self._intf)
		
#			_LOGGER.info("-------------------------test3")
			self._dev.set_configuration(0x01)
			usb.util.claim_interface(self._dev, self._intf)
			self._dev.set_interface_altsetting(self._intf, 0x00)
#			_LOGGER.info("-------------------------test4")
	
	#            print ("Device:", self._dev.filename)
	#            print ("  idVendor: %d (0x%04x)",format(self._dev.idVendor, self._dev.idVendor))
	#            print ("  idProduct: %d (0x%04x)".format(self._dev.idProduct, self._dev.idProduct))
#			manufacturer = usb.util.get_string(self._dev, 0x101, 0x409).encode('ascii')
#			product = usb.util.get_string(self._dev, 0x101, 0x409).encode('ascii')

#			_LOGGER.info("Manufacturer:", manufacturer)
#			_LOGGER.info("Serial:", str(self._dev.iSerialNumber))
#			_LOGGER.info("Product:", product)
	
	#            manufacturer = usb.util.get_string(self._dev, 0x101, 0x01) #, 0x409)
	#            print("test")
	#            product = usb.util.get_string(self._dev, 0x101, 0x02) #, 0x409)
	#            print('iaqstick: Manufacturer: ' + manufacturer + ' - Product: '+ product)
			ret = self.xfer_type1('*IDN?')
#			print(ret)
#			self._dev.write(0x02, bytes('@@@@@@@@@@@@@@@@', 'utf-8'), self._intf, 1000)
			self._dev.write(0x02, bytes('@@@@@@@@@@@@@@@@', 'utf-8'), 1000)
			ret = self.xfer_type1('KNOBPRE?')
	#            print(ret)
			ret = self.xfer_type1('WFMPRE?')
	#            print(ret)
			ret = self.xfer_type1('FLAGS?')
	#            print(ret)
		except Exception as e:
			_LOGGER.critical("iaqstick: init interface failed - " + str(e))
			self._dev.reset()
		else:
			self.alive = True
			_LOGGER.info("iaqstick: init successful")
	
	def stop(self):
		self.alive = False
		try:
			usb.util.release_interface(self._dev, self._intf)
		except Exception as e:
			_LOGGER.critical("iaqstick: releasing interface failed - " + str(e))
	
	def _update_values(self):
	   #logger.debug("iaqstick: update")
		try:
			self.xfer_type1('FLAGGET?')
			meas = self.xfer_type2('*TR')
			self._ppm = int.from_bytes(meas[2:4], byteorder='little')
	#            print('iaqstick: ppm: ' + str(self.ppm))
	       #logger.debug('iaqstick: debug?: {}'.format(int.from_bytes(meas[4:6], byteorder='little')))
	       #logger.debug('iaqstick: PWM: {}'.format(int.from_bytes(meas[6:7], byteorder='little')))
	       #logger.debug('iaqstick: Rh: {}'.format(int.from_bytes(meas[7:8], byteorder='little')*0.01))
	       #logger.debug('iaqstick: Rs: {}'.format(int.from_bytes(meas[8:12], byteorder='little')))
		except Exception as e:
			_LOGGER.critical("iaqstick: update failed - " + str(e))

	@property
	def name(self):
		"""Return the name of the sensor."""
		return 'iAM VOC Sensor'

	@property
	def state(self):
		"""Return the state of the sensor."""
		return self._ppm

	@property
	def unit_of_measurement(self):
		"""Return the unit of measurement."""
		return 'PPM'

	def update(self):
		"""Fetch new state data for the sensor.
		
		This is the only method that should fetch new data for Home Assistant.
		"""
		self._update_values()
