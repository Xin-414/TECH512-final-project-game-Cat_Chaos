"""
CAT CHAOS GAME - Detailed Code Annotations
===========================================
This is a CircuitPython game that runs on microcontroller hardware.
It's a Simon-Says style memory game with a cat theme where players must
replicate sequences of actions using physical inputs (button, rotary encoder,
and accelerometer).
"""

import time           # For delays and timing
import board          # Hardware pin definitions for the microcontroller
import busio          # Communication protocols (I2C)
import neopixel       # RGB LED control
import pwmio          # Pulse Width Modulation for buzzer control
import random         # Random number generation for game sequences
import displayio      # Display management system
import terminalio     # Built-in terminal font
import json           # JSON file handling for high scores
import os             # Operating system interface (file operations)

from digitalio import DigitalInOut, Direction, Pull  # Digital pin control
from adafruit_display_text import label              # Text display on OLED
import adafruit_displayio_ssd1306                   # OLED driver (SSD1306 chip)
import adafruit_adxl34x                              # Accelerometer driver (ADXL345 chip)
import i2cdisplaybus                                 # I2C bus for display

 
# =========================================================
#  OLED DISPLAY INITIALIZATION (using displayio framework)
# =========================================================
# Release any previously used displays to avoid conflicts
displayio.release_displays()

# Initialize I2C communication bus
# SCL = Serial Clock Line, SDA = Serial Data Line
i2c = busio.I2C(board.SCL, board.SDA)

# Create display bus object with device address 0x3C (standard for SSD1306)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)

# Initialize 128x64 pixel OLED display
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)


def show_text(lines):
    """
    Display multiple lines of text on the OLED screen.
    
    Args:
        lines: List of strings, each string is one line of text
        
    How it works:
    1. Creates a display group (container for graphical elements)
    2. Iterates through each line of text
    3. Creates a label for each line positioned vertically
    4. Adds all labels to the group
    5. Sets the group as the display's content
    """
    group = displayio.Group()
    y = 5  # Starting vertical position (pixels from top)
    
    for txt in lines:
        # Create label: white text (0xFFFFFF), positioned at (5, y)
        t = label.Label(terminalio.FONT, text=txt, scale=1, color=0xFFFFFF, x=5, y=y)
        group.append(t)
        y += 10  # Move down 10 pixels for next line
        
    display.root_group = group  # Display the group


# =========================================================
#  NEOPIXEL (RGB LED) INITIALIZATION
# =========================================================
# Initialize one NeoPixel LED on pin D2 with 30% brightness
# NeoPixels are addressable RGB LEDs that can display any color
pixel = neopixel.NeoPixel(board.D2, 1, brightness=0.3)
pixel[0] = (0, 0, 0)  # Start with LED off (R=0, G=0, B=0)


# =========================================================
#  BUZZER (PIEZO SPEAKER) INITIALIZATION
# =========================================================
# Initialize PWM output on pin D10 for sound generation
# duty_cycle=0 means initially off, frequency=440Hz (musical note A)
buzzer = pwmio.PWMOut(board.D10, duty_cycle=0, frequency=440, variable_frequency=True)

def beep(freq=600, dur=0.1):
    """
    Play a tone on the buzzer.
    
    Args:
        freq: Frequency in Hz (higher = higher pitch)
        dur: Duration in seconds
        
    How PWM works for sound:
    - duty_cycle controls volume (20000 out of 65535 = ~30% volume)
    - Rapidly turning the buzzer on/off at 'freq' Hz creates the tone
    """
    buzzer.frequency = freq
    buzzer.duty_cycle = 20000  # Turn on at ~30% volume
    time.sleep(dur)            # Wait for duration
    buzzer.duty_cycle = 0      # Turn off


# =========================================================
#  ROTARY ENCODER INITIALIZATION
# =========================================================
# A rotary encoder is a knob that can be turned left/right and pressed
# It has three pins: CLK (clock), DT (data), SW (switch/button)

# CLK pin (D7) - clock signal
clk = DigitalInOut(board.D7)
clk.direction = Direction.INPUT
clk.pull = Pull.UP  # Pull-up resistor keeps pin HIGH when not grounded

# DT pin (D6) - data signal
dt = DigitalInOut(board.D6)
dt.direction = Direction.INPUT
dt.pull = Pull.UP

# SW pin (D3) - button press (active LOW, meaning pressed = False)
sw = DigitalInOut(board.D3)
sw.direction = Direction.INPUT
sw.pull = Pull.UP

