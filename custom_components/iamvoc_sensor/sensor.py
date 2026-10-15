"""Platform for sensor integration."""
from __future__ import annotations

import logging
import threading

import usb.core
import usb.util

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfRatio
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

# Constants
MAX_READ_ATTEMPTS = 50  # Maximum read attempts in xfer loops (50 * 16 bytes = 800 bytes max)
RECONNECT_ATTEMPTS = 3  # Maximum reconnection attempts
USB_TIMEOUT_MS = 2000  # USB timeout in milliseconds


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
	_attr_native_unit_of_measurement = UnitOfRatio.PARTS_PER_MILLION

	def __init__(self):
		"""Initialize the sensor."""
		self._attr_native_value = None
		self._ppm = None
		self._alive = False
		self._attr_unique_id = "iamvoc_sensor_voc"
		self._usb_lock = threading.Lock()  # Thread safety for USB operations
		self._dev = None
		self._intf = 0
		self._type1_seq = 0x0001
		self._type2_seq = 0x67
		self._consecutive_errors = 0
		self._max_consecutive_errors = 5
	
	def xfer_type1(self, msg):
		"""Transfer type 1 command with safety limits."""
		in_data = bytes()
		out_data = bytes('@{:04X}{}\n@@@@@@@@@@'.format(self._type1_seq, msg), 'utf-8')
		self._type1_seq = (self._type1_seq + 1) & 0xFFFF

		try:
			self._dev.write(0x02, out_data[:16], USB_TIMEOUT_MS)
		except Exception as e:
			_LOGGER.error("iAM VOC Sensor: Write failed in xfer_type1: %s", e)
			raise

		# Read with safety limit to prevent infinite loop
		read_count = 0
		while read_count < MAX_READ_ATTEMPTS:
			try:
				ret = bytes(self._dev.read(0x81, 0x10, USB_TIMEOUT_MS))
				if len(ret) == 0:
					break
				in_data += ret
				read_count += 1
			except usb.core.USBError as e:
				if e.errno == 110:  # Timeout
					break
				_LOGGER.error("iAM VOC Sensor: Read failed in xfer_type1: %s", e)
				raise

		if read_count >= MAX_READ_ATTEMPTS:
			_LOGGER.error("iAM VOC Sensor: Max read attempts reached in xfer_type1 - device may be stuck (read %d bytes)", len(in_data))
			raise usb.core.USBError("Max read attempts exceeded")

		_LOGGER.debug("iAM VOC Sensor: xfer_type1 read %d bytes in %d attempts", len(in_data), read_count)
		return in_data.decode('iso-8859-1')
	
	def xfer_type2(self, msg):
		"""Transfer type 2 command with safety limits."""
		out_data = bytes('@', 'utf-8') + self._type2_seq.to_bytes(1, byteorder='big') + bytes('{}\n@@@@@@@@@@@@@'.format(msg), 'utf-8')
		self._type2_seq = (self._type2_seq + 1) if (self._type2_seq < 0xFF) else 0x67

		try:
			self._dev.write(0x02, out_data[:16], USB_TIMEOUT_MS)
		except Exception as e:
			_LOGGER.error("iAM VOC Sensor: Write failed in xfer_type2: %s", e)
			raise

		# Read with safety limit to prevent infinite loop
		in_data = bytes()
		read_count = 0
		while read_count < MAX_READ_ATTEMPTS:
			try:
				ret = bytes(self._dev.read(0x81, 0x10, USB_TIMEOUT_MS))
				if len(ret) == 0:
					break
				in_data += ret
				read_count += 1
			except usb.core.USBError as e:
				if e.errno == 110:  # Timeout
					break
				_LOGGER.error("iAM VOC Sensor: Read failed in xfer_type2: %s", e)
				raise

		if read_count >= MAX_READ_ATTEMPTS:
			_LOGGER.error("iAM VOC Sensor: Max read attempts reached in xfer_type2 - device may be stuck (read %d bytes)", len(in_data))
			raise usb.core.USBError("Max read attempts exceeded")

		_LOGGER.debug("iAM VOC Sensor: xfer_type2 read %d bytes in %d attempts", len(in_data), read_count)
		return in_data
	
	@property
	def alive(self):
		"""Return if device is alive."""
		return self._alive

	@alive.setter
	def alive(self, value):
		"""Set device alive status."""
		self._alive = value

	def setup(self):
		"""Initialize the USB device connection."""
		with self._usb_lock:
			self._dev = usb.core.find(idVendor=0x03eb, idProduct=0x2013)
			if self._dev is None:
				_LOGGER.error('iAM VOC Sensor: Device not found (VID:0x03eb, PID:0x2013)')
				return False

			try:
				if self._dev.is_kernel_driver_active(self._intf):
					self._dev.detach_kernel_driver(self._intf)

				self._dev.set_configuration(0x01)
				usb.util.claim_interface(self._dev, self._intf)
				self._dev.set_interface_altsetting(self._intf, 0x00)

				# Initialize device with commands
				ret = self.xfer_type1('*IDN?')
				_LOGGER.debug("iAM VOC Sensor: ID response: %s", ret)

				self._dev.write(0x02, bytes('@@@@@@@@@@@@@@@@', 'utf-8'), USB_TIMEOUT_MS)
				self.xfer_type1('KNOBPRE?')
				self.xfer_type1('WFMPRE?')
				self.xfer_type1('FLAGS?')

				self._alive = True
				self._consecutive_errors = 0
				_LOGGER.info("iAM VOC Sensor: Initialization successful")
				return True

			except Exception as e:
				_LOGGER.error("iAM VOC Sensor: Initialization failed - %s", str(e))
				# Don't reset the device - just mark as not alive
				self._alive = False
				if self._dev:
					try:
						usb.util.release_interface(self._dev, self._intf)
					except:
						pass
				return False
	
	def _reconnect(self):
		"""Attempt to reconnect to the device."""
		_LOGGER.info("iAM VOC Sensor: Attempting to reconnect...")

		# Release old device if exists
		if self._dev:
			try:
				usb.util.release_interface(self._dev, self._intf)
			except:
				pass
			self._dev = None

		# Try to reconnect
		for attempt in range(RECONNECT_ATTEMPTS):
			_LOGGER.debug("iAM VOC Sensor: Reconnection attempt %d/%d", attempt + 1, RECONNECT_ATTEMPTS)
			if self.setup():
				_LOGGER.info("iAM VOC Sensor: Reconnection successful")
				return True

		_LOGGER.error("iAM VOC Sensor: Reconnection failed after %d attempts", RECONNECT_ATTEMPTS)
		return False

	def stop(self):
		"""Clean up USB resources."""
		with self._usb_lock:
			self._alive = False
			if self._dev:
				try:
					usb.util.release_interface(self._dev, self._intf)
					_LOGGER.info("iAM VOC Sensor: USB interface released")
				except Exception as e:
					_LOGGER.error("iAM VOC Sensor: Error releasing interface - %s", str(e))
				finally:
					self._dev = None
	
	@property
	def available(self):
		"""Return if entity is available."""
		return self._alive

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
		if not self._alive:
			_LOGGER.debug("iAM VOC Sensor: Device not alive, skipping update")
			self._attr_native_value = None  # Clear value when unavailable
			return

		with self._usb_lock:
			try:
				self.xfer_type1('FLAGGET?')
				meas = self.xfer_type2('*TR')

				# Validate response length
				if len(meas) < 4:
					_LOGGER.warning("iAM VOC Sensor: Invalid response length: %d", len(meas))
					return

				self._ppm = int.from_bytes(meas[2:4], byteorder='little')
				self._attr_native_value = self._ppm
				self._consecutive_errors = 0  # Reset error counter on success
				_LOGGER.debug("iAM VOC Sensor: Updated PPM value: %s", self._ppm)

			except usb.core.USBError as e:
				self._consecutive_errors += 1
				_LOGGER.error("iAM VOC Sensor: USB error during update - %s (error count: %d)",
							 str(e), self._consecutive_errors)

				# If too many consecutive errors, try to reconnect
				if self._consecutive_errors >= self._max_consecutive_errors:
					_LOGGER.warning("iAM VOC Sensor: Too many consecutive errors, attempting reconnect")
					self._alive = False
					if not self._reconnect():
						_LOGGER.error("iAM VOC Sensor: Device disconnected, will retry on next update")

			except Exception as e:
				self._consecutive_errors += 1
				_LOGGER.error("iAM VOC Sensor: Unexpected error during update - %s", str(e))

	def update(self):
		"""Fetch new state data for the sensor.

		This is the only method that should fetch new data for Home Assistant.
		"""
		self._update_values()

	async def async_will_remove_from_hass(self):
		"""Clean up when entity is removed."""
		_LOGGER.info("iAM VOC Sensor: Entity being removed, cleaning up resources")
		await self.hass.async_add_executor_job(self.stop)
