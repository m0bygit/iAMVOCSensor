# iAM VOC Sensor Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/m0bygit/iAMVOCSensor.svg)](https://github.com/m0bygit/iAMVOCSensor/releases)
[![License](https://img.shields.io/github/license/m0bygit/iAMVOCSensor.svg)](LICENSE)

This custom integration allows you to monitor air quality using the iAM VOC Sensor (iAQ-Stick) USB device in Home Assistant.

## About the iAM VOC Sensor

The iAM VOC Sensor (also known as iAQ-Stick) is a USB-based air quality monitoring device that measures Volatile Organic Compounds (VOCs) in parts per million (PPM). This integration provides real-time air quality data directly in your Home Assistant dashboard.

**Device Specifications:**
- **Vendor ID:** 0x03eb
- **Product ID:** 0x2013
- **Manufacturer:** AppliedSensor
- **Model:** iAQ-Stick
- **Measurement:** VOC concentration in PPM

## Features

- 🔌 **Easy Setup**: Configure directly from the Home Assistant UI
- 📊 **Real-time Monitoring**: Track VOC levels in parts per million
- 🏠 **Native Integration**: Works seamlessly with Home Assistant's sensor platform
- 🔄 **Automatic Updates**: Regular polling of sensor data
- 📈 **Statistics Support**: Compatible with Home Assistant's long-term statistics
- 🎨 **Device Page**: Dedicated device page in Home Assistant UI

## Installation

### HACS Installation (Recommended)

1. **Add Custom Repository:**
   - Open HACS in your Home Assistant instance
   - Click on "Integrations"
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add the repository URL: `https://github.com/m0bygit/iAMVOCSensor`
   - Select category: "Integration"
   - Click "Add"

2. **Install the Integration:**
   - Search for "iAM VOC Sensor" in HACS
   - Click "Download"
   - Restart Home Assistant

### Manual Installation

1. Copy the `iamvoc_sensor` directory to your `custom_components` directory:
   ```
   custom_components/
   └── iamvoc_sensor/
       ├── __init__.py
       ├── config_flow.py
       ├── manifest.json
       ├── sensor.py
       └── strings.json
   ```

2. Restart Home Assistant

## Configuration

### Prerequisites

- iAM VOC Sensor (iAQ-Stick) USB device
- USB device must be accessible by the Home Assistant host
- For Docker/Container setups, ensure USB device passthrough is configured

### Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "iAM VOC Sensor"
4. Click on the integration to set it up
5. The integration will automatically detect your USB device

If the device is not found, ensure:
- The USB device is properly connected
- Your system has the necessary USB permissions
- The pyusb library can access the device

### USB Permissions (Linux)

If you're running Home Assistant OS or Supervised, USB access should work automatically. For other installations, you may need to set up udev rules:

1. Create a udev rule file:
   ```bash
   sudo nano /etc/udev/rules.d/99-iamvoc.rules
   ```

2. Add the following content:
   ```
   SUBSYSTEM=="usb", ATTR{idVendor}=="03eb", ATTR{idProduct}=="2013", MODE="0666"
   ```

3. Reload udev rules:
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

4. Restart Home Assistant

### Docker Configuration

If running Home Assistant in Docker, add the USB device to your docker-compose.yml:

```yaml
services:
  homeassistant:
    ...
    devices:
      - /dev/bus/usb:/dev/bus/usb
    privileged: true  # Only if necessary
```

Or use the `--device` flag:
```bash
docker run -d \
  --name homeassistant \
  --device /dev/bus/usb \
  ...
```

## Usage

Once configured, the integration will create a sensor entity:

- **Entity ID:** `sensor.iam_voc_sensor_volatile_organic_compounds_parts`
- **Device Class:** Volatile Organic Compounds
- **Unit:** PPM (Parts Per Million)

### Example Automation

```yaml
automation:
  - alias: "Alert on High VOC Levels"
    trigger:
      - platform: numeric_state
        entity_id: sensor.iam_voc_sensor_volatile_organic_compounds_parts
        above: 1000
    action:
      - service: notify.mobile_app
        data:
          title: "Air Quality Alert"
          message: "VOC levels are high: {{ states('sensor.iam_voc_sensor_volatile_organic_compounds_parts') }} PPM"
```

### Example Dashboard Card

```yaml
type: sensor
entity: sensor.iam_voc_sensor_volatile_organic_compounds_parts
graph: line
name: Indoor Air Quality
detail: 2
```

### VOC Level Guidelines

- **< 300 PPM:** Good air quality
- **300-1000 PPM:** Acceptable air quality
- **1000-3000 PPM:** Moderate air quality, consider ventilation
- **> 3000 PPM:** Poor air quality, ventilation recommended

## Troubleshooting

### Device Not Found

**Problem:** Integration shows "cannot_connect" error during setup.

**Solutions:**
1. Verify the USB device is connected: `lsusb | grep 03eb:2013`
2. Check Home Assistant logs for USB errors
3. Ensure proper USB permissions (see USB Permissions section)
4. Try disconnecting and reconnecting the device
5. Restart Home Assistant

### Sensor Shows "Unavailable"

**Problem:** Sensor entity shows as unavailable after setup.

**Solutions:**
1. Check Home Assistant logs: **Settings** → **System** → **Logs**
2. Look for errors containing "iAM VOC Sensor" or "iaqstick"
3. Verify USB device is still connected
4. Try reloading the integration
5. If persistent, remove and re-add the integration

### Permission Denied Errors

**Problem:** Logs show "Permission denied" when accessing USB device.

**Solutions:**
1. Set up udev rules (see USB Permissions section)
2. Add Home Assistant user to `dialout` group:
   ```bash
   sudo usermod -a -G dialout homeassistant
   ```
3. For Docker, ensure `--privileged` flag or proper device mounting

### Container/Docker Issues

**Problem:** Device not accessible in containerized environment.

**Solutions:**
1. Ensure USB device passthrough is configured
2. Add `--device /dev/bus/usb` to Docker run command
3. For Docker Compose, add device mapping
4. Consider using `--privileged` mode (less secure but simpler)

## Development

### Requirements

- Home Assistant 2023.1.0 or newer
- Python 3.9+
- pyusb 1.3.1

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

If you encounter issues or have questions:

- **Issues:** [GitHub Issues](https://github.com/m0bygit/iAMVOCSensor/issues)
- **Discussions:** [GitHub Discussions](https://github.com/m0bygit/iAMVOCSensor/discussions)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- Original sensor communication code based on iAQ-Stick USB protocol
- Integration structure follows Home Assistant best practices

## Changelog

### Version 1.0.0 (2025-11-04)

- Initial release
- UI-based configuration
- HACS support
- Real-time VOC monitoring
- Device page integration
- Statistics support

---

**Note:** This is a third-party integration and is not officially affiliated with AppliedSensor or the iAQ-Stick manufacturer.