# Variables to track encoder state
last_clk = clk.value
encoder_value = 0  # Cumulative rotation count
last_state = (clk.value, dt.value)

def update_encoder():
    """
    Read the rotary encoder and update encoder_value.
    
    How it works:
    - Rotary encoders generate quadrature signals (two signals 90° out of phase)
    - By comparing CLK and DT states, we determine rotation direction
    - Clockwise: DT is LOW when CLK goes HIGH
    - Counter-clockwise: DT is HIGH when CLK goes HIGH
    
    This is called "quadrature decoding"
    """
    global encoder_value, last_state
    state = (clk.value, dt.value)  # Read current state

    if state != last_state:  # State has changed
        # Check if CLK went from LOW to HIGH (rising edge)
        if last_state[0] == 0 and state[0] == 1:
            if state[1] == 0:      # If DT is LOW
                encoder_value += 1   # Clockwise rotation
            else:                   # If DT is HIGH
                encoder_value -= 1   # Counter-clockwise rotation

        last_state = state



# =========================================================
#  ACCELEROMETER INITIALIZATION
# =========================================================
# ADXL345 is a 3-axis accelerometer that measures acceleration in m/s²
# It detects tilt, shake, and orientation changes
accel = adafruit_adxl34x.ADXL345(i2c)

# Filtered acceleration values (exponential moving average)
fx = fy = fz = 0
alpha = 0.2  # Smoothing factor (0.2 = 20% new data, 80% old data)

def read_accel():
    """
    Read and filter accelerometer data.
    
    Returns:
        (fx, fy, fz): Filtered acceleration in x, y, z axes (m/s²)
        
    Filtering explanation:
    - Raw accelerometer data is noisy
    - Exponential moving average smooths the data
    - Formula: filtered = alpha * new + (1-alpha) * old
    - Lower alpha = more smoothing but slower response
    """
    global fx, fy, fz
    x, y, z = accel.acceleration  # Read raw values
    
    # Apply exponential moving average filter
    fx = alpha*x + (1-alpha)*fx
    fy = alpha*y + (1-alpha)*fy
    fz = alpha*z + (1-alpha)*fz
    
    return fx, fy, fz


# =========================================================
#  SPLASH SCREEN (STARTUP ANIMATION)
# =========================================================
def splash_screen():
    """
    Display animated intro screen when game starts.
    
    Sequence:
    1. Type out "CAT CHAOS" one letter at a time
    2. Show animated cat face with blinking heart
    3. Rainbow color cycle on LED
    4. Play musical beeps
    """
    title = "CAT CHAOS"
    
    # Type-writer effect: show one more letter each frame
    for i in range(1, len(title)+1):
        show_text([title[:i]])  # Slice: first i characters
        pixel[0] = (255, 80, 0)  # Orange color
        time.sleep(0.08)

    # Animation frames: alternate between normal and heart
    frames = [
        ["CAT CHAOS", "", " ^•ﻌ•^ "],    # Normal cat face
        ["CAT CHAOS", "", " ^•ﻌ•^♡"],   # Cat with heart
    ]
    
    # Loop animation 3 times
    for _ in range(3):
        for f in frames:
            show_text(f)
            pixel[0] = (0, 150, 255)  # Cyan color
            time.sleep(0.15)

    # Rainbow color sequence
    rainbow = [
        (255, 80, 0),    # Orange
        (255, 180, 0),   # Yellow
        (0, 200, 255),   # Cyan
        (0, 255, 150),   # Green
        (180, 0, 255)    # Purple
    ]
    for c in rainbow:
        pixel[0] = c
        time.sleep(0.15)

    # Musical beeps with increasing pitch
    for f in [700, 800, 900, 750]:
        beep(f, 0.08)

    pixel[0] = (0, 0, 0)  # Turn off LED


# =========================================================
#  DIFFICULTY SELECTION MENU
# =========================================================
difficulties = ["EASY", "MEDIUM", "HARD"]

