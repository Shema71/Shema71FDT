import serial
import threading
import time

# Константи за конфигурация
BAUDRATE = 9600
TIMEOUT = 0.01  # Агресивно четене с малък timeout

class SerialBridge:
    def __init__(self, real_port, virt_port, comm):
        self.comm = comm
        self.real_port = real_port
        self.virt_port = virt_port
        self.running = True

        self.send_buffer = b''  # Съдържа последно изпратените байтове (за филтриране на ехо)

        self.comm.status_signal.emit("Свързан")
        self.comm.baudrate_signal.emit(str(BAUDRATE))
        self.comm.log_signal.emit("✅ Бриджът между портовете е стартиран")

        # Стартиране на нишки за двупосочна комуникация
        self.t1 = threading.Thread(target=self.forward_r_to_v, daemon=True)
        self.t2 = threading.Thread(target=self.forward_v_to_r, daemon=True)
        self.t1.start()
        self.t2.start()

    def forward_r_to_v(self):
        """Прехвърля данни от реален към виртуален порт, като премахва ехото."""
        while self.running:
            try:
                data = self.real_port.read(1)
                if data:
                    # Филтриране на ехо – ако получен байт съвпада с последно изпратен към реален порт
                    if self.send_buffer.startswith(data):
                        self.send_buffer = self.send_buffer[1:]  # Премахва съвпадението от буфера
                        continue  # Не го препращай – считаме го за ехо

                    # Валидни данни – препрати ги
                    self.virt_port.write(data)
                    self.virt_port.flush()
                    self.comm.log_signal.emit(f"[R→V] {data.hex(' ')}")
            except Exception as e:
                self.comm.log_signal.emit(f"❌ Грешка в R→V: {e}")
                break

    def forward_v_to_r(self):
        """Прехвърля данни от виртуален към реален порт и пази буфер за ехо-филтриране."""
        while self.running:
            try:
                data = self.virt_port.read(1)
                if data:
                    self.send_buffer += data  # Буферирай изпратения байт
                    self.real_port.write(data)
                    self.real_port.flush()
                    self.comm.log_signal.emit(f"[V→R] {data.hex(' ')}")
            except Exception as e:
                self.comm.log_signal.emit(f"❌ Грешка в V→R: {e}")
                break

    def stop(self):
        """Спира бриджа и затваря портовете безопасно."""
        self.running = False
        try:
            if self.real_port and self.real_port.is_open:
                self.real_port.close()
            if self.virt_port and self.virt_port.is_open:
                self.virt_port.close()
            self.comm.log_signal.emit("🛑 Бриджът е спрян и портовете са затворени.")
        except Exception as e:
            self.comm.log_signal.emit(f"❌ Грешка при затваряне: {e}")
