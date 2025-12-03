import os
from random import randint, uniform
from threading import Thread
from time import perf_counter, sleep
from typing import Union
from win32api import GetSystemMetrics  # type: ignore[import-untyped]

from pyautogui import getActiveWindowTitle, press, pixelMatchesColor  # type: ignore[import-untyped]
from pynput.keyboard import Key, KeyCode, Listener  # type: ignore[import-untyped]
from dotenv import find_dotenv, load_dotenv, set_key  # type: ignore[import-not-found]

# Initial setup
os.system("cls")

# Create .env from .env-example if .env doesn't exist
if not os.path.exists(".env") and os.path.exists(".env-example"):
    import shutil
    shutil.copy(".env-example", ".env")
    print("  Created .env from .env-example\n")

load_dotenv()
print("\n" + "=" * 60)
print("  GENSHIN IMPACT - DIALOGUE AUTO-SKIPPER")
print("=" * 60)
print("  Version 1.0 | Keyboard & Mouse Edition")
print("=" * 60 + "\n")

# Check if either screen dimension is missing from .env
if os.environ.get("WIDTH", "") == "" or os.environ.get("HEIGHT", "") == "":
    # Detect and set screen dimensions
    SCREEN_WIDTH = GetSystemMetrics(0)
    SCREEN_HEIGHT = GetSystemMetrics(1)

    print(f"  Resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}\n")

    # Write changes to .env file
    dotenv_file = find_dotenv()
    if dotenv_file:
        set_key(dotenv_file, "WIDTH", str(SCREEN_WIDTH), quote_mode="never")
        set_key(dotenv_file, "HEIGHT", str(SCREEN_HEIGHT), quote_mode="never")
    else:
        # Create .env file if it doesn't exist
        with open(".env", "w") as f:
            f.write(f"WIDTH={SCREEN_WIDTH}\n")
            f.write(f"HEIGHT={SCREEN_HEIGHT}\n")
else:
    # Read screen dimensions from .env
    width_str = os.getenv("WIDTH")
    height_str = os.getenv("HEIGHT")
    if width_str is None or height_str is None:
        raise ValueError("WIDTH or HEIGHT environment variable is None")
    SCREEN_WIDTH = int(width_str)
    SCREEN_HEIGHT = int(height_str)


def width_adjust(x: int) -> int:
    """Adjust variables to the width of the screen."""
    return int(x / 1920 * SCREEN_WIDTH)


def height_adjust(y: int) -> int:
    """Adjust variables to the height of the screen."""
    return int(y / 1080 * SCREEN_HEIGHT)


def get_position_right(
    hdpos_x: int, doublehdpos_x: int, SCREEN_WIDTH: int, extra: float
) -> int:
    """
    Use this if the pixel is bound to the right side.
    Calculates the distance of the pixel from the right side of the screen. Returns position of pixel on x.
    """
    if SCREEN_WIDTH <= 3840:  # above 3840 we need an extra multiplier
        extra = 0
    diff = doublehdpos_x - hdpos_x
    change_per_pixel = diff / 1920
    screen_diff = SCREEN_WIDTH - 1920
    extra_pixels = screen_diff * (change_per_pixel + extra)
    position = int(hdpos_x + extra_pixels)
    return position


def get_position_left(hdpos_x: int, doublehdpos_x: int, SCREEN_WIDTH: int) -> int:
    """
    Use this if the pixel is bound to the left side.
    Calculates the distance of the pixel from the left side of the screen. Returns position of pixel on x
    """
    diff = doublehdpos_x - hdpos_x
    change_per_pixel = diff / 1920
    screen_diff = SCREEN_WIDTH - 1920
    extra_pixels = screen_diff * change_per_pixel
    position = int(hdpos_x + extra_pixels)
    return position


# Pixel coordinates for white part of the autoplay button
if SCREEN_WIDTH > 1920 and float(int(SCREEN_HEIGHT) / int(SCREEN_WIDTH)) != float(0.5625):
    PLAYING_ICON_X = get_position_left(70, 230, SCREEN_WIDTH) # 230 at 3840
    if PLAYING_ICON_X > 230:
        PLAYING_ICON_X = 230
    PLAYING_ICON_Y = height_adjust(46)
else:
    PLAYING_ICON_X = width_adjust(70)
PLAYING_ICON_Y = height_adjust(37)

# Pixel coordinates for white part of the speech bubble in bottom dialogue option
if SCREEN_WIDTH > 1920 and float(int(SCREEN_HEIGHT) / int(SCREEN_WIDTH)) != float(0.5625):
    DIALOGUE_ICON_X = get_position_right(1301, 2770, SCREEN_WIDTH, 0.02)
    DIALOGUE_ICON_LOWER_Y = height_adjust(810)
    DIALOGUE_ICON_HIGHER_Y = height_adjust(792)
