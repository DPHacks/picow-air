# Pico W Air Quality Monitoring w/ PM 2.5 Sensor
A simple board with connection for PMS5003 particulate matter sensor and Qwiic/QT connector for more sensors. Powered, of course, by a Pico W.

![Pico W Air with PM Air Quality Sensor](img/Pico_air-8.jpg?raw=true "Pico W Air")

## About the Pico W Air
The Pico W Air board is tiny little device that tracks PM air quality. The board has a modular design and you can add additional sensors.

The board has a connector for the Plantower PMS5003 Particulate Matter sensor, Qwiic/QT connector for I2C sensors, and a few other exposed GPIO pins.

No Soldering required!

**You can purchase the Pico W Air board from the DPHack's Tindie Store.**

<a href="https://www.tindie.com/stores/dphacks/?ref=offsite_badges&utm_source=sellers_DPHACKS&utm_medium=badges&utm_campaign=badge_large"><img src="https://d2ss6ovg47m0r5.cloudfront.net/badges/tindie-larges.png" alt="I sell on Tindie" width="200" height="104"></a>

## Features
- Raspberry Pi Pico W Onboard
- Connector for PMS5003 Particulate Matter sensor. (Molex PicoBlade 0532610871)
- Qwiic/QT Connector for I2C sensors/peripherals. (JST SM04B-SRSS-TB(LF)(SN))
- 1 Red and 1 Green LED for status or any other blinking business
- 8 Pin header exposing ADC (A1), and 4 other GPIO (GP10, GP11, GP12, GP13), 3.3V, and GND
- Footprint for reset button (fits Omron B3FS-100xP button, button not placed)

## Getting started
1. Before plugging any sensor, plug in the board to your computer using the micro USB port
2. Edit the file ```settings.toml``` to include your WiFi SSID and Password.
3. Unplug/power off the board and connect the PMS5003 sensor and any other sensors. It's best practive to only connect/disconnect sensors while the board is powered off to avoid shorts.

## Recommended Sensors
To take full advantage of the Pico W Air board, you should plug in a PMS5003 PM Sensor. The whole point of the Pico W Air board is to monitor ar quality in your home or outside.

Here is an Amazon (affiliate) link for available PMS5003 sensors: [PMS5003 on Amazon](https://amzn.to/48dOfNM). 

Every time someone buys (anything) through the link above, I get a small commission, which i turn support my projects. If you would like to support small maker focused companies, you can buy the sensors from one of the sellers below (not affiliated).

[Adafruit PMS5003](https://www.adafruit.com/product/3686), [Pishop PMS5003](https://www.pishop.us/product/pms5003-particulate-matter-sensor-with-cable/), [Pimoroni PMS5003](https://shop.pimoroni.com/products/pms5003-particulate-matter-sensor-with-cable?variant=29075640352851)

I also recommend connecting a temperature and humidity sensor. The AHT20 is a reliable and affordable option, but any I2C sensor with a suitable CircuitPython library should work.

The Pico Air W board has a Qwiic/QT connector making it easy to connect sensors with the same style of connector.

You can pick an HT20 sensor for around $5 from one of the sellers below (not affiliated).

[Adafruit AHT20](https://www.adafruit.com/product/4566), [Sparkfun AHT20](https://www.sparkfun.com/products/16618)

## Power Source
Power is supplied directly through the micro USB connector on the Pico W. Power draw is only 70mA to 90mA with a Plantower PMS5003 PM sensor and AHT20 temp/hum sensor connected. This means a 10000mAh power bank should keep the Pico W Air running for a little longer than 5 days.

The Pico's VSYS pin is exposed to a pad on the board, allowing for alternate power sources. VSYS should be supplied 5V.

## Firmware
The Pico W Air board ships with Firmware installed. All you have to do edit the settings is to connect it to a computer using the onboard USB port and a text editor. The firmware is based on CircuitPython, which creates a drive on your computer and lets you edit the code files directly from the microcontroller. There is no need to compile the firmware, just save the file and restart the board for changes to take effect.

The Pico W Air works as a MQTT client capable of sending all sensor data to an MQTT broker. If MQTT is not your thing, the firmware also creates a mini web server that exposes a few api endpointss responding to requests in JSON format. The mini web server also serves a single html page with sensor data.

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

### PM Sensor
The firmware ships assuming that you will be connecting a PMS5003 to the Molex PicoBlade connector but you can connect any **5v** serial sensor to the connector. Refer to the pinout table below for more information on which pins are routed through the Molex PicoBlade connector.

If you are not using the a PMS5003 sensor comment out the lines below

```python
uart = busio.UART(board.GP16, board.GP17, baudrate=9600)
pm25 = PM25_UART(uart, reset_pin)
```

### Temperature and Humidity
The board is preconfigured to use the AHT20 Temperature and Humidity sensor through I2C. This is an accurate and cost effective sensor. You can pick one up from Adafruit [AHT20 Temp and Humidity](https://www.adafruit.com/product/4566).

If you don't have a I2C sensor plugged into the Qwiic connector, make sure to comment out the lines below. 

```python
i2c = busio.I2C(board.GP21, board.GP20)
th = adafruit_ahtx0.AHTx0(i2c)
```

## Settings
Wifi, MQTT, and other options are configured in the ```settings.toml``` file. Edit this file before turning on your board for the first time. Check the ```settings.toml``` file for additional information

```python
# Configure the WiFi SSD and Password
WIFI_SSID = "<WIFI-SSID>"
WIFI_PASSWORD = "<WIFI-PASSWD>"
# MQTT Settings: Set the broker name or IP address and topic to broadcast
MQTT_BROKER = "example.local"
MQTT_TOPIC = "enviro/picowair"
```

## Loading Libraries

Adafruit has an extensive list of libraries for different modules. You can check the page below for more information on how to download and install libraries for CircuitPython

[Adafruit CircuitPython Libraries](https://circuitpython.org/libraries)

## Onboard LEDs
There are 2 LEDs on the board and an additional LED on the Pico W.

You can use these LEDs to create a simple status indicators based on sensor information. For example, you can turn on the green LED if PM 2.5 is between 0 and 5. Green and red LEDs if PM 2.5 is between 5 and 10. Red LED only if PM 2.5 is above 10.

This is configurable in the ```settings.toml``` file. The example above is pre-configured in the ```settings.toml``` file already.

```python
# Green LED
LED_G_MEASURE = "PM25"
LED_G_LOW_THRESHOLD = 0
LED_G_HIGH_THRESHOLD = 10
# Red LED
LED_R_MEASURE = "PM25"
LED_R_LOW_THRESHOLD = 5
LED_R_HIGH_THRESHOLD = 999
```

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


