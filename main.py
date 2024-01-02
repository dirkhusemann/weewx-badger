# Badger2040W project: fetch weewx JSON data from weewx server and display it on the eInk display

import badger2040
badger = badger2040.Badger2040()

import urequests
import json
import gc
import ntptime
import machine


WEEWX_URI = 'http://dobby.fritz.box/weewx/json/weewx.json'
SLEEP_TIME = 5 # min
FONT = "sans"
FONT_SCALE = 0.5
LINE_HEIGHT = 15


class SimpleClass:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if type(v) is dict:
                setattr(self, k, SimpleClass(**v))
            else:
                setattr(self, k, v)



def weewx(badger, uri):
    badger.led(128)
    r = None
    try:
        r = urequests.get(uri)
        badger.led(0)

        if r.status_code != 200:
            return None
        j = json.loads(r.content)
        return SimpleClass(**j)
    except:
        pass
    finally:
        if r:
            r.close()
        badger.led(0)


def display_data(badger, data):
    
    def eprinter(yoffset=10, xoffset=0, line_height=LINE_HEIGHT):
        current_y = yoffset
        
        def eprint(text="", yoffset=0):
            nonlocal current_y
            
            badger.text(text, xoffset, current_y + yoffset, scale=FONT_SCALE)
            current_y += line_height + yoffset

        return eprint
                
    badger.set_pen(15)
    badger.clear()

    badger.set_pen(0)
    badger.set_font(FONT)
    badger.set_thickness(2)
    
    display_width, display_height = badger.get_bounds()
    
    eprint = eprinter()
        
    eprint(f"{data.station.location} Weather Report")
    badger.line(0, LINE_HEIGHT+2, display_width, LINE_HEIGHT+2, 2)
    
    eprint(f"Temp outdoors {data.current.temperature_outdoors.value:.1f}C wind chill {data.current.wind_chill.value:.1f}C", yoffset=3)
    eprint(f"RelH outdoors {data.current.humidity_outdoors.value:.1f}% indoors {data.current.humidity_indoors.value:.1f}%")
    eprint(f"Wind {data.current.wind_speed.value}Bf from {data.current.wind_direction.value}, gusts {data.current.wind_gust.value}Bf")
    eprint(f"Rain {data.current.rain_rate.value:.1f} mm/h, total {data.day.rain_total.value:.1f} mm")
    eprint(f"Barometer {data.current.barometer.value:.2f} mbar")
    eprint(f"  pressure {data.current.barometer_trend.value:+.2f} mbar/6h")
    
    badger.text(f"W {data.generation.time} | L {datetime.datetime.now().strftime('%a %Y-%M-%d %H:%M:%S %Z')}",
                yoffset=5, scale=0.3)

    badger.update()


def setup():
    # connect to the WiFi (and don't muck around with the display)
    badger.connect(status_handler=None)

    if badger.isconnected() and not badger2040.woken_by_rtc():
        # obtain NTP time
        ntptime.host = '192.168.8.1'
        ntptime.settime()

    # GC configuration
    gc.threshold(0)


# NOTE: The following while loop works in two different ways,
# depending on the power source:
# - when powered by USB the loop will behave as you expect it to
# - when powered by battery the badger2040.sleep_for() invocation will
#   basically power down the board and terminate us, on power up we
#   will restart.
setup()

# Watchdog
#wdt = machine.WDT(timeout=5000)

while True:
    try:
        data = weewx(badger, WEEWX_URI)
        #wdt.feed()
        if data:
            display_data(badger, data)
        #wdt.feed()
        data = None
        
        gc.collect()
        badger2040.sleep_for(5)

    except Exception as ex:
        print(ex)


