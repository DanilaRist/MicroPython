import time
from machine import UART, Pin, I2C, Timer, ADC
import ssd1306 
from fifo import Fifo
from led import Led
from piotimer import Piotimer
import micropython
import utime
import network
from time import sleep
import mip
from umqtt.simple import MQTTClient
import ujson
import urequests as requests

button = Pin(12, pull=Pin.PULL_UP, mode=Pin.IN)
led21_pin = 21 
led21 = Led(led21_pin, brightness=10)
pin_nr = 26
sample_rate = 250
threshold_percentage = 0.15
prev_sample = 0
peak_found = False 
current_peak_index = 0
previous_peak_index = 0
index = 0
ms_in_minute = 60000
min_hr = 30
max_hr = 240
first_peak_found = False
samplerate = 250
samples = Fifo(1000)
buffer = [0] * 32  # Initialize buffer variable
avg_size = 32  # Define avg_size


def meanPPI_calculator(data):
    sumPPI = 0 
    for i in data:
        sumPPI += i
    rounded_PPI = round(sumPPI / len(data), 0)
    return int(rounded_PPI)

# Mean HR Calculator
def meanHR_calculator(meanPPI):
    rounded_HR = round(60 * 1000 / meanPPI, 0)
    return int(rounded_HR)

def rmssd_calculator(hr_list, ppi_list):
    # Calculate the differences between successive PPI values
    differences = [ppi_list[i + 1] - ppi_list[i] for i in range(len(ppi_list) - 1)]
    squared_diff = [diff ** 2 for diff in differences]
    mean_squared_diff = sum(squared_diff) / len(squared_diff)
    rmssd = mean_squared_diff ** 0.5

    return int(rmssd)

def sdnn_calculator(hr_list, ppi_list):
    ppi_diff_list = []
    drop_th = 0.15
        
    ppi_mean = sum(ppi_list)/len(ppi_list)
    
    for ppi in ppi_list:
        if ppi >= ppi_mean - drop_th * ppi_mean and ppi <= ppi_mean + drop_th * ppi_mean:
            ppi_diff_list.append((ppi-ppi_mean)**2)
    
    mean_squared_ppi = sum(ppi_diff_list)/len(ppi_diff_list)
    sdnn = mean_squared_ppi**0.5
    
    return sdnn

def sdnn_calculator2(hr_list, ppi_list):
    mean_hr = sum(hr_list) / len(hr_list)
    sum_squared_diff_ppi = sum((x - mean_hr) ** 2 for x in ppi_list)
    variance_ppi = sum_squared_diff_ppi / len(ppi_list)
    sdnn = variance_ppi ** 0.5
    
    return sdnn


ssid = 'KME661_Group4'
password = 'Danmaftq'
BROKER_IP = '192.168.1.254'

def connect_wlan():
    # Connecting to the group WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    # Attempt to connect once per second
    while wlan.isconnected() == False:
        print("Connecting... ")
        sleep(1)

    # Print the IP address of the Pico
    print("Connection successful. Pico IP:", wlan.ifconfig()[0])
        
def connect_mqtt():
    mqtt_client=MQTTClient("", BROKER_IP)
    mqtt_client.connect(clean_session=True)
    return mqtt_client

def send_mqtt_message(mean_hr, mean_ppi, rmssd, sdnn, mqtt_client=None):
    # If MQTT client is not provided, establish WLAN and MQTT connections
    if mqtt_client is None:
        try:
            connect_wlan()
            mqtt_client = connect_mqtt()
            print("Connected to MQTT")
        except Exception as e:
            print(f"Failed to connect to WLAN or MQTT: {e}")
            return

    # Send MQTT message
    try:
        topic = "pico/test"
        measurement = {
            "mean_hr": mean_hr,
            "mean_ppi": mean_ppi,
            "rmssd": rmssd,
            "sdnn": sdnn
        }
        json_message = ujson.dumps(measurement)
        mqtt_client.publish(topic, json_message)
        print(f"Sending to MQTT: {topic} -> {json_message}")
    except Exception as e:
        print(f"Failed to send MQTT message: {e}")

         
class Encoder:
    def __init__(self, rot_a, rot_b):
        self.a = Pin(rot_a, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(rot_b, mode=Pin.IN, pull=Pin.PULL_UP)
        self.fifo = Fifo(500, typecode='i')
        self.a.irq(handler=self.handler, trigger=Pin.IRQ_RISING, hard=True)
    
    def handler(self, pin):
        if self.b.value():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)

def display_menu(oled, menu_items, selected_item):
    oled.fill(0)
    for i, item in enumerate(menu_items):
        if i == selected_item:
            oled.text(f'[{item}]', 0, i * 10)
        else:
            oled.text(item, 0, i * 10)
    oled.show()

