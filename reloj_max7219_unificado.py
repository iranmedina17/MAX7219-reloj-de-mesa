from machine import Pin, SPI, RTC
import time
import network
import ntptime
import max7219
import secrets

# =========================================================
# RELOJ + FECHA PARA MAX7219 (4 matrices 8x8 = 32x8)
# Basado en la lógica de hora.py y fecha.py, unificado.
#
# Muestra:
#   1) Hora grande durante 10 segundos
#   2) Fecha en scroll con formato largo del archivo fecha.py
#
# Hardware esperado:
#   SPI0 -> SCK=GP2, MOSI=GP3, CS=GP5
# =========================================================

# ---------------- CONFIG GENERAL ----------------
UTC_OFFSET = -5                 # Ecuador continental
NTP_RESYNC_HOURS = 6            # resincronizar cada 6 horas
SHOW_TIME_SECONDS = 10          # duración de pantalla de hora
DATE_SCROLL_SPEED = 0.05        # menor = más rápido
DISPLAY_BRIGHTNESS = 2          # 0..15
USE_24H_FORMAT = False          # False = 12h, True = 24h

# Ajustes finos de orientación.
# Si algo sale espejado o invertido, toca SOLO estas banderas.
BIG_DIGIT_ROTATE_180 = True     # en tu hora.py esto resolvía la orientación
SCROLL_FLIP_X = False           # invierte horizontalmente columnas del scroll
SCROLL_FLIP_Y = False           # invierte verticalmente bits del scroll
WEEKDAY_OFFSET = 0              # si el día sale corrido: prueba 1 o -1

# ---------------- HARDWARE / SPI ----------------
spi = SPI(
    0,
    baudrate=10000000,
    polarity=0,
    phase=0,
    sck=Pin(2),
    mosi=Pin(3)
)
cs = Pin(5, Pin.OUT)
display = max7219.Matrix8x8(spi, cs, 4)
display.brightness(DISPLAY_BRIGHTNESS)

# =========================================================
# FUENTE 5x7 PARA SCROLL Y MENSAJES
# Base tomada y preservada de fecha.py para mantener la misma idea.
# Cada número representa una columna.
# =========================================================
font = {
    ' ': [0, 0, 0, 0, 0],
    '!': [0, 125, 0, 0, 0],
    '-': [8, 8, 8, 8, 8],
    '/': [32, 16, 8, 4, 2],
    ':': [0, 54, 54, 0, 0],

    'A': [31, 36, 68, 36, 31],
    'B': [127, 73, 73, 73, 54],
    'C': [62, 65, 65, 65, 34],
    'D': [127, 65, 65, 34, 28],
    'E': [127, 73, 73, 65, 65],
    'F': [127, 72, 72, 72, 64],
    'G': [62, 65, 65, 69, 38],
    'H': [127, 8, 8, 8, 127],
    'I': [0, 65, 127, 65, 0],
    'J': [2, 1, 1, 1, 126],
    'K': [127, 8, 20, 34, 65],
    'L': [127, 1, 1, 1, 1],
    'M': [127, 32, 16, 32, 127],
    'N': [127, 32, 16, 8, 127],
    'O': [62, 65, 65, 65, 62],
    'P': [127, 72, 72, 72, 48],
    'Q': [62, 65, 69, 66, 61],
    'R': [127, 72, 76, 74, 49],
    'S': [50, 73, 73, 73, 38],
    'T': [64, 64, 127, 64, 64],
    'U': [126, 1, 1, 1, 126],
    'V': [124, 2, 1, 2, 124],
    'W': [126, 1, 6, 1, 126],
    'X': [99, 20, 8, 20, 99],
    'Y': [96, 16, 15, 16, 96],
    'Z': [67, 69, 73, 81, 97],

    '0': [62, 81, 73, 69, 62],
    '1': [0, 65, 127, 1, 0],
    '2': [35, 69, 73, 81, 33],
    '3': [66, 65, 81, 105, 70],
    '4': [24, 40, 72, 127, 8],
    '5': [114, 81, 81, 81, 78],
    '6': [30, 41, 73, 73, 6],
    '7': [64, 71, 72, 80, 96],
    '8': [54, 73, 73, 73, 54],
    '9': [48, 73, 73, 74, 60],
}

