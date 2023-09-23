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
from adafruit_pm25.uart import PM25_UART
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
reset_pin = DigitalInOut(board.GP8)
reset_pin.direction = Direction.OUTPUT
reset_pin.value = False

uart = busio.UART(board.GP16, board.GP17, baudrate=9600)
pm25 = PM25_UART(uart, reset_pin)

## Add Qwiic/QT/I2C Sensors
## SCL on GP21; SDA on GP20
i2c = busio.I2C(board.GP21, board.GP20)
th = adafruit_ahtx0.AHTx0(i2c)

avgDict = {}

### SENSOR METHODS ###
def read_all():
    """
    Read all sensor data and return a single dictionary
    """
    data = {}
    data = merge_dicts(read_pms25(), data)
    data = merge_dicts(read_temp_hum(), data)

    return data

def read_pms25():
    """
    Read air quality information from PMS5003
    """
    pmdata = {}

    try:
        pmdata = pm25.read()
    except RuntimeError:
        print("Unable to read PM2.5 Data")

    return pmdata

def read_temp_hum():
    """
    Read temp and humidity from environment sensor
    """
    values = {}

    if(C_TO_F):
        values['temperature'] = round(c_to_f(th.temperature), 2)
    else:
        values['temperature'] = round(th.temperature, 2)
    
    values['humidity'] = round(th.relative_humidity, 2)

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
    for d in dicts:
        if(d not in avgDict):
            avgDict[d]=[]
        avgDict[d].append(dicts[d])
        ln = len(avgDict[d])
        if(ln > SMOOTH):
            newList = avgDict[d]
            avgDict[d] = newList[ln-SMOOTH:]

    return avgDict
    
def average_values(avgDict):
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

    return JSONResponse(request, data)

@server.route("/pmdata")
def pmdata_client(request: Request):
    """
    Serve PMS 5003 data as JSON
    """
    data = read_pms25()
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
    

# Setup MQTT Client
mqtt_client = MQTT.MQTT(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    socket_pool=pool,
    is_ssl=MQTT_ISTLS
)

# Connect callback handlers for mqtt_client
mqtt_client.on_connect = connect
mqtt_client.on_disconnect = disconnect
mqtt_client.on_subscribe = subscribe
mqtt_client.on_unsubscribe = unsubscribe
mqtt_client.on_publish = publish
mqtt_client.on_message = message

if MQTT_USERNAME and MQTT_PASSWORD:
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

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

        if mqtt_msg:
            mqtt_client.publish(MQTT_TOPIC, json.dumps(mqtt_msg))
        else:
            print("No successful readings")

        clock = time.monotonic()
    
    # Process html requests between reading sensor data
    pool_result = server.poll()