def choose_difficulty():
    """
    Let player select difficulty using rotary encoder.
    
    Returns:
        Selected difficulty string ("EASY", "MEDIUM", or "HARD")
        
    Controls:
    - Rotate encoder to cycle through options
    - Press button to confirm selection
    """
    global encoder_value
    encoder_value = 0  # Reset encoder position

    while True:
        update_encoder()
        
        # Use modulo to cycle through 3 options (0, 1, 2)
        # abs() handles negative values from counter-clockwise rotation
        idx = abs(encoder_value) % 3

        # Display current selection
        show_text([
            "Select Difficulty:",
            f"> {difficulties[idx]}",  # '>' shows current selection
            "",
            "Press to Start"
        ])

        # Check if button is pressed (active LOW, so False = pressed)
        if not sw.value:
            beep(800)  # Confirmation beep
            return difficulties[idx]


# =========================================================
#  GAME LOGIC
# =========================================================
# Define the 5 possible actions players must perform
ACTIONS = ["PAW", "TAIL_LEFT", "TAIL_RIGHT", "SHAKE", "FLIP"]

def generate_sequence(level):
    """
    Generate a random sequence of actions for the player to perform.
    
    Args:
        level: Current game level (1-10)
        
    Returns:
        List of action strings, length = level + 1
        
    Example: level 1 returns 2 actions, level 5 returns 6 actions
    """
    return [random.choice(ACTIONS) for _ in range(level + 1)]


def detect_action(action, time_limit):
    """
    Wait for player to perform the specified action within time limit.
    
    Args:
        action: String indicating required action
        time_limit: Maximum seconds to wait
        
    Returns:
        True if action performed successfully, False if time runs out
        
    Action detection methods:
    - PAW: Button press (sw.value == False)
    - TAIL_LEFT: Encoder turned counter-clockwise (< -2)
    - TAIL_RIGHT: Encoder turned clockwise (> 2)
    - SHAKE: X-axis acceleration > 15 m/s² (shake sideways)
    - FLIP: Z-axis acceleration < -5 m/s² (flip upside down)
    """
    global encoder_value
    encoder_value = 0  # Reset encoder
    start = time.monotonic()  # Record start time (monotonic = doesn't reset)

    # Loop until time runs out
    while time.monotonic() - start < time_limit:

        update_encoder()           # Update encoder state
        x, y, z = read_accel()     # Read accelerometer

        # Check each action type
        if action == "PAW" and not sw.value:  # Button pressed
            pixel[0] = (0,255,0)  # Green = success
            beep(900)
            return True

        if action == "TAIL_LEFT" and encoder_value < -2:  # Turned left
            pixel[0] = (0,255,0)
            beep(800)
            return True

        if action == "TAIL_RIGHT" and encoder_value > 2:  # Turned right
            pixel[0] = (0,255,0)
            beep(850)
            return True

        if action == "SHAKE" and abs(x) > 15:  # Shaken hard
            pixel[0] = (0,255,0)
            beep(650)
            return True

        if action == "FLIP" and z < -5:  # Flipped upside down
            pixel[0] = (0,255,0)
            beep(500)
            return True

    # Time ran out - failure
    pixel[0] = (255,0,0)  # Red = failure
    beep(200)  # Low failure sound
    return False


def play_game(diff):
    """
    Main game loop - plays through 10 levels.
    
    Args:
        diff: Difficulty level ("EASY", "MEDIUM", "HARD")
        
    Returns:
        (score, win): Final score and whether player won (completed all levels)
        
    Scoring:
    - +1 point for each correct action
    - +5 bonus points for completing a level
    
    Time limits:
    - Starts at base time (2.0s/1.5s/1.0s for easy/medium/hard)
    - Decreases by 8% each level (multiplied by 0.92)
    - Formula: time = base * (0.92 ^ level)
    """
    # Set base time limit based on difficulty
    if diff == "EASY": base = 2.0
    elif diff == "MEDIUM": base = 1.5
    else: base = 1.0  # HARD

    score = 0

    # Play 10 levels
    for level in range(1, 11):
        seq = generate_sequence(level)  # Generate action sequence

        # Player must perform each action in sequence
        for i, act in enumerate(seq):
 
            pixel[0] = (0,0,255)  # Blue = waiting for input

            # Display instructions
            show_text([
                f"Level {level}",
                f"Step {i+1}/{len(seq)}",  # Current step / total steps
                f"Do: {act}"               # Action to perform
            ])

            # Calculate time limit (gets shorter each level)
            time_limit = base * (0.92 ** level)

            # Wait for player action
            if not detect_action(act, time_limit):
                return score, False  # Failed - game over

            score += 1  # Correct action

        # Completed level!
        score += 5  # Bonus points
        pixel[0] = (0,255,180)  # Cyan = level complete
        beep(700); beep(900)    # Success melody
        pixel[0] = (0,0,0)

    # Completed all 10 levels!
    return score, True


