from machine import Pin
from led import Led 
from fifo import Fifo  

Led1 = Led(20)

class Encoder:
    def __init__(self, rot_a_pin, rot_b_pin, button_pin):
        self.a = Pin(rot_a_pin, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(rot_b_pin, mode=Pin.IN, pull=Pin.PULL_UP)
        self.button = Pin(button_pin, mode=Pin.IN, pull=Pin.PULL_UP)
        self.fifo = Fifo(30, typecode='i')
        self.a.irq(handler=self.handler, trigger=Pin.IRQ_RISING, hard=True)

    def handler(self, pin):
        if self.b.value():
            self.fifo.put(-1)  # Clockwise rotation
        else:
            self.fifo.put(1)   # Counter-clockwise rotation

    def is_button_pressed(self):
        return not self.button.value()  # Check if button is pressed (active low)

# Initialize rotary encoder on GPIO pins 10 (rot_a), 11 (rot_b), and 12 (button)
rot = Encoder(10, 11, 12)

# Initial LED state: Turn LED off
Led1.off()

# Initial LED brightness
br = 0
Led1.brightness(br)

led_state = False  # Track LED state (off by default)

while True:
#    try:
        # Check if encoder button is pressed
        if rot.is_button_pressed():
            led_state = not led_state
            if led_state:
                Led1.on()  # Turn LED on
            else:
                Led1.off()  # Turn LED off

            # Wait for button release (debounce)
            while rot.is_button_pressed():
                pass

        # Check if FIFO is not empty (encoder rotation detected)
        if not rot.fifo.empty():
            turn = rot.fifo.get()  # Retrieve encoder turn
            if led_state:
                # Adjust brightness within range [0, 1023]
                br = max(0, min(1023, br + turn))
                Led1.brightness(br)  # Update LED brightness if LED is on
            else:
                br = 0  # Set brightness to 0 if LED is off

    #except RuntimeError as e:
        #print("Error:", e)  # Print error message
        #pass  # Continue execution if FIFO is empty
    #except AttributeError:
        #pass  # Handle AttributeError (Fifo has no 'empty' method), continue loop
