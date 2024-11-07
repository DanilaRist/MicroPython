from machine import Pin
from fifo import Fifo

class Encoder:
    def __init__(self, rot_a, rot_b):
        # Initialize pins for rotary encoder
        self.a = Pin(rot_a, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(rot_b, mode=Pin.IN, pull=Pin.PULL_UP)
        
        # Initialize FIFO buffer
        self.fifo = Fifo(30, typecode='i')
        
        # Attach interrupt handler to pin a
        self.a.irq(handler=self.handler, trigger=Pin.IRQ_RISING, hard=True)
        
    def handler(self, pin):
        # Interrupt handler function
        if self.b():  # Check the state of pin b
            self.fifo.put(-1)  # If pin b is high, put -1 in the FIFO
        else:
            self.fifo.put(1)   # If pin b is low, put 1 in the FIFO

# Create an instance of Encoder with pins 10 and 11
rot = Encoder(10, 11)

# Main loop to continuously check for data in the FIFO
while True:
    if rot.fifo.has_data():
        print(rot.fifo.get())