# =========================================================
#  HIGH SCORE SYSTEM (PERSISTENT STORAGE)
# =========================================================
HIGHSCORE_FILE = "highscores.json"

# Default high scores if file doesn't exist
DEFAULT_SCORES = [
    {"name": "AAA", "score": 0},
    {"name": "BBB", "score": 0},
    {"name": "CCC", "score": 0}
]


def load_highscores():
    """
    Load high scores from JSON file.
    
    Returns:
        List of dictionaries: [{"name": "ABC", "score": 100}, ...]
        
    Error handling:
    - If file doesn't exist or is corrupted, return default scores
    """
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_SCORES.copy()


def save_highscores(scores):
    """
    Save high scores to JSON file.
    
    Args:
        scores: List of score dictionaries to save
    """
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(scores, f)


LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def enter_initials():
    """
    Let player enter 3-letter name using rotary encoder.
    
    Returns:
        3-character string (e.g., "ABC")
        
    Controls:
    - Rotate encoder to select letter
    - Press button to confirm and move to next letter
    - Cycles through A-Z using modulo arithmetic
    """
    global encoder_value
    name = ["A", "A", "A"]  # Start with "AAA"
    pos = 0                 # Current letter position (0, 1, or 2)
    encoder_value = 0

    while True:
        update_encoder()
        
        # Select letter based on encoder position (cycles A-Z)
        idx = abs(encoder_value) % len(LETTERS)
        name[pos] = LETTERS[idx]

        # Display current name with all three positions
        show_text([
            "NEW HIGH SCORE!",
            "",
            f"Name: {''.join(name)}",  # Convert list to string
            "",
            f"Choose Letter {pos+1}/3"
        ])

        # Button pressed - confirm letter
        if not sw.value:
            beep(800)
            time.sleep(0.2)  # Debounce delay
            pos += 1
            encoder_value = 0  # Reset for next letter
            
            if pos >= 3:  # All 3 letters entered
                return "".join(name)


def show_highscores(scores):
    """
    Display top 3 high scores on screen.
    
    Args:
        scores: List of score dictionaries (already sorted)
        
    Waits for button press to continue.
    """
    lines = ["HIGH SCORES:"]
    
    # Format each score as "1. ABC  123"
    for i, s in enumerate(scores):
        lines.append(f"{i+1}. {s['name']}  {s['score']}")
    
    lines.append("")
    lines.append("Press to continue")
    show_text(lines)

    # Wait for button press
    while True:
        if not sw.value:
            time.sleep(0.2)  # Debounce
            return


# =========================================================
#  END SCREEN + HIGH SCORE INTEGRATION
# =========================================================
def end_screen(score, win):
    """
    Display game over screen and handle high score entry.
    
    Args:
        score: Player's final score
        win: True if player completed all levels, False if failed
        
    Process:
    1. Show win/loss screen
    2. Check if score qualifies for top 3
    3. If yes, let player enter initials
    4. Update and save high scores
    5. Display high score table
    """
    # Display appropriate end message
    if win:
        show_text(["YOU WIN!", f"Score: {score}", "", "Press to continue"])
        pixel[0] = (0,255,150)  # Green
        beep(900); beep(1100)   # Victory fanfare
    else:
        show_text(["GAME OVER", f"Score: {score}", "", "Press to continue"])
        pixel[0] = (255,0,0)    # Red
        beep(300)               # Failure sound

    # Wait for button press to continue
    while True:
        if not sw.value:
            break
    time.sleep(0.2)
    beep(600)

    # ----- High Score Handling -----
    scores = load_highscores()

    # Check if player's score beats the 3rd place score
    if score > scores[-1]["score"]:  # scores[-1] is last item (3rd place)
        name = enter_initials()      # Get player's name
        
        # Add new score to list
        scores.append({"name": name, "score": score})
        
        # Sort by score (highest first) and keep top 3
        scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:3]
        
        save_highscores(scores)  # Save to file

    show_highscores(scores)  # Display final high score table


# =========================================================
#  MAIN LOOP (GAME ENTRY POINT)
# =========================================================
splash_screen()  # Show intro animation

# Infinite game loop
while True:
    diff = choose_difficulty()    # Select difficulty
    score, win = play_game(diff)  # Play game
    end_screen(score, win)        # Show results and high scores
    # Loop automatically restarts game