# =========================================================
# DÍGITOS GRANDES 8x8
# Base del archivo hora.py para ocupar casi todo cada panel 8x8.
# =========================================================
big_digits = {
    '0': [0b00111100, 0b01100110, 0b11000011, 0b11000011, 0b11000011, 0b11000011, 0b01100110, 0b00111100],
    '1': [0b00011000, 0b00111000, 0b01111000, 0b00011000, 0b00011000, 0b00011000, 0b00011000, 0b01111110],
    '2': [0b00111100, 0b01100110, 0b00000110, 0b00001100, 0b00011000, 0b00110000, 0b01100000, 0b01111110],
    '3': [0b00111100, 0b01100110, 0b00000110, 0b00011100, 0b00000110, 0b00000110, 0b01100110, 0b00111100],
    '4': [0b00001100, 0b00011100, 0b00101100, 0b01001100, 0b11111110, 0b00001100, 0b00001100, 0b00001100],
    '5': [0b01111110, 0b01100000, 0b01100000, 0b01111100, 0b00000110, 0b00000110, 0b01100110, 0b00111100],
    '6': [0b00111100, 0b01100110, 0b01100000, 0b01111100, 0b01100110, 0b01100110, 0b01100110, 0b00111100],
    '7': [0b01111110, 0b00000110, 0b00001100, 0b00011000, 0b00110000, 0b00110000, 0b00110000, 0b00110000],
    '8': [0b00111100, 0b01100110, 0b01100110, 0b00111100, 0b01100110, 0b01100110, 0b01100110, 0b00111100],
    '9': [0b00111100, 0b01100110, 0b01100110, 0b01100110, 0b00111110, 0b00000110, 0b01100110, 0b00111100],
    ' ': [0, 0, 0, 0, 0, 0, 0, 0],
}

# =========================================================
# NOMBRES DE DÍAS Y MESES
# =========================================================
days = {
    0: "LUNES",
    1: "MARTES",
    2: "MIERCOLES",
    3: "JUEVES",
    4: "VIERNES",
    5: "SABADO",
    6: "DOMINGO"
}

months = {
    1: "ENERO",
    2: "FEBRERO",
    3: "MARZO",
    4: "ABRIL",
    5: "MAYO",
    6: "JUNIO",
    7: "JULIO",
    8: "AGOSTO",
    9: "SEPTIEMBRE",
    10: "OCTUBRE",
    11: "NOVIEMBRE",
    12: "DICIEMBRE"
}

# =========================================================
# UTILIDADES GENERALES
# =========================================================
def clear():
    display.fill(0)
    display.show()


def reverse_byte(b):
    r = 0
    for i in range(8):
        if b & (1 << i):
            r |= (1 << (7 - i))
    return r


def text_width(text):
    if not text:
        return 0
    width = 0
    for i, ch in enumerate(text):
        width += len(font.get(ch.upper(), font[' ']))
        if i < len(text) - 1:
            width += 1
    return width


def draw_char(x0, char):
    pattern = font.get(char.upper(), font[' '])
    for x in range(len(pattern)):
        col = pattern[x]
        for y in range(7):
            if col & (1 << y):
                display.pixel(x0 + x, y, 1)


def draw_text(text, x_offset=0):
    display.fill(0)
    x = x_offset
    for ch in text:
        draw_char(x, ch)
        x += len(font.get(ch.upper(), font[' '])) + 1
    display.show()


