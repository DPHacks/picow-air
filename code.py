# MIT License

# Copyright (c) 2023 dphacks.com
# Copyright (c) 2023 André Costa

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


## Created by André Costa for dphacks.com
## Documentation is available at https://github.com/DPHacks/picow-air
## Make sure to edit the settings.toml file with WiFi credentials

import os
import time
#import ipaddress
import wifi
import socketpool
import json
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import dphacks_usaqi as USAQI

import adafruit_ahtx0
from adafruit_httpserver import (
    Server,
    Request,
    Response,
    FileResponse,
    JSONResponse,
    GET,
    POST
)

# getenv variables are setup in the ***setting.toml*** file
# These variables are replicated here for code readability only.
MQTT_ENABLED = os.getenv('MQTT_ENABLED')
MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_TOPIC = os.getenv('MQTT_TOPIC')
MQTT_PORT = os.getenv('MQTT_PORT')
MQTT_ISTLS = os.getenv('MQTT_ISTLS')
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')

INTERVAL = os.getenv('INTERVAL')

LED_R_MEASURE = os.getenv('LED_R_MEASURE')
LED_R_LOW_THRESHOLD = os.getenv('LED_R_LOW_THRESHOLD')
LED_R_HIGH_THRESHOLD = os.getenv('LED_R_HIGH_THRESHOLD')
LED_G_MEASURE = os.getenv('LED_G_MEASURE')
LED_G_LOW_THRESHOLD = os.getenv('LED_G_LOW_THRESHOLD')
LED_G_HIGH_THRESHOLD = os.getenv('LED_G_HIGH_THRESHOLD')

C_TO_F = os.getenv('C_TO_F')
SMOOTH = os.getenv('SMOOTH')

VERSION = 1.1

### PIN DEFINITIONS ###
## PICO LED
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT

## BOARD LED
## Red LED on GP22
board_led_r = DigitalInOut(board.GP22)
board_led_r.direction = Direction.OUTPUT

## Green LED on GP18
board_led_g = DigitalInOut(board.GP18)
board_led_g.direction = Direction.OUTPUT

# Header Pin 1 is connected to GPIO ADC1 (A1)
# Uncomment the code below for reading analog signal through A1
#import analogio
#adc = analogio.AnalogIn(board.A1)

### SENSOR DEFINITIONS ###

## PMS 5003
print('Setting up PM Sensor...')
from pms5003 import PMS5003

pm25 = PMS5003()
time.sleep(0.1)
pm25.cmd_mode_passive()

print('Sensor Setup!')

## Setup i2c bus for Qwiic/QT sensors
## SCL on GP21; SDA on GP20
try:
    i2c = busio.I2C(board.GP21, board.GP20)
except RuntimeError:
    print("I2C/Qwiic sensor not found")
    i2c = 0

## Add Qwiic/QT/I2C Sensors below
if i2c:
    th = adafruit_ahtx0.AHTx0(i2c) # Comment this line if not using AHT20

avgDict = {}

### SENSOR METHODS ###
def read_all():
    """
    Read all sensor data and return a single dictionary
    """
    data = {}
    data = merge_dicts(read_pms25(), data)
    data = merge_dicts(read_temp_hum(), data) # Comment this line if not using AHT20

    return data

def read_pms25():
    """
    Read air quality information from PMS5003
    """
    pmvalues = {}
    pmdata = {}

    try:
        pmdata = pm25.read()
    except RuntimeError:
        print("Unable to read PM2.5 Data")
        # pm25.reset()

    if(pmdata):
        pmvalues['pm10 standard'] = pmdata.data[0]
        pmvalues['pm25 standard'] = pmdata.data[1]
        pmvalues['pm100 standard'] = pmdata.data[2]
        pmvalues['pm10 env'] = pmdata.data[3]
        pmvalues['pm25 env'] = pmdata.data[4]
        pmvalues['pm100 env'] = pmdata.data[5]
        pmvalues['particles 03um'] = pmdata.data[6]
        pmvalues['particles 05um'] = pmdata.data[7]
        pmvalues['particles 10um'] = pmdata.data[8]
        pmvalues['particles 25um'] = pmdata.data[9]
        pmvalues['particles 50um'] = pmdata.data[10]
        pmvalues['particles 100um'] = pmdata.data[11]


    return pmvalues

