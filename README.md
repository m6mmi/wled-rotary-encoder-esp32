# WLED Rotary Encoder Remote (ESP32 + MicroPython)

This project is a WiFi-enabled rotary encoder remote for controlling WLED brightness and power state over UDP. It runs on ESP32 using MicroPython and supports deep sleep to save power. The device also features a web-based configuration portal for setting up WLED connection and WiFi credentials.

## Features

- **Adjust brightness** using a rotary encoder
- **Toggle WLED power** on/off using a button press
- **Enter deep sleep** after inactivity to conserve power
- **Wake up on button press**
- Built-in **configuration mode** with WiFi AP and web server for setting up WLED connection and WiFi credentials
- Configuration stored in a **JSON file** (`wled_config.json`)
- **RTC memory** preserves brightness and power state across deep sleep cycles

## Hardware Requirements

- **ESP32** (any model with enough pins)
- **Rotary Encoder** (with CLK, DT, and BTN pins)
- **MicroPython firmware** (tested with MicroPython 1.21 or newer)

## Pinout

| Function             | ESP32 Pin  |
|----------------------|------------|
| Rotary Encoder CLK   | GPIO 34    |
| Rotary Encoder DT    | GPIO 35    |
| Rotary Encoder BTN   | GPIO 33    |

## Configuration Workflow

1. On first boot (or if WiFi connection fails), the device enters **AP Mode**.
2. Connect to the WiFi network called **WLED-Config** (password: `wled-config`).
3. Open a browser and go to `http://192.168.4.1` to access the configuration page.
4. Enter the following details:
   - WLED device IP
   - UDP Port (default: `21324`)
   - WiFi SSID and password
5. Save and reboot. The device will connect to WiFi and start controlling WLED.

## Usage

- **Rotate Encoder**: Adjust brightness (0-255)
- **Press Button**: Toggle WLED on/off
- **Hold Button for 10 seconds**: Enter AP Mode to reconfigure WiFi or WLED settings
- **Inactivity Timeout (15 seconds)**: Automatically enters deep sleep to save power

## Example `wled_config.json`

```json
{
    "ip": "192.168.1.100",
    "port": 21324,
    "ssid": "YourWiFiNetwork",
    "pw": "YourWiFiPassword"
}
```
Power Saving
The device enters deep sleep after 15 seconds of inactivity and wakes up when the button is pressed. This helps conserve power, making it ideal for battery-powered applications.

Deep Sleep Flow:
Inactivity Timeout (15 seconds): After 15 seconds of no activity (e.g., no rotation or button presses), the device enters deep sleep.
Wake-Up on Button Press: The device will wake up from deep sleep as soon as the button is pressed.
RTC Memory: The device saves the last brightness level and power state using the ESP32's RTC (Real-Time Clock) memory. This ensures that the brightness and power state are preserved between sleep cycles.
Installation
Flash MicroPython firmware to your ESP32.
Upload all required files, including the main script and wled_config.json.
On first boot, configure WiFi and WLED connection via the web portal.
The device is now ready to use!

Dependencies
MicroPython modules: network, socket, machine, ujson, time, esp32
External library: rotary_irq_esp for rotary encoder handling
