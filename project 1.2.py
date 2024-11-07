import time
from machine import Pin, I2C
import ssd1306

i2c = I2C(1, scl=Pin(15), sda=Pin(14))
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

line_height = 8
current_y = 0

def display_text(text):
    global current_y
    
    # If current_y exceeds the height of the OLED, scroll the screen
    if current_y >= oled_height - line_height:
        oled.scroll(0, -line_height)
        current_y -= line_height
    
    # Clear the current line and display the text
    oled.fill_rect(0, current_y, oled_width, line_height, 0)
    oled.text(text, 0, current_y)
    oled.show()
    
    # Update the current_y position for the next text
    current_y += line_height

print("Type text and press enter to display it on the OLED. Type 'exit' to quit.")

while True:
    text = input('Enter text: ')
    if text.lower() == 'exit':
        break
    display_text(text)


