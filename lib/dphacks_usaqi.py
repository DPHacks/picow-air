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

# US AQI calculation based on the US EPA AQI: https://www.epa.gov/outdoor-air-quality-data/how-aqi-calculated
# This was tested against the AirNow.gov calculator: https://www.airnow.gov/aqi/aqi-calculator-concentration/


import math

## Breakpoints
# PM2.5 (ug/m3)
PM25 = [ [0, 12.0], [12.1, 35.4], [35.5, 55.4], [55.5, 150.4], [150.5, 250.4], [250.5, 350.4], [350.5, 500.4] ]
# PM10 (ug/m3)
PM100 = [ [0, 54], [55, 154], [155, 254], [255, 354], [355, 424], [425, 504], [505, 604] ]
# AQI
AQI = [ [0, 50], [51, 100], [101, 150], [151, 200], [201, 300], [301, 400], [401, 500] ]

AQI_INFO = [{'category': 'Good', 'color':'Green', 'rgb':[0, 228, 0]},
            {'category': 'Moderate', 'color':'Yellow', 'rgb':[255, 255, 0]},
            {'category': 'Unhealthy for Sensitive Groups', 'color':'Orange', 'rgb':[255, 126, 0]},
            {'category': 'Unhealthy', 'color':'Red', 'rgb':[255, 0, 0]},
            {'category': 'Very Unhealthy', 'color':'Purple', 'rgb':[143, 63, 151]},
            {'category': 'Hazardous', 'color':'Maroon', 'rgb':[126, 0, 35]}]

def truncate(number, digits) -> float:
    """
    Truncate a floating point number to the correct number of decimal places.
    PM 2.5 concentration needs to be truncated to 1 decimal place
    """ 
    if '.' not in str(number):
        return number
    nbDecimals = len(str(number).split('.')[1]) 
    if nbDecimals <= digits:
        return number
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

def pm25_aqi(pm25_val):
    """
    Returns the AQI based on the PM2.5 concentration
    """
    for i, values in enumerate(PM25):
        val = truncate(pm25_val, 1)
        if values[0] <= val <= values[1]:
            break
    
    aqi_range = AQI[i]

    ihigh = aqi_range[1]
    ilow = aqi_range[0]

    bphigh = values[1]
    bplow = values[0]

    # AQI formula
    aqi_index = (((ihigh - ilow) / (bphigh - bplow))*(val - bplow)) + ilow

    return int(round(aqi_index))

def pm100_aqi(pm100_val):
    """
    Returns the AQI based on the PM10 concentration
    """
    for i, values in enumerate(PM100):
        # PM10 AQI uses concentration truncated to full integer
        if values[0] <= int(pm100_val) <= values[1]:
            break
    
    aqi_range = AQI[i]

    ihigh = aqi_range[1]
    ilow = aqi_range[0]

    bphigh = values[1]
    bplow = values[0]

    # AQI formula
    aqi_index = (((ihigh - ilow) / (bphigh - bplow))*(int(pm100_val) - bplow)) + ilow

    return int(round(aqi_index))

def aqi_info(aqi):
    """
    Returns the AQI Category, Color, and RGB values based on the AQI
    """
    for i, values in enumerate(AQI):
        if values[0] <= aqi <= values[1]:
            break

    data = {'aqi': aqi}
    data.update(AQI_INFO[i]) 

    return data