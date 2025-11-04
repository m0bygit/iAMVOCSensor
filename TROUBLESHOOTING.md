# Troubleshooting iAM VOC Sensor Integration

## Integration Not Showing in UI / Cannot Add from UI

If you see "This integration cannot be added from the UI" or don't see the integration icon:

### Step 1: Verify Installation Location

After installing via HACS, check that files are in the correct location:

```bash
ls -la config/custom_components/iamvoc_sensor/
```

You should see:
- `__init__.py`
- `config_flow.py`
- `manifest.json`
- `sensor.py`
- `strings.json`
- `icon.png`
- `translations/en.json`

### Step 2: Full Home Assistant Restart

**IMPORTANT:** You must perform a **FULL RESTART** (not just reload):

1. Go to **Settings** → **System** → **Restart**
2. Click **Restart Home Assistant**
3. Wait for the restart to complete (1-2 minutes)

**Note:** Quick reload or reloading integrations is NOT sufficient!

### Step 3: Clear Browser Cache

After restart, clear your browser cache:

**Chrome/Edge:**
- Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (Mac)
- Select "Cached images and files"
- Click "Clear data"
- Refresh Home Assistant page (`Ctrl+F5` or `Cmd+Shift+R`)

**Firefox:**
- Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (Mac)
- Select "Cache"
- Click "Clear Now"
- Refresh Home Assistant page

**Safari:**
- `Cmd+Option+E` to empty cache
- Refresh page

### Step 4: Check Home Assistant Logs

Look for errors related to the integration:

1. Go to **Settings** → **System** → **Logs**
2. Search for "iamvoc" or "iAM VOC"
3. Look for any red error messages

Common errors and solutions:

#### Error: "No module named 'usb'"
```
Solution: The pyusb library failed to install. Check your Home Assistant setup method:
- Home Assistant OS: Should auto-install (restart required)
- Docker: May need to rebuild container
- Core/Manual: Run: pip3 install pyusb==1.3.1
```

#### Error: "USBError: [Errno 13] Access denied"
```
Solution: USB permission issues. See USB Permissions section in README.md
```

#### Error: "Setup failed for iamvoc_sensor"
```
Solution: Check the full error message for details. Common causes:
- USB device not connected
- Permission issues
- Missing dependencies
```

### Step 5: Reinstall via HACS

If the above steps don't work:

1. **Remove Integration:**
   - HACS → Integrations → iAM VOC Sensor
   - Click three dots → Remove
   - Restart Home Assistant

2. **Delete Old Files (if present):**
   ```bash
   rm -rf config/custom_components/iamvoc_sensor/
   ```

3. **Reinstall:**
   - HACS → Integrations → Explore & Download Repositories
   - Search "iAM VOC Sensor"
   - Download
   - **Restart Home Assistant** (full restart)

4. **Clear Browser Cache** (see Step 3)

5. **Try Adding Integration:**
   - Settings → Devices & Services → Add Integration
   - Search "iAM VOC Sensor"

### Step 6: Manual Installation Test

To verify the integration files are correct, try manual installation:

1. **Download the latest release** or clone the repo
2. **Copy files** to Home Assistant:
   ```bash
   cp -r custom_components/iamvoc_sensor config/custom_components/
   ```
3. **Verify files copied:**
   ```bash
   ls -la config/custom_components/iamvoc_sensor/
   ```
4. **Full restart** Home Assistant
5. **Try adding** via UI

## Icon Not Showing

If the integration appears but without an icon:

### Check Icon File
```bash
ls -lh config/custom_components/iamvoc_sensor/icon.png
```

Should show: `~12K icon.png`

If missing:
1. Download `icon.png` from the repository
2. Place in `config/custom_components/iamvoc_sensor/`
3. Restart Home Assistant
4. Clear browser cache

### Browser Cache Issue
Icons are heavily cached by browsers:
1. Hard refresh: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)
2. Or clear cache completely (see Step 3 above)
3. Try a different browser or incognito mode

## USB Device Issues

### Device Not Detected

1. **Verify USB Connection:**
   ```bash
   lsusb | grep 03eb:2013
   ```
   Should show: `Bus XXX Device XXX: ID 03eb:2013`

2. **Check USB Permissions:**
   - See "USB Permissions" section in README.md
   - Add udev rules for the device

3. **Reconnect Device:**
   - Unplug USB device
   - Wait 5 seconds
   - Plug back in
   - Check `dmesg` for connection messages

### Home Assistant OS Specific

If running Home Assistant OS:
1. Go to **Settings** → **System** → **Hardware**
2. Check if USB device appears
3. If not shown, try a different USB port
4. Consider using a powered USB hub

### Docker Specific

Ensure USB device is passed through:

**docker-compose.yml:**
```yaml
services:
  homeassistant:
    devices:
      - /dev/bus/usb:/dev/bus/usb
    privileged: true  # May be needed
```

**Docker command:**
```bash
docker run -d \
  --name homeassistant \
  --device /dev/bus/usb \
  ...
```

After changing Docker configuration:
1. Recreate container
2. Restart Home Assistant

## Still Having Issues?

### Gather Debug Information

1. **Check HA Version:**
   - Settings → About
   - Must be 2024.1.0 or newer

2. **Check Logs:**
   - Settings → System → Logs
   - Look for "iamvoc_sensor" errors
   - Copy full error message

3. **Check HACS:**
   - HACS → Integrations → iAM VOC Sensor
   - Verify version installed
   - Check for updates

4. **Verify USB Device:**
   ```bash
   lsusb -v -d 03eb:2013
   ```

### Report Issue

Open an issue on GitHub with:
- Home Assistant version
- Installation method (HACS/manual)
- Full error logs from Settings → System → Logs
- Output of `lsusb | grep 03eb:2013`
- Steps you've already tried

GitHub Issues: https://github.com/m0bygit/iAMVOCSensor/issues

## Quick Checklist

Before reporting an issue, verify:

- [ ] Home Assistant version is 2024.1.0 or newer
- [ ] Integration installed via HACS or manual copy
- [ ] **Full restart** performed (not quick reload)
- [ ] Browser cache cleared
- [ ] USB device connected (`lsusb` shows device)
- [ ] USB permissions configured (if on Linux)
- [ ] Logs checked for specific errors
- [ ] Tried reinstalling integration
- [ ] Tried different browser or incognito mode

## Common Solutions Summary

| Problem | Solution |
|---------|----------|
| "Cannot add from UI" | Full HA restart + clear browser cache |
| No icon | Clear browser cache, verify icon.png exists |
| "Device not found" | Check USB connection and permissions |
| "No module named 'usb'" | Wait for pyusb install, then restart |
| Already configured | Remove old entry first |
| Permission denied | Add udev rules, check Docker device pass-through |
