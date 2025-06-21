# 🛠 Serial Bridge GUI for Renesas FDT

This project is a graphical user interface (GUI) tool built with Python and PyQt5. It is designed to facilitate serial communication between a real COM port (connected to a Renesas microcontroller) and a virtual COM port used by Renesas Flash Development Toolkit (FDT).

## 📦 Features

- Graphical control of serial bridge between two COM ports (real ↔ virtual)
- Ability to boot a Renesas R8C microcontroller into **MODE 3** (via DTR/RTS control)
- Automatic or manual FDT launching
- ID check command (verifies communication with target MCU)
- Echo filtering to prevent feedback between Rx and Tx (important in hardware loopback setups)
- Real-time log console for serial events

## 📂 Files

| File | Description |
|------|-------------|
| `main.py` | Main GUI script, handles UI and logic for port control and FDT launching |
| `serial_bridge_class.py` | Background thread-based class that handles the serial bridging and echo filtering |
| `Screen01.ui` | PyQt5 UI layout file created with Qt Designer |
| `run_gui.bat` | Batch file to start the app via `main.py` |
| `dist/main.exe` | (Optional) Standalone compiled version using `pyinstaller` |

## 🧰 Requirements

- Python 3.8+ (if not using EXE)
- `pyqt5`, `pyserial`
- Virtual COM ports created using [com0com](https://sourceforge.net/projects/com0com/)

## ⚙️ Boot Sequence

The `Boot` button:
1. Controls **DTR** and **RTS** to trigger MODE 3 entry.
2. Sends synchronization bytes (7*0x00, 0xB0  only 9600bps).
3. Performs an ID check via serial.

## ▶ How to Use
R8C(R5Fxxxx) BOOT Mode3 <-> Real port (bayt manipulate)<-> Virtual ComPort <-> Mode2 FDT
1. Connect the hardware and create a virtual COM pair using com0com.
2. Start the app using `run_gui.bat` or `main.exe`.
3. Select real and virtual ports from dropdowns.
4. Click `Boot` to enter programming mode.
5. Click `Start FDT` to launch Renesas FDT.

---

**Developed for quick R8C FDT flashing in modern systems.**







**Demo**  
[![Watch the demo](https://img.youtube.com/vi/djGYxQSHl3w/0.jpg)](https://youtu.be/djGYxQSHl3w)





