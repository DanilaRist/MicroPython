import time
from machine import UART, Pin, I2C, Timer, ADC
import ssd1306

# Buttons
left_button = Pin(7, Pin.IN, Pin.PULL_UP)  
right_button = Pin(9, Pin.IN, Pin.PULL_UP) 

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# Screen boundaries
x_min = 0
x_max = oled_width - 1
y_min = 0
y_max = oled_height - 1

# UFO properties
ufo = "<=>"
ufo_width = len(ufo) * 8  

# Initial UFO position
x = (x_max + 1 - ufo_width) // 2
y = y_max - 8  # Place UFO at the bottom

# Function to draw the UFO
def draw_ufo(x, y):
    oled.fill(0)
    oled.text(ufo, x, y)
    oled.show()

# Draw the initial UFO
draw_ufo(x, y)

while True:
    # Move left
    if left_button.value() == 0 and x > x_min:
        x -= 1
        draw_ufo(x, y)
        time.sleep(0.1)  # Debounce delay

    # Move right
    if right_button.value() == 0 and x < (x_max - ufo_width + 1):
        x += 1
        draw_ufo(x, y)
        time.sleep(0.001)  # Debounce delay
