# 🐱 Cat Chaos
*A reaction-based handheld game built with the Xiao ESP32-C3 and CircuitPython.*

---

##  Overview
Cat Chaos is a simple 90s-style handheld game.  
Players must follow instructions shown on the OLED and perform actions quickly using the rotary encoder, accelerometer, and buttons.  
The game includes multiple difficulty levels, ten progressively faster stages, NeoPixel feedback, buzzer tones, and a persistent high-score system.

---

##  How to Play

### **1. Difficulty Selection**
Use the rotary encoder to choose a difficulty:
- EASY  
- MEDIUM  
- HARD  

Press the encoder button to start.

### **2. Game Actions**
The OLED displays an action. Perform it before time runs out.

| Action        | Trigger Method                     |
|---------------|------------------------------------|
| **PAW**       | Press encoder button               |
| **TAIL_LEFT** | Rotate encoder Counter-Clockwise                |
| **TAIL_RIGHT**| Rotate encoder Clockwise               |
| **SHAKE**     | Shake the device                  |
| **FLIP**      | Flip device upside down            |

Fail → *Game Over*  
Clear all 10 levels → *You Win*

---

##  High Score System
If your score is within the top 3:
- Enter your initials using the rotary encoder  
- Score is saved into onboard flash (`highscores.json`)  
- High score list shown after every game  

**(Extra credit implemented)**

---

##  Hardware Components
- Xiao ESP32-C3  
- SSD1306 OLED (I2C)  
- ADXL345 accelerometer  
- Rotary encoder (CLK, DT, SW)  
- NeoPixel RGB LED  
- Piezo buzzer (PWM)  
- LiPo battery + switch  
- Perfboard with female headers  
- Laser-cut cat-head enclosure

---

##  Wiring Summary

### **I2C Devices**
| Device | Pin | Notes |
|--------|------|-------|
| OLED SSD1306 | SDA → D4, SCL → D5 | Address 0x3C |
| ADXL345 | SDA → D4, SCL → D5 | Address 0x53 |

### **Other Components**
| Component | ESP32-C3 Pin |
|-----------|---------------|
| Rotary Encoder CLK | D7 |
| Rotary Encoder DT | D6 |
| Encoder Button SW | D3 |
| NeoPixel | D2 |
| Buzzer (PWM) | D9 |
| Power | LiPo → Switch → 5V → GND |

---

##  Enclosure
A laser-cut **rounded cat-head** design featuring:
- OLED window  
- Rotary encoder hole  
- LED indicator hole  
- Two button holes  
- Side power switch  
- Bottom USB-C port  
- Internal space for battery + perfboard  

Design files provided in `Documentation/`.

---

##  Repository Structure
CatChaos/
│
├── README.md
│
├── src/
│   └── code.py
│
└── Documentation/
    ├── circuit_diagram1.pdf
    ├── System Block Diagram1.drawio.png
    ├── enclosure_design.svg


---

##  Running the Game
1. Install CircuitPython on the Xiao ESP32-C3  
2. Copy all files from `src/` to the device  
3. Add required libraries to `/lib/`  
4. Power via USB-C or LiPo battery  
5. Play Cat Chaos!

---

##  License
For educational use.