def read_temp_hum():
    """
    Read temp and humidity from environment sensor
    """
    values = {}
    try:
        if(C_TO_F):
            values['temperature'] = round(c_to_f(th.temperature), 2)
        else:
            values['temperature'] = round(th.temperature, 2)
        
        values['humidity'] = round(th.relative_humidity, 2)
    except Exception:
        print("No temp or humidity sensor")

    return values

def read_analog():
    """
    Read analog signal from Pin ADC1 (A1)
    """
    return adc.value

### LED METHODS ###
def led_on(led):
    """
    Turn on the LED passed to the function
    """
    led.value = True

def led_off(led):
    """
    Turn off the LED passed to the function
    """
    led.value = False

def blink(led, period, times):
    """
    Blink the LED passed to the function
    """
    for i in range(times):
        led_on(led)
        time.sleep(period)
        led_off(led)
        if(i != times):
            time.sleep(period)

def led_status(values):
    """
    Turn onboard LEDs on/off based on sensor data. This can be used to create a status
    indicator based on sensor reading values.
    """
    if(LED_R_LOW_THRESHOLD < values[LED_R_MEASURE] <= LED_R_HIGH_THRESHOLD):
        board_led_r.value = True
    else:
        board_led_r.value = False

    if(LED_G_LOW_THRESHOLD < values[LED_G_MEASURE] <= LED_G_HIGH_THRESHOLD):
        board_led_g.value = True
    else:
        board_led_g.value = False

### HELPER METHODS ###
def merge_dicts(values, dicts):
    """
    Merge two dictionaries into a single dict
    """
    dicts.update(values)

    return dicts

def average_dict(dicts):
    """
    Record sensor measurements in a dictionary of lists. Used to smooth sensor readings
    so they don't jump around too much
    """
    for d in dicts:
        # Add sensor measurement to avgDict if it doesn't already exists
        # Helpful for not having to declare every possible sensor measure
        if(d not in avgDict):
            avgDict[d]=[]
        avgDict[d].append(dicts[d])
        ln = len(avgDict[d])
        if(ln > SMOOTH):
            newList = avgDict[d]
            # Only keep SMOOTH number of items in the list
            avgDict[d] = newList[ln-SMOOTH:]

    return avgDict
    
def average_values(avgDict):
    """
    Calculates the average measurement based on values stored in the average dict
    """
    values = {}
    for v in avgDict:
        values[v] = round(sum(avgDict[v])/len(avgDict[v]))

    return values

def c_to_f(temp):
    """
    Convert Celsius to Fahrenheit
    """
    return (temp * 9 / 5) + 32


print("Connecting to WiFi")

wifi.radio.connect(os.getenv('WIFI_SSID'), os.getenv('WIFI_PASSWORD'))

# Blink the green LED if Wifi is connected
if(wifi.radio.connected):
    print("Connected to WiFi")
    blink(board_led_g, 0.2, 3)
    

# Create socket pool
pool = socketpool.SocketPool(wifi.radio)

# Create html server
server = Server(pool, '/html', debug=True)

#  prints MAC address to REPL
print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

#  prints IP address to REPL
print("My IP address is", wifi.radio.ipv4_address)

# Setup MQTT Client
mqtt_client = MQTT.MQTT(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    socket_pool=pool,
    is_ssl=MQTT_ISTLS,
    connect_retries = 2
)

### HTML SERVER ROUTES ###
@server.route("/")
def base(request: Request):
    """
    Serve the default index.html file.
    """
    return FileResponse(request, "index.html")

@server.route("/getdata")
def get_sensor_data(request: Request):
    """
    Read sendor data and return JSON
    """
    data = read_all()

    # averrage to smooth out values
    avgDict = average_dict(data)
    data = average_values(avgDict)

    return JSONResponse(request, data)

@server.route("/pmdata")
def pmdata_client(request: Request):
    """
    Serve PMS 5003 data as JSON
    """
    data = read_pms25()
    return JSONResponse(request, data)

@server.route("/aqi")
def pmdata_client(request: Request):
    """
    Serve US AQI info as JSON
    """
    data = USAQI.pm25_aqi(average_values(avgDict)['pm25 env'])
    data = USAQI.aqi_info(data)
    return JSONResponse(request, data)

