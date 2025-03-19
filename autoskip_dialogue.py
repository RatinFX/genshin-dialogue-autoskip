import os
from random import randint, uniform
from threading import Thread
from typing import Tuple, Union
from time import sleep
from win32api import GetSystemMetrics

from pyautogui import getActiveWindowTitle, pixel, pixelMatchesColor, press
from pynput.keyboard import Key, KeyCode, Listener
from dotenv import find_dotenv, load_dotenv, set_key

# Initial setup
os.system('cls')
load_dotenv()
print('Welcome to Genshin Impact Dialogue Skipper\n')

SCREEN_WIDTH = None
SCREEN_HEIGHT = None

# Whole script can be simplified because in the new genshin update the F key can be used to select dialogue options.

# Check if either screen dimension is missing from .env
if os.environ['WIDTH'] == '' or os.environ['HEIGHT'] == '':
    # Detect and set screen dimensions
    SCREEN_WIDTH = GetSystemMetrics(0)
    SCREEN_HEIGHT = GetSystemMetrics(1)

    # In case the resolution is not correct, ask for the correct resolution
    print(f'Detected Resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}')
    print('Is the resolution correct? (y/n)')
    response = input()

    if response.lower().startswith('n'):
        print('Enter resolution width: ', end='')
        SCREEN_WIDTH = int(input())
        print('Enter resolution height: ', end='')
        SCREEN_HEIGHT = int(input())
        print('\nNew resolution set to ' + str(SCREEN_WIDTH) + 'x' + str(SCREEN_HEIGHT) + '\n')

    # Write changes to .env file
    dotenv_file = find_dotenv()
    set_key(dotenv_file, "WIDTH", str(SCREEN_WIDTH), quote_mode="never")
    set_key(dotenv_file, "HEIGHT", str(SCREEN_HEIGHT), quote_mode="never")
else:
    # Read screen dimensions from .env
    SCREEN_WIDTH = int(os.getenv('WIDTH'))
    SCREEN_HEIGHT = int(os.getenv('HEIGHT'))


def width_adjust(x: int) -> int:
    """Adjust variables to the width of the screen."""
    return int(x/1920 * SCREEN_WIDTH)


def height_adjust(y: int) -> int:
    """Adjust variables to the height of the screen."""
    return int(y/1080 * SCREEN_HEIGHT)


def get_position_right(hdpos_x: int, doublehdpos_x: int, SCREEN_WIDTH: int, extra: float) -> int:
    """
    Use this if the pixel is bound to the right side.
    Calculates the distance of the pixel from the right side of the screen. Returns position of pixel on x.
    hdpos_x
    position of the pixel on 1920*1080 display.
    doublehdpos_x
    position of the pixel on 3840*1080 display.
    SCREEN_WIDTH
    width of the screen we want to get the position for.
    extra
    we need an extra multiplier for screens above 3840*1920
    :return: position
    """

    if SCREEN_WIDTH <= 3840:  # above 3840 we need an extra multiplier
        extra = 0
    diff = doublehdpos_x - hdpos_x
    change_per_pixel = diff/1920
    screen_diff = SCREEN_WIDTH - 1920
    extra_pixels = screen_diff * (change_per_pixel+extra)
    position = int(hdpos_x + extra_pixels)

    return position


def get_position_left(hdpos_x: int, doublehdpos_x: int, SCREEN_WIDTH: int) -> int:
    """
    Use this if the pixel is bound to the left side.
    Calculates the distance of the pixel from the left side of the screen. Returns position of pixel on x
    hdpos_x
    position of the pixel on 1920*1080 display.
    doublehdpos_x
    position of the pixel on 3840*1080 display.
    SCREEN_WIDTH
    width of the screen we want to get the position for.
    :return: position
    """

    diff = doublehdpos_x - hdpos_x
    change_per_pixel = diff/1920
    screen_diff = SCREEN_WIDTH - 1920
    extra_pixels = screen_diff * change_per_pixel
    position = int(hdpos_x + extra_pixels)

    return position


# Top left white part of the "auto" or "playing" button
if SCREEN_WIDTH > 1920 and float(int(SCREEN_HEIGHT)/int(SCREEN_WIDTH)) != float(0.5625):
    # I will leave the flexible position here, but I found out that it won't be greater than 230.
    # So it might have to be removed if someone can test with a 1440p screen.
    PLAYING_ICON_X = get_position_left(56, 230, SCREEN_WIDTH)
    if PLAYING_ICON_X > 231:
        PLAYING_ICON_X = 230
else:
    PLAYING_ICON_X = width_adjust(56)
PLAYING_ICON_Y = height_adjust(47)


# Pixel coordinates for white part of the speech bubble in bottom dialogue option
if SCREEN_WIDTH > 1920 and float(int(SCREEN_HEIGHT)/int(SCREEN_WIDTH)) != float(0.5625):
    DIALOGUE_ICON_X = get_position_right(1301, 2770, SCREEN_WIDTH, 0.02)
else:
    DIALOGUE_ICON_X = width_adjust(1301)
DIALOGUE_ICON_LOWER_Y = height_adjust(808)
DIALOGUE_ICON_HIGHER_Y = height_adjust(790)


# TODO: add `get_position_left()` / `get_position_right()` for wider res - 16:9 user here, so..
# TODO: resolve random "F" and "ESC" spam in the inventory and/or overworld - just disable it after you're done


# Top left "logs" button
LOGS_ICON_X = width_adjust(241)
LOGS_ICON_Y = height_adjust(47)

# Top left "hide-ui" button
HIDEUI_ICON_X = width_adjust(324)
HIDEUI_ICON_Y = height_adjust(52)

