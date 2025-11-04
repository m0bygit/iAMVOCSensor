#!/usr/bin/env python3
"""
Diagnostic script to detect iAM VOC Sensor / iAQ-Stick device.

This script checks:
1. Raw USB devices with vendor/product ID
2. Serial devices (if using USB-to-serial adapter)
3. Permissions and access
"""

import sys

print("=" * 60)
print("iAM VOC Sensor Device Diagnostic")
print("=" * 60)

# Check for USB devices
print("\n1. Checking for RAW USB device (VID:0x03eb, PID:0x2013)...")
try:
    import usb.core
    dev = usb.core.find(idVendor=0x03eb, idProduct=0x2013)
    if dev:
        print("   ✓ FOUND raw USB device!")
        print(f"   - Manufacturer: {usb.util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else 'N/A'}")
        print(f"   - Product: {usb.util.get_string(dev, dev.iProduct) if dev.iProduct else 'N/A'}")
        print(f"   - Bus: {dev.bus}, Address: {dev.address}")
        print("   - This device uses RAW USB (pyusb library)")
    else:
        print("   ✗ No raw USB device found with VID:0x03eb PID:0x2013")
except ImportError:
    print("   ✗ pyusb not installed (pip3 install pyusb)")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Check for all USB devices
print("\n2. Listing ALL USB devices:")
try:
    import usb.core
    devices = usb.core.find(find_all=True)
    count = 0
    for dev in devices:
        try:
            manufacturer = usb.util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else "Unknown"
            product = usb.util.get_string(dev, dev.iProduct) if dev.iProduct else "Unknown"
            print(f"   - {dev.idVendor:04x}:{dev.idProduct:04x} - {manufacturer} - {product}")
            count += 1
        except:
            print(f"   - {dev.idVendor:04x}:{dev.idProduct:04x} - (access denied)")
            count += 1
    print(f"   Total: {count} USB devices found")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Check for serial devices (USB-to-serial adapters)
print("\n3. Checking for Serial devices (USB-to-serial adapters):")
try:
    import glob
    import os

    serial_devices = []

    # Check common serial device paths
    for pattern in ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/serial/by-id/*']:
        serial_devices.extend(glob.glob(pattern))

    if serial_devices:
        print(f"   Found {len(serial_devices)} serial device(s):")
        for dev in serial_devices:
            try:
                # Try to get symlink target for by-id devices
                if 'by-id' in dev:
                    target = os.readlink(dev)
                    print(f"   ✓ {dev} -> {target}")
                else:
                    print(f"   ✓ {dev}")
            except:
                print(f"   ✓ {dev}")
    else:
        print("   ✗ No serial devices found")

except Exception as e:
    print(f"   ✗ Error: {e}")

# Check pyserial availability
print("\n4. Checking Python Serial library:")
try:
    import serial
    import serial.tools.list_ports

    print("   ✓ pyserial is installed")
    ports = serial.tools.list_ports.comports()
    if ports:
        print(f"   Found {len(ports)} serial port(s):")
        for port in ports:
            print(f"   - {port.device}")
            print(f"     VID:PID: {port.vid:04x}:{port.pid:04x}" if port.vid else "     (no USB info)")
            print(f"     Description: {port.description}")
            print(f"     Manufacturer: {port.manufacturer}")
    else:
        print("   ✗ No serial ports detected")

except ImportError:
    print("   ✗ pyserial not installed (pip3 install pyserial)")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("SUMMARY:")
print("=" * 60)
print("""
If you found your device:
  - As RAW USB (step 1): Integration should work as-is
  - As Serial device (step 3/4): Integration needs to be updated for serial

If device NOT found:
  1. Ensure device is physically connected
  2. Check 'lsusb' output in terminal
  3. Check permissions (udev rules may be needed)
  4. Try different USB port
  5. Check dmesg for connection errors

For the iAQ-Stick specifically:
  - Original device uses RAW USB (libusb/pyusb)
  - Some clones or variants may use serial adapter
  - Check device documentation
""")