@server.route("/th")
def pmdata_client(request: Request):
    """
    Serve Temp and Humidity data as JSON
    """
    data = read_temp_hum()
    return JSONResponse(request, data)
    
@server.route("/ledon")
def pico_led_on(request: Request):
    """
    Turn on the Pico W LED
    """
    led.value = True

    return FileResponse(request, "index.html")

@server.route("/ledoff")
def pico_led_on(request: Request):
    """
    Turn off the Pico W LED
    """
    led.value = False

    return FileResponse(request, "index.html")

@server.route("/redledon")
def board_led_on(request: Request):
    """
    Turn on the red LED
    """
    led_on(board_led_r)

    return FileResponse(request, "index.html")

@server.route("/redledoff")
def board_led_on(request: Request):
    """
    Turn off the red LED
    """
    led_off(board_led_r)

    return FileResponse(request, "index.html")

@server.route("/greenledon")
def board_led_on(request: Request):
    """
    Turn on the green LED
    """
    led_on(board_led_g)

    return FileResponse(request, "index.html")

@server.route("/greenledoff")
def board_led_on(request: Request):
    """
    Turn off the green LED
    """
    led_off(board_led_g)

    return FileResponse(request, "index.html")

### MQTT METHODS ###
## Leaving all methods here even though not all are being used
## Some people might find it helpful
def connect(mqtt_client, userdata, flags, rc):
    """
    This method is be called when the mqtt_client is connected successfully to the broker.
    """
    print("Connected to MQTT Broker!")
    print("Flags: {0}\n RC: {1}".format(flags, rc))


def disconnect(mqtt_client, userdata, rc):
    """
    This method is called when the mqtt_client disconnects from the broker.
    """
    print("Disconnected from MQTT Broker!")


def subscribe(mqtt_client, userdata, topic, granted_qos):
    """
    This method is called when the mqtt_client subscribes to a new feed.
    """
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))


def unsubscribe(mqtt_client, userdata, topic, pid):
    """
    This method is called when the mqtt_client unsubscribes from a feed.
    """
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))


def publish(mqtt_client, userdata, topic, pid):
    """
    This method is called when the mqtt_client publishes data to a feed.
    """
    print("Published to {0} with PID {1}".format(topic, pid))


def message(client, topic, message):
    """
    This method is called when a client's subscribed feed has a new value.
    """
    print("New message on topic {0}: {1}".format(topic, message))

def mqtt_try_reconnect():
    try:
        mqtt_client.reconnect()
    except MQTT.MMQTTException as e:
        print(e)

# Connect callback handlers for mqtt_client
mqtt_client.on_connect = connect
mqtt_client.on_disconnect = disconnect
mqtt_client.on_subscribe = subscribe
mqtt_client.on_unsubscribe = unsubscribe
mqtt_client.on_publish = publish
mqtt_client.on_message = message

if MQTT_USERNAME and MQTT_PASSWORD:
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

if MQTT_ENABLED:
    mqtt_client.connect()

# Start the html server.
server.start(str(wifi.radio.ipv4_address))

# Get clock reference
clock = time.monotonic()
values = {}

while True:
    
    # Take the measurements after every interval
    if (clock + INTERVAL) < time.monotonic():

        mqtt_msg = {}

        mqtt_msg = read_all()
        
        # averrage to smooth out values
        avgDict = average_dict(mqtt_msg)

        mqtt_msg = average_values(avgDict)

        led_status(mqtt_msg)

        if not mqtt_client.is_connected():
            mqtt_try_reconnect()
            continue

        else:     
            if (mqtt_msg and MQTT_ENABLED and wifi.radio.connected):
                try:
                    mqtt_client.publish(MQTT_TOPIC, json.dumps(mqtt_msg))
                except MQTT.MMQTTException as e:
                    print(e)
                except:
                    print("WiFi disconnected and MQTT socket is broken...")
                    print("Trying to reconnect")
                    mqtt_try_reconnect()
            else:
                print("No successful readings or wifi is disconnected")

        clock = time.monotonic()
    
    # Process html requests between reading sensor data
    pool_result = server.poll()