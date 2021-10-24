from pynput.mouse import Controller
from pynput import keyboard
from threading import Thread
import time, random, pyautogui
from ctypes import windll


RESOLUTION = (1024, 768)


if RESOLUTION == (1024, 768):
    # bottom dialogue option for 1024*768 windowed
    MIN_X = 1584
    MAX_X = 1766
    MIN_Y = 914
    MAX_Y = 942


dc= windll.user32.GetDC(0)
mouse = Controller()


def getpixel(x,y):
    return tuple(int.to_bytes(windll.gdi32.GetPixel(dc,x,y), 3, "little"))


def random_interval():
    if random.randrange(1,7) == 6:
        return random.uniform(0.18, 0.3)
    return random.uniform(0.12, 0.18)


def random_cursor_position():
    x = random.randrange(MIN_X, MAX_X+1)
    y = random.randrange(MIN_Y, MAX_Y+1)
    position = (x, y)
    print("Cursor moved to: ", position)
    return position


def exit_program():
    def on_press(key):
        if str(key) == 'Key.f8':
            mouse.position = random_cursor_position()
            main.status = 'run'

        elif str(key) == 'Key.f9':
            print("PAUSED")
            main.status = 'pause'

        elif str(key) == 'Key.f12':
            main.status = 'exit'
            exit()
    
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


def main():
    main.status = 'pause'
    print('-------------')
    print("F8 to start")
    print("F9 to stop")
    print("F12 to quit")
    print('-------------')

    while True:
        while main.status == 'pause':
            time.sleep(0.5)

        if main.status == 'exit':
            print('Main program closing')
            break
        
        print('running')
        time.sleep(random_interval())
        pyautogui.click()
        
    
Thread(target=main).start()
Thread(target=exit_program).start()