# "Readable content" top left hamburger icon
READABLE_CONTENT_X = width_adjust(80)
READABLE_CONTENT_Y = height_adjust(40)

# "Readable content" bottom decor
READABLE_CONTENT_BOTTOM_X = width_adjust(956)
READABLE_CONTENT_BOTTOM_Y = height_adjust(1050)

# Top left "Back" icon
TOP_LEFT_BACK_ICON_X = width_adjust(45)
TOP_LEFT_BACK_ICON_Y = height_adjust(45)

# Top right "X" icon
TOP_RIGHT_CLOSE_ICON_X = width_adjust(1843)
TOP_RIGHT_CLOSE_ICON_Y = height_adjust(48)

# "Click to continue" during black-screen white-text
CLICK_TO_CONTINUE_X = width_adjust(856)
CLICK_TO_CONTINUE_Y = height_adjust(968)

# Black screen
BLACK_SCREEN_LEFT_X = width_adjust(300)
BLACK_SCREEN_RIGHT_X = width_adjust(1700)
BLACK_SCREEN_Y = height_adjust(727)

# Pixel coordinates near middle of the screen known to be white while the game is loading
# This should work fine on most screen sizes I think - @withoutface
LOADING_SCREEN_X = width_adjust(1200)
LOADING_SCREEN_Y = height_adjust(700)

def random_interval() -> float:
    """
    Return a random interval between 0.12 and 0.18 seconds, or 0.18 and 0.2 seconds if a 6 is rolled.
    :return: A random interval between 0.12 and 0.18 seconds, or 0.18 and 0.3 seconds if a 6 is rolled.
    """

    return uniform(0.18, 0.2) if randint(1, 6) == 6 else uniform(0.12, 0.18)


def on_press(key: (Union[Key, KeyCode, None])) -> None:
    """
    Start, stop, or exit the program based on the key pressed.
    :param key: The key pressed.
    :return: None
    """

    key_pressed = str(key)

    if key_pressed == 'Key.f8':
        main.status = 'run'
        print('RUNNING')
    elif key_pressed == 'Key.f9':
        main.status = 'pause'
        print('PAUSED')
    elif key_pressed == 'Key.f12':
        main.status = 'exit'
        exit()


def main() -> None:
    """
    Skip Genshin Impact dialogue when it's present based on the colors of 3 specific pixels.
    :return: None
    """

    def is_genshinimpact_active():
        """Check if Genshin Impact is the active window."""
        return getActiveWindowTitle() == "Genshin Impact"

    def is_dialogue_playing():
        return pixelMatchesColor(PLAYING_ICON_X, PLAYING_ICON_Y, (236, 229, 216))

    def is_dialogue_option_available():
        # Confirm loading screen is not white
        if pixelMatchesColor(LOADING_SCREEN_X, LOADING_SCREEN_Y, (255, 255, 255)):
            return False
            
        if pixelMatchesColor(TOP_LEFT_BACK_ICON_X, TOP_LEFT_BACK_ICON_Y, (59, 66, 85), tolerance=5):
            return False

        if pixelMatchesColor(TOP_RIGHT_CLOSE_ICON_X, TOP_RIGHT_CLOSE_ICON_Y, (59, 66, 85), tolerance=5):
            return False

        # Check if higher dialogue icon pixel is white
        if pixelMatchesColor(DIALOGUE_ICON_X, DIALOGUE_ICON_HIGHER_Y, (255, 255, 255), tolerance=5):
            return True

        # Check if lower dialogue icon pixel is white
        if pixelMatchesColor(DIALOGUE_ICON_X, DIALOGUE_ICON_LOWER_Y, (255, 255, 255), tolerance=5):
            return True

        # Check if "Click to continue" pixel is yellow
        if pixelMatchesColor(CLICK_TO_CONTINUE_X, CLICK_TO_CONTINUE_Y, (255, 195, 0), tolerance=5) and \
            pixelMatchesColor(BLACK_SCREEN_LEFT_X, BLACK_SCREEN_Y, (0, 0, 0)) and \
            pixelMatchesColor(BLACK_SCREEN_RIGHT_X, BLACK_SCREEN_Y, (0, 0, 0)):
            return True

        return False

    def dialogue_should_esc():
        # Top left Book is yellow and top right X icon pixel is gray
        if pixelMatchesColor(READABLE_CONTENT_X, READABLE_CONTENT_Y, (164, 146, 111), tolerance=5) or \
           pixelMatchesColor(READABLE_CONTENT_BOTTOM_X, READABLE_CONTENT_BOTTOM_Y, (79, 74, 65), tolerance=5):

            if pixelMatchesColor(TOP_RIGHT_CLOSE_ICON_X, TOP_RIGHT_CLOSE_ICON_Y, (161, 144, 109), tolerance=5) or \
               pixelMatchesColor(TOP_RIGHT_CLOSE_ICON_X, TOP_RIGHT_CLOSE_ICON_Y, (211, 188, 142)):
                return True

        return False

    main.status = 'pause'

    print('-------------\n'
          'F8 to start\n'
          'F9 to stop\n'
          'F12 to quit\n'
          '-------------')

    while True:
        while main.status == 'pause':
            sleep(0.5)

        if main.status == 'exit':
            print('Main program closing')
            break

        if is_genshinimpact_active() and (is_dialogue_playing() or is_dialogue_option_available()):
            press('f')

        if is_genshinimpact_active() and dialogue_should_esc() and random_interval() < 0.12:
            press('esc')


if __name__ == "__main__":
    Thread(target=main).start()

    with Listener(on_press=on_press) as listener:
        listener.join()
