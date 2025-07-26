import cv2
import csv
import pytesseract
import os
import re
import time
import requests
from datetime import datetime
from conexion_mysql import conectar  # Asegúrate de tener este módulo

# =========================
# CONFIGURACIÓN PRINCIPAL
# =========================
CSV_FILE = os.path.join(os.getcwd(), "registro.csv")
HAAR_CASCADE_PATH = "haarcascades/haarcascade_russian_plate_number.xml"
ESP32_IP = "http://10.239.134.124"  # Sin slash final

# =========================
# CLASE PARA REGISTROS
# =========================
class RegistroPlacas:
    def __init__(self, archivo_csv):
        self.archivo_csv = archivo_csv
        self.registros = []
        self.cargar_registros()

    def cargar_registros(self):
        if not os.path.exists(self.archivo_csv):
            print(f"⚠️ CSV no encontrado: {self.archivo_csv}")
            return
        with open(self.archivo_csv, 'r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            next(reader, None)  # Saltar encabezado
            for row in reader:
                if len(row) >= 5:
                    _, placa, evento, _, propietario = row
                    self.registros.append((placa.strip().upper(), evento.lower(), propietario))

    def agregar_registro(self, placa, evento, propietario):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        id_ = self.obtener_ultimo_id() + 1

        try:
            with open(self.archivo_csv, 'a', newline='', encoding='utf-8-sig') as file:
                csv.writer(file).writerow([id_, placa, evento, timestamp, propietario])
            print(f"✅ CSV guardado: {placa} - {evento}")
        except Exception as e:
            print(f"❌ Error guardando en CSV: {e}")

        self.registros.append((placa, evento, propietario))

        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO registros (placa, evento, fecha_hora, propietario)
                VALUES (%s, %s, %s, %s)
            """, (placa, evento, timestamp, propietario))
            conn.commit()
            cursor.close(); conn.close()
            print("🗃️ Registro guardado en MySQL.")
        except Exception as err:
            print(f"❌ Error MySQL: {err}")

    def obtener_ultimo_id(self):
        try:
            with open(self.archivo_csv, 'r', encoding='utf-8-sig') as f:
                return max([int(line.split(',')[0]) for line in f.readlines()[1:]])
        except:
            return 0

    def buscar_placa(self, placa):
        for registro in reversed(self.registros):
            if registro[0] == placa:
                return registro
        return None

# =========================
# FUNCIONES AUXILIARES
# =========================
def limpiar_texto(texto):
    return re.sub(r'[^A-Z0-9]', '', texto.upper())

def levantar_barrera(evento):
    ruta = "entrada" if evento == "entrada" else "salida"
    try:
        url = f"{ESP32_IP}/{ruta}"
        print(f"🔗 Enviando solicitud a: {url}")
        r = requests.get(url, timeout=5)
        print(f"📥 Respuesta ESP32: {r.status_code} - {r.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al conectar con ESP32: {e}")

# =========================
# PROCESO PRINCIPAL
# =========================
def main():
    detector = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
    cam = cv2.VideoCapture(2)

    if not cam.isOpened():
        print("❌ No se puede acceder a la cámara.")
        return

    registro = RegistroPlacas(CSV_FILE)
    print("📸 Sistema de reconocimiento activo. Presiona 'q' para salir.")

    while True:
        ret, frame = cam.read()
        if not ret:
            print("⚠️ No se pudo leer la imagen de la cámara.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        placas = detector.detectMultiScale(gray, 1.1, 5)

        for (x, y, w, h) in placas:
            roi = gray[y:y+h, x:x+w]
            roi = cv2.resize(roi, None, fx=2, fy=2)
            roi = cv2.bilateralFilter(roi, 11, 17, 17)
            _, roi = cv2.threshold(roi, 150, 255, cv2.THRESH_BINARY)

            texto = pytesseract.image_to_string(roi, config='--psm 8')
            texto_limpio = limpiar_texto(texto)

            print(f"🔍 OCR detectado: '{texto.strip()}' → Limpio: '{texto_limpio}'")

            if len(texto_limpio) >= 5:
                r = registro.buscar_placa(texto_limpio)
                if r:
                    nuevo_evento = "salida" if r[1] == "entrada" else "entrada"
                    registro.agregar_registro(texto_limpio, nuevo_evento, r[2])
                    levantar_barrera(nuevo_evento)
                    print("⏳ Esperando 5 segundos para evitar duplicados...")
                    time.sleep(5)  # 🕒 Espera 10 segundos antes de seguir escaneando
                else:
                    print(f"⛔ Placa no registrada: {texto_limpio}")

        cv2.imshow("Lector de Placas", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("🛑 Saliendo del sistema...")
            break

    cam.release()
    cv2.destroyAllWindows()

# =========================
# EJECUCIÓN DEL SCRIPT
# =========================
if __name__ == "__main__":
    main()
