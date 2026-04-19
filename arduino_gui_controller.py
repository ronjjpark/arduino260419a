import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - shown to the user at runtime
    serial = None
    list_ports = None


BAUD_RATES = ["9600", "19200", "38400", "57600", "115200"]
DEFAULT_BAUD = "9600"


class ArduinoGuiController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Arduino Controller")
        self.geometry("780x560")
        self.minsize(720, 520)

        self.serial_conn = None
        self.reader_thread = None
        self.stop_reader = threading.Event()
        self.incoming = queue.Queue()

        self.port_var = tk.StringVar()
        self.baud_var = tk.StringVar(value=DEFAULT_BAUD)
        self.status_var = tk.StringVar(value="Disconnected")
        self.command_var = tk.StringVar()
        self.led_pin_var = tk.StringVar(value="13")
        self.pwm_pin_var = tk.StringVar(value="9")
        self.servo_pin_var = tk.StringVar(value="10")
        self.pwm_value_var = tk.IntVar(value=0)
        self.servo_angle_var = tk.IntVar(value=90)

        self._build_ui()
        self.refresh_ports()
        self.after(80, self._drain_incoming)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        root = ttk.Frame(self, padding=16)
        root.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(2, weight=1)

        connection = ttk.LabelFrame(root, text="Connection", padding=12)
        connection.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        connection.columnconfigure(1, weight=1)

        ttk.Label(connection, text="Port").grid(row=0, column=0, sticky="w")
        self.port_combo = ttk.Combobox(connection, textvariable=self.port_var, state="readonly", width=24)
        self.port_combo.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(connection, text="Refresh", command=self.refresh_ports).grid(row=0, column=2, padx=(0, 8))

        ttk.Label(connection, text="Baud").grid(row=0, column=3, sticky="w")
        ttk.Combobox(
            connection,
            textvariable=self.baud_var,
            values=BAUD_RATES,
            state="readonly",
            width=10,
        ).grid(row=0, column=4, sticky="w", padx=(8, 8))

        self.connect_button = ttk.Button(connection, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=5)

        ttk.Label(connection, textvariable=self.status_var).grid(
            row=1, column=0, columnspan=6, sticky="w", pady=(10, 0)
        )

        digital = ttk.LabelFrame(root, text="Digital Output", padding=12)
        digital.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        digital.columnconfigure(1, weight=1)

        ttk.Label(digital, text="LED Pin").grid(row=0, column=0, sticky="w")
        ttk.Entry(digital, textvariable=self.led_pin_var, width=8).grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Button(digital, text="ON", command=lambda: self.send_digital(1)).grid(row=1, column=0, sticky="ew", pady=(12, 0))
        ttk.Button(digital, text="OFF", command=lambda: self.send_digital(0)).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(12, 0))

        analog = ttk.LabelFrame(root, text="PWM / Servo", padding=12)
        analog.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        analog.columnconfigure(1, weight=1)

        ttk.Label(analog, text="PWM Pin").grid(row=0, column=0, sticky="w")
        ttk.Entry(analog, textvariable=self.pwm_pin_var, width=8).grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Label(analog, text="Brightness").grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Scale(
            analog,
            from_=0,
            to=255,
            variable=self.pwm_value_var,
            command=lambda _value: self.pwm_value_label.config(text=str(self.pwm_value_var.get())),
        ).grid(row=1, column=1, sticky="ew", padx=(8, 8), pady=(12, 0))
        self.pwm_value_label = ttk.Label(analog, text="0", width=4)
        self.pwm_value_label.grid(row=1, column=2, sticky="e", pady=(12, 0))
        ttk.Button(analog, text="Send PWM", command=self.send_pwm).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 0))

        ttk.Label(analog, text="Servo Pin").grid(row=3, column=0, sticky="w", pady=(18, 0))
        ttk.Entry(analog, textvariable=self.servo_pin_var, width=8).grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(18, 0))
        ttk.Label(analog, text="Angle").grid(row=4, column=0, sticky="w", pady=(12, 0))
        ttk.Scale(
            analog,
            from_=0,
            to=180,
            variable=self.servo_angle_var,
            command=lambda _value: self.servo_angle_label.config(text=str(self.servo_angle_var.get())),
        ).grid(row=4, column=1, sticky="ew", padx=(8, 8), pady=(12, 0))
        self.servo_angle_label = ttk.Label(analog, text="90", width=4)
        self.servo_angle_label.grid(row=4, column=2, sticky="e", pady=(12, 0))
        ttk.Button(analog, text="Send Servo", command=self.send_servo).grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 0))

        log_frame = ttk.LabelFrame(root, text="Serial Monitor", padding=12)
        log_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=12, wrap="word", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        command_bar = ttk.Frame(log_frame)
        command_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        command_bar.columnconfigure(0, weight=1)
        ttk.Entry(command_bar, textvariable=self.command_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(command_bar, text="Send Command", command=self.send_custom_command).grid(row=0, column=1, padx=(8, 0))

    def refresh_ports(self):
        if list_ports is None:
            self.status_var.set("pyserial is not installed. Run: pip install -r requirements.txt")
            self.port_combo["values"] = []
            return

        ports = [port.device for port in list_ports.comports()]
        self.port_combo["values"] = ports
        if ports and self.port_var.get() not in ports:
            self.port_var.set(ports[0])
        elif not ports:
            self.port_var.set("")
            self.status_var.set("No serial ports found")

    def toggle_connection(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        if serial is None:
            messagebox.showerror("Missing package", "pyserial is required. Run: pip install -r requirements.txt")
            return

        port = self.port_var.get().strip()
        if not port:
            messagebox.showwarning("No port", "Select an Arduino serial port first.")
            return

        try:
            baud = int(self.baud_var.get())
            self.serial_conn = serial.Serial(port=port, baudrate=baud, timeout=0.2)
            time.sleep(2.0)
        except serial.SerialException as exc:
            messagebox.showerror("Connection failed", str(exc))
            self.serial_conn = None
            return

        self.stop_reader.clear()
        self.reader_thread = threading.Thread(target=self._read_serial_loop, daemon=True)
        self.reader_thread.start()
        self.connect_button.configure(text="Disconnect")
        self.status_var.set(f"Connected to {port} at {baud} baud")
        self._append_log(f"[SYSTEM] Connected to {port}")

    def disconnect(self):
        self.stop_reader.set()
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)

        if self.serial_conn:
            try:
                self.serial_conn.close()
            except serial.SerialException:
                pass

        self.serial_conn = None
        self.connect_button.configure(text="Connect")
        self.status_var.set("Disconnected")
        self._append_log("[SYSTEM] Disconnected")

    def _read_serial_loop(self):
        while not self.stop_reader.is_set():
            try:
                if self.serial_conn and self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode("utf-8", errors="replace").strip()
                    if line:
                        self.incoming.put(line)
                else:
                    time.sleep(0.05)
            except serial.SerialException as exc:
                self.incoming.put(f"[ERROR] {exc}")
                self.stop_reader.set()

    def _drain_incoming(self):
        while True:
            try:
                line = self.incoming.get_nowait()
            except queue.Empty:
                break
            self._append_log(f"< {line}")
        self.after(80, self._drain_incoming)

    def _append_log(self, line):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _write_line(self, command):
        if not self.serial_conn or not self.serial_conn.is_open:
            messagebox.showwarning("Not connected", "Connect to Arduino first.")
            return

        try:
            self.serial_conn.write((command + "\n").encode("utf-8"))
            self._append_log(f"> {command}")
        except serial.SerialException as exc:
            messagebox.showerror("Send failed", str(exc))
            self.disconnect()

    def _read_pin(self, value):
        try:
            pin = int(value.get())
        except ValueError:
            raise ValueError("Pin number must be an integer.")
        if pin < 0:
            raise ValueError("Pin number must be zero or greater.")
        return pin

    def send_digital(self, value):
        try:
            pin = self._read_pin(self.led_pin_var)
        except ValueError as exc:
            messagebox.showwarning("Invalid pin", str(exc))
            return
        self._write_line(f"D {pin} {value}")

    def send_pwm(self):
        try:
            pin = self._read_pin(self.pwm_pin_var)
        except ValueError as exc:
            messagebox.showwarning("Invalid pin", str(exc))
            return
        self._write_line(f"P {pin} {self.pwm_value_var.get()}")

    def send_servo(self):
        try:
            pin = self._read_pin(self.servo_pin_var)
        except ValueError as exc:
            messagebox.showwarning("Invalid pin", str(exc))
            return
        self._write_line(f"S {pin} {self.servo_angle_var.get()}")

    def send_custom_command(self):
        command = self.command_var.get().strip()
        if not command:
            return
        self._write_line(command)
        self.command_var.set("")

    def on_close(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.disconnect()
        self.destroy()


if __name__ == "__main__":
    app = ArduinoGuiController()
    app.mainloop()
