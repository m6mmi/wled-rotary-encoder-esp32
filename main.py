import socket
import ujson
import time
from machine import Pin, deepsleep, RTC, reset_cause, DEEPSLEEP_RESET, reset, freq
from rotary_irq_esp import RotaryIRQ
import network
import esp32

# Load WLED config from file if available
try:
    with open('wled_config.json', 'r') as f:
        print('Reading conf fail ... ')
        WLED_CONFIG = ujson.load(f)
except Exception as e:
    print("Using default WLED config:", e)
    WLED_CONFIG = {
        "ip": "",
        "port": 21324,
        "ssid": "",
        "pw": ""
    }

# Encoder and button pins
PIN_CLK = 34
PIN_DT = 35
PIN_BTN = 33

# Global state
rtc = RTC()
brightness = 128
wled_on = True

# Load saved state from RTC memory
if reset_cause() == DEEPSLEEP_RESET:
    try:
        data = ujson.loads(rtc.memory())
        brightness = data['brightness']
        wled_on = data['wled_on']
    except:
        pass

# UDP socket
sock = None

def connect_wifi():
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(WLED_CONFIG['ssid'], WLED_CONFIG['pw'])
        
        for _ in range(10):
            if wlan.isconnected():
                print("Connected, IP:", wlan.ifconfig()[0])
                return
            time.sleep(1)
            
        deepsleep()
        
    except Exception as e:
        print("Coult not connect to wifi.'")
        enter_ap_mode()
    

def send_udp(data):
    global sock
    try:
        msg = ujson.dumps(data).encode('utf-8')
        sock.sendto(msg, (WLED_CONFIG["ip"], WLED_CONFIG["port"]))
    except Exception as e:
        print("Send error:", e)


def set_brightness(bri):
    global brightness
    brightness = max(0, min(255, bri))
    send_udp({"bri": brightness})


def toggle_wled():
    global wled_on
    wled_on = not wled_on
    send_udp({"on": wled_on})


def save_state():
    data = ujson.dumps({'brightness': brightness, 'wled_on': wled_on})
    rtc.memory(data)


def setup_wakeup():
    btn_pin = Pin(PIN_BTN, Pin.IN, Pin.PULL_UP)
    esp32.wake_on_ext0(btn_pin, 0)


def enter_ap_mode():
    # Disconnect from current WiFi
    wlan_sta = network.WLAN(network.STA_IF)
    wlan_sta.active(False)
    
    # Configure AP
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='WLED-Config', password='wled-config', authmode=network.AUTH_WPA_WPA2_PSK)
    ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '8.8.8.8'))
    
    print("AP mode active. IP:", ap.ifconfig()[0])
    start_webserver()

def start_webserver():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 80))
    s.listen(5)
    
    while True:
        conn, addr = s.accept()
        print('Client connected from', addr)
        request = conn.recv(1024).decode()
        
        if 'POST /configure' in request:
            # Extract form data
            data = request.split('\r\n\r\n')[1]
            params = {}
            for pair in data.split('&'):
                key, value = pair.split('=')
                params[key] = value
            
            # Update configuration
            WLED_CONFIG['ip'] = params.get('ip', WLED_CONFIG['ip'])
            WLED_CONFIG['port'] = int(params.get('port', WLED_CONFIG['port']))
            WLED_CONFIG['ssid'] = params.get('ssid', WLED_CONFIG['ssid'])
            WLED_CONFIG['pw'] = params.get('pw', WLED_CONFIG['pw'])
            
            # Save to file
            with open('wled_config.json', 'w') as f:
                ujson.dump(WLED_CONFIG, f)
            
            # Send response
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            conn.send('<html><body>Configuration saved. Rebooting...</body></html>')
            conn.close()
            
            # Reboot
            time.sleep(1)
            reset()
        else:
            # Send configuration form
            html = """<!DOCTYPE html>
                <html lang="et">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Seadista WLED ühendus</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            background-color: #f0f0f5;
                            padding: 20px;
                            margin: 0;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                        }}
                        .container {{
                            background-color: #fff;
                            padding: 20px;
                            border-radius: 12px;
                            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                            width: 100%%;
                            max-width: 400px;
                        }}
                        input {{
                            width: calc(100%% - 20px);
                            padding: 12px;
                            margin: 8px 0;
                            border: 1px solid #ccc;
                            border-radius: 6px;
                            font-size: 16px;
                        }}
                        input[type="submit"] {{
                            background-color: #007BFF;
                            color: white;
                            cursor: pointer;
                            border: none;
                        }}
                        input[type="submit"]:hover {{
                            background-color: #0056b3;
                        }}
                        label {{
                            font-weight: bold;
                            display: block;
                            margin-top: 12px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <form action="/configure" method="post">
                            <label for="ip">WLED IP:</label>
                            <input type="text" id="ip" name="ip" value="{ip}">

                            <label for="port">Port:</label>
                            <input type="number" id="port" name="port" value="{port}">

                            <label for="ssid">SSID:</label>
                            <input type="text" id="ssid" name="ssid" value="{ssid}">

                            <label for="pw">Parool:</label>
                            <input type="password" id="pw" name="pw" value="{pw}">

                            <input type="submit" value="Salvesta">
                        </form>
                    </div>
                </body>
                </html>
                """.format(
                ip=WLED_CONFIG['ip'],
                port=WLED_CONFIG['port'],
                ssid=WLED_CONFIG['ssid'],
                pw=WLED_CONFIG['pw']
                
            )
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            conn.send(html)
            conn.close()

def main():
    global sock

    connect_wifi()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    rotary = RotaryIRQ(pin_num_clk=PIN_CLK, pin_num_dt=PIN_DT)
    btn = Pin(PIN_BTN, Pin.IN, Pin.PULL_UP)

    send_udp({"on": wled_on, "bri": brightness})

    last_value = rotary.value()
    last_button_state = btn.value()
    last_activity = time.ticks_ms()
    button_held = False
    press_start = 0

    while True:
        current_value = rotary.value()
        if current_value != last_value:
            delta = current_value - last_value
            set_brightness(brightness + (delta * 5))
            last_value = current_value
            last_activity = time.ticks_ms()
            save_state()

        current_btn = btn.value()
        if current_btn == 0 and last_button_state == 1:
            press_start = time.ticks_ms()
            button_held = True
        elif current_btn == 0 and button_held:
            if time.ticks_diff(time.ticks_ms(), press_start) >= 10000:
                print("Entering AP mode")
                sock.close()
                enter_ap_mode()
        elif current_btn == 1 and last_button_state == 0:
            if button_held:
                if time.ticks_diff(time.ticks_ms(), press_start) < 10000:
                    toggle_wled()
                    last_activity = time.ticks_ms()
                    save_state()
                button_held = False
        
        last_button_state = current_btn

        if time.ticks_diff(time.ticks_ms(), last_activity) > 15000:
            print("Entering deep sleep")
            sock.close()
            save_state()
            deepsleep()

        time.sleep_ms(10)

if __name__ == "__main__":
    freq(80000000)
    cpu_freq = freq() // 1_000_000
    print("CPU speed:", cpu_freq, "MHz")
    print("Cold boot" if reset_cause() != DEEPSLEEP_RESET else "Wake from sleep")
    
    setup_wakeup()
    main()