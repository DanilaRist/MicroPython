from machine import Pin, I2C
import ssd1306
import time

# Initialize I2C communication and OLED display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Define button pins
button_SW0 = Pin(7, Pin.IN, Pin.PULL_UP)
button_SW1 = Pin(8, Pin.IN, Pin.PULL_UP)
button_SW2 = Pin(9, Pin.IN, Pin.PULL_UP)

# Define screen dimensions
screen_width = 128
screen_height = 64

# Initialize current pixel position
current_x = 0
current_y = screen_height // 2

# Function to draw a pixel at the specified coordinates
def draw_pixel(x, y):
    # Check if the pixel coordinates are within the screen boundaries
    if x >= 0 and x < screen_width and y >= 0 and y < screen_height:
        # Draw the pixel on the OLED display
        oled.pixel(x, y, 1)
        # Update the OLED display to show the drawn pixel
        oled.show()

# Function to clear the OLED screen
def clear_screen():
    # Fill the OLED display buffer with zeros to clear the screen
    oled.fill(0)
    # Update the OLED display to clear the screen
    oled.show()

# Initial screen setup: clear the screen
clear_screen()

# Main loop
while True:
    # Draw the pixel at the current position
    draw_pixel(current_x, current_y)
    # Move the pixel to the right
    current_x += 1
    # If the pixel reaches the right edge of the screen, reset its position to the left edge
    if current_x >= screen_width:
        current_x = 0

    # Check button SW0 for upward movement
    if button_SW0.value() == 0:
        # Move the pixel up
        current_y -= 1
        # If the pixel goes above the top edge of the screen, keep it at the top edge
        if current_y < 0:
            current_y = 0

    # Check button SW2 for downward movement
    elif button_SW2.value() == 0:
        # Move the pixel down
        current_y += 1
        # If the pixel goes below the bottom edge of the screen, keep it at the bottom edge
        if current_y >= screen_height:
            current_y = screen_height - 1

    # Check button SW1 for screen clearing
    elif button_SW1.value() == 0:
        # Clear the screen and reset the pixel position to the center
        clear_screen()
        current_x = 0
        current_y = screen_height // 2