def on_press(pin):
    global last_press_time, selected_item, current_screen
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_press_time) > 50:
        last_press_time = current_time
        selected_item = (selected_item + 1) % len(menu_items)
        display_menu(oled, menu_items, selected_item)
        current_screen = None  # Reset current screen when navigating through menu items

def button_pressed(pin):
    global current_screen, selected_item
    if current_screen in ["HR_Measurement", "HRV_screen", "Kubios_screen"]:
        selected_item = 0  # Go back to the first item in the menu
        oled.fill(0) 
        display_menu(oled, menu_items, selected_item)
        current_screen = None  # Reset current screen to allow navigation through menu items
    else:
        # If not in the specific screens, proceed with the default button behavior
        if selected_item == 0:
            HR_Measurement()  # Display HR Measurement screen
            current_screen = "HR_Measurement"
        elif selected_item == 1:
            HR_Measurement()  # Display HR Measurement screen
            current_screen = "HR_Measurement"
            #utime.sleep(30)  # Wait for 30 seconds for HR Measurement to complete
            selected_item = 1  # Switch to HRV Analysis automatically
            oled.fill(0) 
            display_menu(oled, menu_items, selected_item)
            current_screen = "HRV_screen"
            utime.sleep(0.1)  # Give some time for the screen to update
            HRV_screen()  # Call HRV screen function
            selected_item = 0  # Go back to the first item in the menu
        elif selected_item == 2:
            HR_Measurement()  # Display HR Measurement screen
            current_screen = "HR_Measurement"
            selected_item = 2  # Switch to Kubios screen automatically
            oled.fill(0) 
            display_menu(oled, menu_items, selected_item)
            current_screen = "Kubios_screen"
            utime.sleep(0.1)  # Give some time for the screen to update
            kubios_screen()  # Call Kubios screen function
            selected_item = 0  # Go back to the first item in the menu

            
def read_adc(tid):
    x = adc.read_u16()
    samples.put(x)

def HR_Measurement():
    oled.fill(0)
    oled.show()

    x1 = -1
    y1 = 32
    m0 = 65535 / 2
    a = 1 / 10

    disp_div = samplerate / 25
    disp_count = 0
    capture_length = 0

    capture_length = samplerate * 30  # Capture data for 30 seconds

    index = 0
    capture_count = 0
    subtract_old_sample = 0
    sample_sum = 0

    min_bpm = 30
    max_bpm = 240
    sample_peak = 0
    sample_index = 0
    previous_peak = 0
    previous_index = 0
    PPI_array = []
    brightness = 0
    interval_ms = 0

    tmr = Piotimer(freq=samplerate, callback=read_adc)

    while capture_count < capture_length:
        if button.value() == 0:  # Check if the button is pressed
            mode = 0
            break

        if not samples.empty():
            x = samples.get()
            disp_count += 1

            if disp_count >= disp_div:
                disp_count = 0
                m0 = (1 - a) * m0 + a * x
                y2 = int(32 * (m0 - x) / 14000 + 35)
                y2 = max(10, min(53, y2))
                x2 = x1 + 1
                oled.fill_rect(0, 0, 128, 9, 1)
                oled.fill_rect(0, 55, 128, 64, 1)
                if len(PPI_array) > 3:
                    actual_PPI = meanPPI_calculator(PPI_array)
                    actual_HR = meanHR_calculator(actual_PPI)
                    text_width = len(f'HR: {actual_HR}') * 8
                    x_pos = (128 - text_width) // 2
                    oled.text(f'HR: {actual_HR}', x_pos, 1, 0)
                text_width = len(f'Time:  {int(capture_count/samplerate)}s') * 8
                x_pos = (128 - text_width) // 2
                oled.text(f'Time:  {int(capture_count/samplerate)}s', x_pos, 56, 0)
                oled.line(x2, 10, x2, 53, 0)
                oled.line(x1, y1, x2, y2, 1)
                oled.show()
                x1 = x2
                if x1 > 127:
                    x1 = -1
                y1 = y2

            if subtract_old_sample:
                old_sample = buffer[index]
            else:
                old_sample = 0
            sample_sum = sample_sum + x - old_sample

            if subtract_old_sample:
                sample_avg = sample_sum / avg_size
                sample_val = x
                if sample_val > sample_avg * 1.05:
                    if sample_val > sample_peak:
                        sample_peak = sample_val
                        sample_index = capture_count
                else:
                    if sample_peak > 0:
                        if (sample_index - previous_index) > (60 * samplerate / min_bpm):
                            previous_peak = 0
                            previous_index = sample_index
                        else:
                            if sample_peak >= (0.8 * previous_peak):
                                if (sample_index - previous_index) > (60 * samplerate / max_bpm):
                                    if previous_peak > 0:
                                        interval = sample_index - previous_index
                                        interval_ms = int(interval * 1000 / samplerate)
                                        PPI_array.append(interval_ms)
                                        brightness = 5
                                        led21(4000)
                                    previous_peak = sample_peak
                                    previous_index = sample_index
                    sample_peak = 0

                if brightness > 0:
                    brightness -= 1
                else:
                    led21(0)

            buffer[index] = x
            capture_count += 1
            index += 1
            if index >= avg_size:
                index = 0
                subtract_old_sample = 1

    tmr.deinit()

    while not samples.empty():
        x = samples.get()