def show_centered(text):
    text = text.upper()
    x = max((32 - text_width(text)) // 2, 0)
    draw_text(text, x)

# =========================================================
# ORIENTACIÓN - DÍGITOS GRANDES
# =========================================================
def transform_big_digit(pattern):
    if BIG_DIGIT_ROTATE_180:
        return pattern[::-1]
    return pattern


def draw_big_digit(panel_index, char):
    pattern = transform_big_digit(big_digits.get(char, big_digits[' ']))
    x_base = panel_index * 8

    for y in range(8):
        row = pattern[y]
        for x in range(8):
            bit = (row >> (7 - x)) & 1
            display.pixel(x_base + x, y, bit)


def show_big_4chars(text):
    text = (text + "    ")[:4]
    display.fill(0)
    for i in range(4):
        draw_big_digit(i, text[i])
    display.show()


def draw_center_colon(visible=True):
    # Dos puntos centrados entre HH y MM
    if not visible:
        return
    display.pixel(15, 2, 1)
    display.pixel(16, 2, 1)
    display.pixel(15, 5, 1)
    display.pixel(16, 5, 1)

# =========================================================
# ORIENTACIÓN - SCROLL DE FECHA
# =========================================================
def text_to_columns(text):
    columns = []
    for ch in text.upper():
        pattern = list(font.get(ch, font[' ']))

        if SCROLL_FLIP_X:
            pattern.reverse()
        if SCROLL_FLIP_Y:
            pattern = [reverse_byte(c) for c in pattern]

        columns.extend(pattern)
        columns.append(0)
    return columns


def draw_scrolling_columns(columns, speed=0.05):
    width = len(columns)
    for offset in range(width + 32):
        display.fill(0)
        for x in range(32):
            src_x = offset - 32 + x
            if 0 <= src_x < width:
                col = columns[src_x]
                for y in range(7):
                    if col & (1 << y):
                        display.pixel(x, y, 1)
        display.show()
        time.sleep(speed)

# =========================================================
# RTC / NTP / FECHA-HORA
# =========================================================
def is_leap(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def days_in_month(year, month):
    days_list = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month == 2 and is_leap(year):
        return 29
    return days_list[month - 1]


def apply_utc_offset(year, month, day, hour, minute, second, weekday, yearday, offset_hours):
    hour += offset_hours

    while hour < 0:
        hour += 24
        day -= 1
        weekday = (weekday - 1) % 7
        if day < 1:
            month -= 1
            if month < 1:
                month = 12
                year -= 1
            day = days_in_month(year, month)

    while hour >= 24:
        hour -= 24
        day += 1
        weekday = (weekday + 1) % 7
        if day > days_in_month(year, month):
            day = 1
            month += 1
            if month > 12:
                month = 1
                year += 1

    return year, month, day, hour, minute, second, weekday, yearday


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("WiFi ya conectado:", wlan.ifconfig())
        return wlan

    print("Conectando al WiFi...")
    wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASS)

    start = time.time()
    timeout = 15
    while not wlan.isconnected():
        if time.time() - start > timeout:
            raise RuntimeError("No se pudo conectar al WiFi")
        time.sleep(0.5)

    print("WiFi conectado:", wlan.ifconfig())
    return wlan


def sync_time():
    print("Sincronizando hora por NTP...")
    ntptime.host = "pool.ntp.org"
    ntptime.settime()  # RTC queda en UTC

    rtc = RTC()
    year, month, day, weekday, hour, minute, second, subseconds = rtc.datetime()

    year, month, day, hour, minute, second, weekday, _ = apply_utc_offset(
        year, month, day, hour, minute, second, weekday, 0, UTC_OFFSET
    )

    rtc.datetime((year, month, day, weekday, hour, minute, second, 0))
    print("Hora local ajustada:", rtc.datetime())


def get_time_digits_and_second():
    rtc = RTC()
    year, month, day, weekday, hour, minute, second, subseconds = rtc.datetime()

    if USE_24H_FORMAT:
        display_hour = hour
    else:
        if hour == 0:
            display_hour = 12
        elif hour > 12:
            display_hour = hour - 12
        else:
            display_hour = hour

    return "{:02d}{:02d}".format(display_hour, minute), second


def get_full_date_text():
    rtc = RTC()
    year, month, day, weekday, hour, minute, second, subseconds = rtc.datetime()

    weekday = (weekday + WEEKDAY_OFFSET) % 7
    day_name = days.get(weekday, "DIA")
    month_name = months.get(month, "MES")

    # Mantiene el estilo del archivo fecha.py
    return "{} - {} DE {}   ".format(day_name, day, month_name)

# =========================================================
# PANTALLAS PRINCIPALES
# =========================================================
def show_time_for_seconds(duration_seconds=10):
    start = time.time()
    last_second = -1

    while time.time() - start < duration_seconds:
        time_str, second = get_time_digits_and_second()

        if second != last_second:
            last_second = second
            colon_on = (second % 2 == 0)
            show_big_4chars(time_str)
            draw_center_colon(colon_on)
            display.show()

        time.sleep(0.05)


def show_date_once():
    text = get_full_date_text()
    cols = text_to_columns(text)
    draw_scrolling_columns(cols, speed=DATE_SCROLL_SPEED)

# =========================================================
# PRUEBAS
# =========================================================
def test_digits():
    while True:
        show_big_4chars("1234")
        draw_center_colon(True)
        time.sleep(2)
        show_big_4chars("5678")
        draw_center_colon(False)
        time.sleep(2)


def test_date():
    while True:
        show_date_once()

# =========================================================
# MAIN
# =========================================================
def main():
    clear()
    show_centered("WIFI")
    wlan = connect_wifi()

    show_centered("NTP")
    sync_time()
    last_sync = time.time()

    while True:
        try:
            if time.time() - last_sync > (NTP_RESYNC_HOURS * 3600):
                if not wlan.isconnected():
                    wlan = connect_wifi()
                sync_time()
                last_sync = time.time()

            show_time_for_seconds(SHOW_TIME_SECONDS)
            show_date_once()

        except Exception as e:
            print("Error:", e)
            show_centered("ERR")
            time.sleep(2)

            try:
                wlan = connect_wifi()
                sync_time()
                last_sync = time.time()
            except Exception as e2:
                print("Reconexión falló:", e2)
                time.sleep(5)


# Descomenta una prueba si quieres depurar algo puntual:
# test_digits()
# test_date()

main()
