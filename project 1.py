import time
from machine import Pin, I2C
import ssd1306

SW_0 = Pin(7, Pin.IN, Pin.PULL_UP) 
SW_2 = Pin(9, Pin.IN, Pin.PULL_UP) 
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

ufo_x = (128 - 3) // 2  # Center the UFO horizontally
ufo_y = 64 - 8  # Place UFO at the bottom of the screen

def draw_ufo():
    oled.fill(0)  # Clear the display
    oled.text("<=>", ufo_x, ufo_y)  # Draw the UFO
    oled.show()  # Update the display

# Function to debounce button presses
def button_pressed(pin):
    time.sleep_ms(20)  # Debounce time
    return not pin.value()

while True:
    # Check button inputs and adjust UFO position accordingly
    if button_pressed(SW_0) and ufo_x < 128 - 3:  # Move UFO right if SW0 is pressed and UFO is not at right edge
        ufo_x += 1
    elif button_pressed(SW_2) and ufo_x > 0:  # Move UFO left if SW2 is pressed and UFO is not at left edge
        ufo_x -= 1

    # Draw the UFO at the current position
    draw_ufo()

    time.sleep(0.1)  # Optional delay for stability