def HRV_screen():
    
    mean_PPI = meanPPI_calculator(PPI_array)
    mean_HR = meanHR_calculator(mean_PPI)
    SDNN = sdnn_calculator(PPI_array)
    RMSSD = rmssd_calculator(PPI_array)

    oled.fill(0)
    oled.text('MeanPPI:'+ str(int(mean_PPI)) +'ms', 0, 0, 1)
    oled.text('MeanHR:'+ str(int(mean_HR)) +'bpm', 0, 9, 1)
    oled.text('SDNN:'+str(int(SDNN)) +'ms', 0, 18, 1)
    oled.text('RMSSD:'+str(int(RMSSD)) +'ms', 0, 27, 1)
    oled.show()

    # Send data via MQTT
    connect_wlan()
    connect_mqtt()
    send_mqtt_message(mean_HR, mean_PPI, RMSSD, SDNN)

def kubios_screen():
   
    # Connect to WLAN
    connect_wlan()

    # Convert interval data into Kubios Cloud dataset dictionary format
    dataset = {
        "type": "RRI",
        "data": ppi_list,
        "analysis": {"type": "readiness"}
    }
    APIKEY = "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a"
    CLIENT_ID = "3pjgjdmamlj759te85icf0lucv"
    CLIENT_SECRET = "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef"
    TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
    response = requests.post(
        url=TOKEN_URL,
        data='grant_type=client_credentials&client_id={}'.format(CLIENT_ID),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        auth=(CLIENT_ID, CLIENT_SECRET)
    )
    response = response.json()
    access_token = response["access_token"]
    response = requests.post(
        url="https://analysis.kubioscloud.com/v2/analytics/analyze",
        headers={
            "Authorization": "Bearer {}".format(access_token),
            "X-Api-Key": APIKEY
        },
        json=dataset
    )
    response = response.json()
    sns_index_value = round(response['analysis']['sns_index'])
    pns_index_value = round(response['analysis']['pns_index'])
    mean_hr_value = round(response['analysis']['mean_hr_bpm'])
    mean_rr_value = round(response['analysis']['mean_rr_ms'])
    rmssd_value = round(response['analysis']['rmssd_ms'])
    sdnn_value = round(response['analysis']['sdnn_ms'])

    print("SNS     :", sns_index_value)
    print("PNS     :", pns_index_value)
    print("Mean HR :", mean_hr_value)
    print("Mean PPI:", mean_rr_value)
    print("RMSSD   :", rmssd_value)
    print("SDNN    :", sdnn_value)

    oled.fill(0)
    oled.text(str(mean_hr_value), 80, 0, 1)
    oled.text(str(mean_rr_value), 80, 10, 1)
    oled.text(str(rmssd_value), 80, 20, 1)
    oled.text(str(sdnn_value), 80, 30, 1)
    oled.text(str(sns_index_value), 80, 40, 1)
    oled.text(str(pns_index_value), 80, 50, 1)
    oled.show()

# Initialize rotary encoder
rot = Encoder(10, 11)

# Initialize button
button = Pin(12, Pin.IN, Pin.PULL_UP)
button.irq(handler=on_press, trigger=Pin.IRQ_RISING, hard=True)

# Define menu items
menu_items = ['1. Measure HR', '2. HRV Analysis', '3. Kubios']

# Initialize I2C for OLED display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# Display initial menu
selected_item = 0
current_screen = None
display_menu(oled, menu_items, selected_item)

last_press_time = time.ticks_ms()  # Initialize last press time

button.irq(handler=button_pressed, trigger=Pin.IRQ_FALLING)
adc = ADC(Pin(pin_nr))

tmr = Piotimer(mode = Piotimer.PERIODIC, freq = sample_rate) # gets samples 

while True:
    if rot.fifo.has_data():
        event = rot.fifo.get()
        if event != 0:  # Rotary encoder event
            selected_item = (selected_item + event) % len(menu_items)
            display_menu(oled, menu_items, selected_item)
            current_screen = None  # Reset current screen when navigating through menu items
    #if current_screen == "HR Measurement":
        #HR_Measurement()
   # elif current_screen == "HRV_screen":
       # HRV_screen()
  #  elif current_screen == "kubios_screen":
     #   kubios_screen()
        
        