else:
    DIALOGUE_ICON_X = width_adjust(1301)
DIALOGUE_ICON_LOWER_Y = height_adjust(808)
DIALOGUE_ICON_HIGHER_Y = height_adjust(790)

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

CLICK_TO_CONTINUE_LOWER_X = width_adjust(960)
CLICK_TO_CONTINUE_LOWER_Y = height_adjust(1026)

# Black screen
BLACK_SCREEN_LEFT_X = width_adjust(300)
BLACK_SCREEN_RIGHT_X = width_adjust(1700)
BLACK_SCREEN_Y = height_adjust(727)

# Pixel coordinates near middle of the screen known to be white while the game is loading
LOADING_SCREEN_X = width_adjust(1200)
LOADING_SCREEN_Y = height_adjust(700)


def random_f_key_interval() -> float:
    """
    Return a random interval between F key presses using original timing.
    Most of the time: 0.12-0.18 seconds
    Sometimes (1 in 6 chance): 0.18-0.2 seconds for variation
    :return: A random interval in seconds (same as original script)
    """
    return uniform(0.18, 0.2) if randint(1, 6) == 6 else uniform(0.12, 0.18)


def should_take_break() -> bool:
    """
    Determine if we should take an occasional break.
    1 in 25 chance (4%) of taking a break.
    :return: True if we should take a break
    """
    return randint(1, 25) == 1


def take_random_break() -> float:
    """
    Take a random break between 1-4 seconds.
    :return: Duration of the break in seconds
    """
    break_duration = uniform(1.0, 4.0)
    print(f"  Taking a {break_duration:.1f}s break...")
    return break_duration


class MainStatus:
    """Class to hold the status of the main loop."""

    def __init__(self) -> None:
        self.status: str = "pause"


main_status = MainStatus()

last_log = ""


def log_once(message: str) -> None:
    """Print a message only if it's different from the last logged message."""
    global last_log
    if message != last_log:
        print(message)
        last_log = message

def on_press(key: Union[Key, KeyCode, None]) -> None:
    """
    Start, stop, or exit the program based on the key pressed.
    :param key: The key pressed.
    :return: None
    """
    key_pressed = str(key)

    if key_pressed == "Key.f8":
        main_status.status = "run"
        print("\n" + "=" * 50)
        print("  STATUS: RUNNING")
        print("  Auto-skip is now ACTIVE")
        print("=" * 50 + "\n")
    elif key_pressed == "Key.f9":
        main_status.status = "pause"
        print("\n" + "=" * 50)
        print("  STATUS: PAUSED")
        print("  Auto-skip is now INACTIVE")
        print("=" * 50 + "\n")
    elif key_pressed == "Key.f12":
        main_status.status = "exit"
        print("\n" + "=" * 50)
        print("  Shutting down... Goodbye!")
        print("=" * 50 + "\n")
        exit()


