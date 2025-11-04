"""Platform for sensor integration."""
from __future__ import annotations

import logging

import usb.core
import usb.util

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.info("Setting up iAM VOC Sensor")

    def setup_sensor():
        """Set up the sensor in executor."""
        dev = iAMVOCSensor()
        dev.setup()
        return dev

    try:
        dev = await hass.async_add_executor_job(setup_sensor)
        if not dev.alive:
            _LOGGER.error("iAM VOC Sensor: Device not responding")
            return
        async_add_entities([dev], True)
        _LOGGER.info("iAM VOC Sensor: Successfully initialized")
    except Exception as err:
        _LOGGER.exception("Failed to set up iAM VOC Sensor: %s", err)

class iAMVOCSensor(SensorEntity):
	"""Representation of a Sensor."""

	_attr_has_entity_name = True
	_attr_name = None
	_attr_device_class = SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS
	_attr_state_class = SensorStateClass.MEASUREMENT
	_attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION

	def __init__(self):
		"""Initialize the sensor."""
		self._attr_native_value = None
		self._ppm = None
		self.alive = False
		self._attr_unique_id = "iamvoc_sensor_voc"
	
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
	
	@property
	def device_info(self):
		"""Return device information."""
		return {
			"identifiers": {("iamvoc_sensor", "iamvoc_usb")},
			"name": "iAM VOC Sensor",
			"manufacturer": "AppliedSensor",
			"model": "iAQ-Stick",
			"sw_version": "1.0",
		}

	def _update_values(self):
		"""Update sensor values from device."""
		try:
			self.xfer_type1('FLAGGET?')
			meas = self.xfer_type2('*TR')
			self._ppm = int.from_bytes(meas[2:4], byteorder='little')
			self._attr_native_value = self._ppm
			_LOGGER.debug("iAM VOC Sensor: Updated PPM value: %s", self._ppm)
		except Exception as e:
			_LOGGER.error("iAM VOC Sensor: Update failed - %s", str(e))

	def update(self):
		"""Fetch new state data for the sensor.

		This is the only method that should fetch new data for Home Assistant.
		"""
		self._update_values()
