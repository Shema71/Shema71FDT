import sys
import os
import threading
import subprocess
import ctypes
import time
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QFileDialog
from serial_bridge_class import SerialBridge  # Импортираме нашия бридж клас

class Communicator(QObject):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    baudrate_signal = pyqtSignal(str)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        try:
            uic.loadUi(self.resource_path("Screen01.ui"), self)
        except Exception as e:
            print(f"Грешка при зареждане на UI: {e}")
            sys.exit(1)

        self.comm = Communicator()
        self.comm.log_signal.connect(self.log_to_console)
        self.comm.status_signal.connect(self.update_status)
        self.comm.baudrate_signal.connect(self.update_baudrate)

        self.btnBoot.clicked.connect(self.boot_controller_mode3)
        self.btnStartFDT.clicked.connect(self.start_fdt)

        self.real_port = None
        self.virt_port = None
        self.bridge = None

        self.refresh_ports()

        if not self.is_admin():
            self.comm.log_signal.emit("Създаването на виртуални портове изисква администраторски права.")
            self.comm.log_signal.emit("Моля, създайте виртуални COM портове ръчно с помощта на com0com.")
            self.comm.log_signal.emit("Скриптът ще ги разпознае автоматично при следващото стартиране.")

    def resource_path(self, relative_path):
        """Позволява работа със скрипта като .exe с PyInstaller"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def refresh_ports(self):
        self.comboRealPort.clear()
        self.comboVirtPort.clear()

        real_ports, virtual_ports = self.get_serial_ports()
        if not real_ports:
            self.comm.log_signal.emit("⚠ Не са намерени реални серийни портове!")
        else:
            self.comboRealPort.addItems(real_ports)

        if not virtual_ports:
            self.comm.log_signal.emit("⚠ Не са намерени виртуални серийни портове!")
        else:
            self.comboVirtPort.addItems(virtual_ports)

        self.activate_selected_ports()
        self.start_bridge()

    def get_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        real_ports = []
        virtual_ports = []

        for port in ports:
            description = getattr(port, 'description', '')
            if 'com0com' in description.lower() or 'virtual' in description.lower():
                virtual_ports.append(port.device)
            else:
                real_ports.append(port.device)

        return real_ports, virtual_ports

    def activate_selected_ports(self):
        real_name = self.comboRealPort.currentText()
        virt_name = self.comboVirtPort.currentText()

        if self.real_port and self.real_port.is_open:
            self.real_port.close()
        if self.virt_port and self.virt_port.is_open:
            self.virt_port.close()

        try:
            self.real_port = serial.Serial(real_name, baudrate=9600, timeout=1)
            self.comm.log_signal.emit(f"✅ Успешно отворен реален порт: {real_name}")
        except Exception as e:
            self.comm.log_signal.emit(f"❌ Неуспешно отваряне на реален порт: {e}")

        try:
            self.virt_port = serial.Serial(virt_name, baudrate=9600, timeout=1)
            self.comm.log_signal.emit(f"✅ Успешно отворен виртуален порт: {virt_name}")
        except Exception as e:
            self.comm.log_signal.emit(f"❌ Неуспешно отваряне на виртуален порт: {e}")

    def start_bridge(self):
        if self.bridge:
            self.bridge.stop()
        if self.real_port and self.virt_port:
            self.bridge = SerialBridge(self.real_port, self.virt_port, self.comm)

    def start_fdt(self):
        def find_fdt_exe():
            paths = []
            for path in os.environ["PATH"].split(os.pathsep):
                exe = os.path.join(path, "FDT.exe")
                paths.append(exe)
                if os.path.isfile(exe):
                    return exe, paths

            fallback = [
                r"C:\Program Files (x86)\Renesas\FDT4.09\FDT.exe",
                r"C:\Renesas\FDT\FDT.exe"
            ]
            for p in fallback:
                paths.append(p)
                if os.path.isfile(p):
                    return p, paths

            return None, paths

        self.comm.log_signal.emit("🔍 Търся FDT.exe.")
        fdt_path, paths = find_fdt_exe()

        if not fdt_path:
            self.comm.log_signal.emit("❌ FDT.exe не е намерен автоматично.")
            for p in paths:
                self.comm.log_signal.emit(f"  - {p}")
            fdt_path, _ = QFileDialog.getOpenFileName(self, "Избери FDT.exe", "", "FDT (*.exe)")
            if not fdt_path:
                self.comm.log_signal.emit("❌ FDT не е избран.")
                return

        try:
            subprocess.Popen([fdt_path], shell=True)
            self.comm.log_signal.emit(f"✅ FDT стартирано: {fdt_path}")
        except Exception as e:
            self.comm.log_signal.emit(f"❌ Грешка при стартиране на FDT: {e}")

    def boot_controller_mode3(self):
        try:
            if not self.real_port or not self.real_port.is_open:
                self.comm.log_signal.emit("❌ Реалният порт не е отворен.")
                return

            self.real_port.setDTR(False)
            self.comm.log_signal.emit("DTR=HIGH (реално) => Освобождава Tx_Break")
            self.real_port.setRTS(True)
            self.comm.log_signal.emit("RTS=LOW (реално) => RESET активен")
            self.delay_precise_ms(200)

            self.real_port.setDTR(True)
            self.comm.log_signal.emit("DTR=LOW (реално) => Заема Tx_Break")
            self.real_port.setRTS(False)
            self.comm.log_signal.emit("RTS=HIGH (реално) => RESET Освободен")
            self.delay_precise_ms(200)

            self.real_port.setRTS(True)
            self.comm.log_signal.emit("RTS=LOW (реално) => RESET активен")
            self.delay_precise_ms(200)

            self.real_port.setRTS(False)
            self.comm.log_signal.emit("RTS=HIGH (реално) => RESET Освободен")
            self.delay_precise_ms(200)

            self.real_port.setDTR(False)
            self.comm.log_signal.emit("DTR=HIGH (реално) => Освобождава BREAK")
            self.delay_precise_ms(240)

            for _ in range(16):
                self.real_port.reset_input_buffer()
                self.real_port.write(b'\x00')
                self.comm.log_signal.emit("Изпратено: 00")
                self.delay_precise_ms(50)

            self.real_port.reset_input_buffer()
            self.real_port.write(b'\xB0')
            self.delay_precise_ms(5)
            response = self.real_port.read(1)

            if response == b'\xB0':
                self.comm.log_signal.emit("✅ Контролерът стартира успешно в MODE 3.")
            else:
                self.comm.log_signal.emit(f"❌ Контролерът не върна B0. Получено: {response.hex().upper() if response else 'празно'}")
                return

            self.comm.log_signal.emit("=== Започва ID проверка ===")
            def check_id(id_bytes):
                self.real_port.reset_input_buffer()
                cmd = bytes([0xF5, 0xDF, 0xFF, 0x00, 0x07] + id_bytes)
                self.real_port.write(cmd)
                self.real_port.flush()
                self.comm.log_signal.emit(f"Изпратено: {cmd.hex().upper()}")
                self.delay_precise_ms(10)

                self.real_port.write(b'\x50')
                self.comm.log_signal.emit("Изпратено: 50")
                self.delay_precise_ms(10)

                self.real_port.write(b'\x70')
                self.comm.log_signal.emit("Изпратено: 70")
                self.delay_precise_ms(30)

                available = self.real_port.in_waiting
                resp = self.real_port.read(available)
                self.comm.log_signal.emit(f"Получен статус: {resp.hex().upper()} (дължина {len(resp)})")

                try:
                    i = resp.index(b'\x50')
                    if len(resp) >= i + 4:
                        sdr1 = resp[i + 2]
                        sdr2 = resp[i + 3]
                        if sdr1 == 0x80 and sdr2 == 0x0C:
                            self.comm.log_signal.emit("✅ ID потвърден успешно (SDR10=1, SDR11=1)")
                            return True
                        else:
                            self.comm.log_signal.emit(f"❌ ID не е потвърден. Получено: {sdr1:02X} {sdr2:02X}, Очаквано: 80 0C")
                    else:
                        self.comm.log_signal.emit("❌ Статус отговорът не съдържа достатъчно байтове след 50")
                except ValueError:
                    self.comm.log_signal.emit("❌ Не е открита команда 50 в отговора")

                return False

            if check_id([0x00]*7) or check_id([0xFF]*7):
                self.comm.log_signal.emit("ID проверката премина успешно.")
            else:
                self.comm.log_signal.emit("❌ ID проверка неуспешна.")

        except Exception as e:
            self.comm.log_signal.emit(f"Грешка при бутване: {e}")

    def delay_precise_ms(self, ms):
        start = time.perf_counter()
        while (time.perf_counter() - start) < (ms / 1000.0):
            pass

    def log_to_console(self, text):
        self.console.append(text)

    def update_status(self, status):
        self.labelStatus.setText(f"Статус: {status}")

    def update_baudrate(self, baudrate):
        self.labelBaudrate.setText(f"Скорост: {baudrate} bps")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