def main() -> None:
    """
    Automatically press F key when dialogue is detected in Genshin Impact.
    Uses original dialogue detection logic but replaces clicks with F key presses.
    Includes random delays and occasional breaks for natural behavior.
    :return: None
    """

    def is_genshin_impact_active() -> bool:
        """Check if Genshin Impact is the active window."""
        title = getActiveWindowTitle()
        return bool(title == "Genshin Impact")

    def is_dialogue_playing() -> bool:
        """Check if dialogue is currently playing (autoplay button visible)."""
        try:
            return pixelMatchesColor(PLAYING_ICON_X, PLAYING_ICON_Y, (236, 229, 216), tolerance=5)
        except Exception:
            return False

    def is_dialogue_option_available() -> bool:
        """Check if dialogue options are available."""
        try:
            # Confirm loading screen is not white
            if pixelMatchesColor(LOADING_SCREEN_X, LOADING_SCREEN_Y, (255, 255, 255)):
                log_once("- Stop | Loading screen")
                return False

            # Check for back icon (menu screen)
            if pixelMatchesColor(TOP_LEFT_BACK_ICON_X, TOP_LEFT_BACK_ICON_Y, (59, 66, 85), tolerance=5):
                log_once("- Stop | Top-left BACK icon")
                return False

            # Check for close icon (menu screen)
            if pixelMatchesColor(TOP_RIGHT_CLOSE_ICON_X, TOP_RIGHT_CLOSE_ICON_Y, (59, 66, 85), tolerance=5):
                log_once("- Stop | Top-right CLOSE icon")
                return False

            # Check if higher dialogue icon pixel is white
            if pixelMatchesColor(DIALOGUE_ICON_X, DIALOGUE_ICON_HIGHER_Y, (255, 255, 255), tolerance=5):
                log_once("> Choice (higher)")
                return True

            # Check if lower dialogue icon pixel is white
            if pixelMatchesColor(DIALOGUE_ICON_X, DIALOGUE_ICON_LOWER_Y, (255, 255, 255), tolerance=5):
                log_once("> Choice (lower)")
                return True

            # Check if "Click to continue" pixel is yellow (black-screen white-text)
            if pixelMatchesColor(CLICK_TO_CONTINUE_X, CLICK_TO_CONTINUE_Y, (255, 190, 0), tolerance=5) and \
                pixelMatchesColor(BLACK_SCREEN_LEFT_X, BLACK_SCREEN_Y, (0, 0, 0)) and \
                pixelMatchesColor(BLACK_SCREEN_RIGHT_X, BLACK_SCREEN_Y, (0, 0, 0)):
                log_once("> Click to continue (bottom yellow + black screen)")
                return True
                
            if pixelMatchesColor(CLICK_TO_CONTINUE_LOWER_X, CLICK_TO_CONTINUE_LOWER_Y, (255, 190, 0), tolerance=5):
                log_once("> Click to continue (bottom yellow)")
                return True

            return False
        except Exception:
            return False

    def dialogue_should_esc() -> bool:
        """Check if ESC should be pressed (readable content screens)."""
        try:
            # Top left Book is yellow and top right X icon pixel is gray
            if pixelMatchesColor(READABLE_CONTENT_X, READABLE_CONTENT_Y, (164, 146, 111), tolerance=5) or \
               pixelMatchesColor(READABLE_CONTENT_BOTTOM_X, READABLE_CONTENT_BOTTOM_Y, (79, 74, 65), tolerance=5):

                if pixelMatchesColor(TOP_RIGHT_CLOSE_ICON_X, TOP_RIGHT_CLOSE_ICON_Y, (161, 144, 109), tolerance=5) or \
                   pixelMatchesColor(TOP_RIGHT_CLOSE_ICON_X, TOP_RIGHT_CLOSE_ICON_Y, (211, 188, 142)):
                    log_once("> ESC (full-screen readable content)")
                    return True

            return False
        except Exception:
            return False

    main_status.status = "pause"
    last_f_press = 0.0
    next_f_interval = random_f_key_interval()

    # Break tracking
    last_break_check = perf_counter()
    break_check_interval = 30.0  # Check for breaks every 30 seconds

    print("\n" + "=" * 60)
    print("  READY TO START")
    print("=" * 60)
    print("  Controls:")
    print("    [F8]  - Start Auto-Skip")
    print("    [F9]  - Pause Auto-Skip")
    print("    [F12] - Exit Program")
    print("=" * 60)
    print("\n  Waiting for input...\n")

    while True:
        current_time = perf_counter()

        # Handle pause state
        while main_status.status == "pause":
            sleep(0.5)
            current_time = perf_counter()  # Update time after pause
            last_f_press = current_time  # Reset timing after pause

        # Handle exit
        if main_status.status == "exit":
            break

        # Only proceed if Genshin Impact is active
        if not is_genshin_impact_active():
            sleep(0.5)
            continue

        # Check if ESC should be pressed for readable content
        if dialogue_should_esc() and random_f_key_interval() < 0.12:
            try:
                press("esc")
            except Exception as e:
                print(f"\n  Error pressing ESC key: {e}")
            sleep(0.1)
            continue

        # Check if dialogue is active (either playing or options available)
        dialogue_active = is_dialogue_playing() or is_dialogue_option_available()

        if not dialogue_active:
            sleep(0.1)
            continue

        # Check if it's time for an occasional break
        if current_time - last_break_check > break_check_interval:
            last_break_check = current_time
            if should_take_break():
                break_duration = take_random_break()
                sleep(break_duration)
                # Reset timing after break
                last_f_press = perf_counter()
                next_f_interval = random_f_key_interval()
                continue

        # Check if it's time to press F
        if current_time - last_f_press >= next_f_interval:
            try:
                press("f")
            except Exception as e:
                print(f"\n  Error pressing F key: {e}")

            # Set up next F press timing
            last_f_press = current_time
            next_f_interval = random_f_key_interval()

        # Small sleep to prevent excessive CPU usage
        sleep(0.05)


if __name__ == "__main__":
    Thread(target=main).start()

    with Listener(on_press=on_press) as listener:
        listener.join()
