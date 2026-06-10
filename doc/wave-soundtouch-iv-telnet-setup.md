# Wave SoundTouch IV — Telnet Port 17000 Setup Guide

**Status:** 🧪 Experimental — Testing in progress  
**Applies to:** Bose Wave SoundTouch IV (sm2 firmware, all versions)  
**Alternative to:** USB provisioning, ETAP serial cable

---

## Overview

The **Wave SoundTouch IV** does not support USB provisioning via the standard `remote_services` method. However, it provides **Telnet access on port 17000** with a limited but sufficient command set to configure OpenCloudTouch URLs.

This guide shows how to configure your Wave SoundTouch IV without opening the device or using special cables.

---

## Prerequisites

- Wave SoundTouch IV connected to your local network
- IP address of your Wave device (check your router or Bose SoundTouch app)
- OpenCloudTouch server running and reachable from Wave device
- Telnet client (built-in on Windows 10+, macOS, Linux)

---

## Step 1: Enable Telnet (Windows Only)

If you're on **Windows 10/11**, Telnet might be disabled by default.

**Enable it:**
1. Open **Control Panel** → **Programs** → **Turn Windows features on or off**
2. Check **Telnet Client**
3. Click **OK** and wait for installation

**Alternative:** Use **PuTTY** (download from [putty.org](https://www.putty.org/))

---

## Step 2: Connect to Wave via Telnet

Open a terminal (Command Prompt, PowerShell, macOS Terminal, or Linux shell) and connect:

```bash
telnet <wave-ip-address> 17000
```

**Example:**
```bash
telnet 192.168.1.100 17000
```

**Expected output:**
```
Trying 192.168.1.100...
Connected to 192.168.1.100.
Escape character is '^]'.
```

**⚠️ Note:** The prompt is invisible — just type commands and press Enter.

---

## Step 3: Configure OpenCloudTouch URLs

Run the following commands one by one.  
**Replace `<oct-server>` with your OpenCloudTouch server's hostname or IP address.**

### If using hostname (e.g., `opencloudtouch.local`):

```bash
sys configuration bmxRegistryUrl http://opencloudtouch.local:8080/bmx/registry/v1/services
sys configuration margeServerUrl http://opencloudtouch.local:8080/marge
sys configuration statsServerUrl http://opencloudtouch.local:8080
sys configuration swUpdateUrl http://opencloudtouch.local:8080/updates/soundtouch
envswitch boseurls set http://opencloudtouch.local:8080/marge http://opencloudtouch.local:8080/updates/soundtouch
```

### If using IP address (e.g., `192.168.1.50`):

```bash
sys configuration bmxRegistryUrl http://192.168.1.50:8080/bmx/registry/v1/services
sys configuration margeServerUrl http://192.168.1.50:8080/marge
sys configuration statsServerUrl http://192.168.1.50:8080
sys configuration swUpdateUrl http://192.168.1.50:8080/updates/soundtouch
envswitch boseurls set http://192.168.1.50:8080/marge http://192.168.1.50:8080/updates/soundtouch
```

**⚠️ Important:** Use **`http://`** (not `https://`) and include the **port** if not using 80.

---

## Step 4: Verify Configuration

Before rebooting, verify that URLs were applied correctly:

```bash
getpdo CurrentSystemConfiguration
```

**Expected output:**
```xml
<CurrentSystemConfiguration>
  <bmxRegistryUrl>http://opencloudtouch.local:8080/bmx/registry/v1/services</bmxRegistryUrl>
  <margeServerUrl>http://opencloudtouch.local:8080/marge</margeServerUrl>
  ...
</CurrentSystemConfiguration>
```

**✅ If URLs match:** Proceed to reboot.  
**❌ If URLs are wrong:** Re-run the `sys configuration` commands.

---

## Step 5: Reboot Wave

```bash
sys reboot
```

**What happens:**
- Telnet connection will close
- Wave reboots (takes ~60 seconds)
- After reboot, Wave will contact OpenCloudTouch server instead of Bose cloud

---

## Step 6: Verify in OpenCloudTouch

1. Open OpenCloudTouch web interface: `http://<oct-server>:8080`
2. Navigate to **Devices**
3. Your Wave SoundTouch IV should appear with status **Online**

**If device does NOT appear:**
- Check that OCT server is reachable from Wave's network
- Check OCT logs: `docker logs opencloudtouch-backend -f`
- Reconnect via Telnet and verify URLs with `getpdo CurrentSystemConfiguration`

---

## Troubleshooting

### Cannot connect via Telnet

**Symptom:** `Connection refused` or `Unable to connect`

**Solutions:**
1. Verify Wave is powered on and connected to network
2. Verify IP address is correct (ping the Wave: `ping <wave-ip>`)
3. Check firewall rules on your computer (allow outgoing Telnet port 17000)
4. Try from a different device (macOS/Linux if Windows fails)

### Commands not working

**Symptom:** `Command not found` or no response

**Solutions:**
1. Wave SoundTouch IV firmware **27.0.6** confirmed working
2. Older firmware (15.x, 9.x) may have limited command set
3. Try updating Wave firmware via Bose app before cloud shutdown, or:
4. Download firmware from [archive.org/details/bose-soundtouch-software-and-firmware](https://archive.org/details/bose-soundtouch-software-and-firmware)
5. Update via `http://203.0.113.1:17008/update.html` (requires factory reset first)

### Wave still contacts Bose cloud after reboot

**Symptom:** Presets don't work, OCT shows device offline

**Solutions:**
1. Reconnect via Telnet and verify URLs: `getpdo CurrentSystemConfiguration`
2. If URLs are correct but Wave ignores them: Try **factory reset** then repeat setup
3. Factory reset: Hold Wi-Fi button while plugging power cable until LED blinks (2-3 minutes)

---

## Limitations

### What works:
- ✅ TuneIn presets (via OpenCloudTouch)
- ✅ Multi-room zones
- ✅ WebSocket updates
- ✅ Device control via OCT web UI
- ✅ Spotify Connect (if configured)

### What does NOT work:
- ❌ SSH access (Wave IV does not support SSH via USB or Telnet)
- ❌ Advanced diagnostics (limited Telnet command set)
- ❌ File system access (read-only via Telnet)

---

## Advanced: ETAP Serial Cable Alternative

If Telnet does not work for your Wave, you can use the **Service Port** (3.5mm jack) with a serial UART adapter.

**Hardware needed:**
- FTDI USB-UART adapter (e.g., CP2102, FT232RL)
- 3.5mm TRRS cable (Tip-Ring-Ring-Sleeve)
- Wiring: **Tip=RX, Ring=TX, Sleeve=GND**
- Signal inversion required (configure via FT_Prog utility)

**Serial settings:**
- Baud rate: 115200
- Data bits: 8
- Parity: None
- Stop bits: 1
- Flow control: None

**Detailed guide:** See [SoundCork Issue #309](https://github.com/deborahgu/soundcork/issues/309) by @pointy56

---

## Community Success Stories

- **@pointy56** (SoundCork #309): Successfully enabled SSH via ETAP, then used Telnet 17000 for config
- **@jakovasaur** (SoundCork #309): Confirmed all Telnet commands working on Wave IV firmware 27.0.6
- **@akpdw** (SoundCork #309): Provided command syntax for SoundCork (compatible with OCT)

---

## Next Steps

1. ✅ **Set up your Wave via Telnet** (this guide)
2. ⏳ **Wait for OpenCloudTouch v1.5.2** (Telnet auto-config in wizard)
3. 🚀 **Test presets and multi-room** (report issues on GitHub)

---

## Feedback

This setup method is **experimental**. If you encounter issues or have improvements:
- Open an issue: [github.com/opencloudtouch/opencloudtouch/issues](https://github.com/opencloudtouch/opencloudtouch/issues)
- Join the discussion: [github.com/opencloudtouch/opencloudtouch/discussions](https://github.com/opencloudtouch/opencloudtouch/discussions)

**Testing Wave IV Telnet support is tracked in Issue #352.**

---

**Last updated:** 2026-06-10  
**Tested on:** Wave SoundTouch IV (sm2), firmware 27.0.6
