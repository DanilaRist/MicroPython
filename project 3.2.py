import time
from machine import Pin, I2C
import ssd1306
from led import Led
from fifo import Fifo

class Encoder:
def __init__(self, 10, 11):
        self.a = Pin(rot_a, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(rot_b, mode=Pin.IN, pull=Pin.PULL_UP)
        self.fifo = Fifo(30, typecode='i')
        self.a.irq(handler=self.handler, trigger=Pin.IRQ_RISING, hard=True)
    
    def handler(self, pin):
        if self.b.value():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)

def on_press(pin):
    global last_press_time
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_press_time) > 50:
        last_press_time = current_time
        rot.fifo.put(0)  # Add an event for button press

rot = Encoder(10, 11)

button = Pin(12, Pin.IN, Pin.PULL_UP)
button.irq(handler=on_press, trigger=Pin.IRQ_RISING, hard=True)

menu_items = ['1.Measure HR', '2.HRV Analysis']

def display_menu(oled, menu_items, selected_led):
    oled.fill(0)
    for i, item in enumerate(menu_items):
        if i == selected_led:
            oled.text(f'[{item} - {"ON" if led_states[i] else "OFF"}]', 0, i * 10)
        else:
            oled.text(f'{item} - {"ON" if led_states[i] else "OFF"}', 0, i * 10)
    oled.show()

# Initialize I2C for OLED display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# Display initial menu
selected_led = 0
display_menu(oled, menu_items, selected_led)

last_press_time = time.ticks_ms()  # Initialize last press time

while True:
    if rot.fifo.has_data():
        event = rot.fifo.get()
        if event == 0:  # Button press event
            led_states[selected_led] = not led_states[selected_led]  # Toggle LED state
            if all(led_states):  # Check if all LEDs are on
                for led in leds:
                    led.on()
            else:
                
            display_menu(oled, menu_items, selected_led)
        else:  # Rotary encoder event
            selected_led = (selected_led + event) % len(menu_items)
            display_menu(oled, menu_items, selected_led)
