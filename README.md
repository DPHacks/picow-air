# Pico W Air Quality Monitoring w/ PM 2.5 Sensor
Future home of the documentation for the DPHacks Pico W Air Quality Monitor

A simple board with connection for PMS5003 particulate matter sensor and Qwiic/QT connector for more sensors. Powered, of course, by a Pico W.

## About the Pico W Air
The Pico W Air board is tiny little device that tracks PM air quality. The board has a modular design and you can add additional sensors.

The board has a connector for the Plantower PMS5003 Particulate Matter sensor, Qwiic/QT connector for I2C sensors, and a few other exposed GPIO pins.

## Features
- Connector for PMS 5003 Particulate Matter sensor. (Molex PicoBlade 0532610871)
- Qwiic/QT Connector for I2C sensors/peripherals. (JST SM04B-SRSS-TB(LF)(SN))
- 1 Red and 1 Green LED for status or any other blinking business
- 8 Pin header exposing ADC (A1), and 4 other GPIO (GP10, GP11, GP12, GP13), 3.3V, and GND
- Footprint for reset button (fits Omron B3FS-100xP button, button not placed)


## Firmware
The firmware is based on CircuitPython. The Pico W Air works as a MQTT client capable of sending all sensor data through to a MQTT broker. If MQTT is not your thing, the firmware also creates a mini web server that exposes a few api endpointss responding to requests in JSON format. The mini web server also serves a single html page with sensor data.

Suppose our Pico W has IP 10.0.0.20 and you have a PMS5003 plugged in, querying 10.0.0.20/pmdata returns the data from the PMS5003 sensor as JSON

```python
@server.route("/pmdata")
def pmdata_client(request: Request):
    """
    Serve PMS 5003 data as JSON
    """
    data = read_pms25()
    return JSONResponse(request, data)
```

## Modifying the Firmware
The firmware ships assuming that you will connect

### Settings
Wifi, MQTT, and oother options are configured in the ```settings.toml``` file.

## Pin Reference
|**Board Feature**|**Pico w**
---|---
PMS5003 Pin 1|NC
PMS5003 Pin 2|NC
PMS5003 Pin 3 (PMS_RESET)|GP08
PMS5003 Pin 4 (PMS_RX)|GP17
PMS5003 Pin 5 (PMS_TX)|GP16
PMS5003 Pin 6 (PMS_SET)|GP09
PMS5003 Pin 7 (GND)|GND
PMS5003 Pin 8 (GND)|VBUS
Qwiic Pin 1 (GND)|GND
Qwiic Pin 2 (3.3v)|3V3 OUT
Qwiic Pin 3 (SDA)|GP20
Qwiic Pin 4 (SCL)|GP21
Red LED|GP22
Green LED|GP18
Button (NP) Pin 1|RUN
Button (NP) Pin 2|GND
Header Pin 1|GP27 (aka A1)
Header Pin 2|3V3 OUT
Header Pin 3|GND
Header Pin 4|GP10
Header Pin 5|GP11
Header Pin 6|GP12
Header Pin 7|GP13
Header Pin 8|GND


