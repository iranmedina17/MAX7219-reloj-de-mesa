from machine import Pin, SPI
import time
import urandom
import max7219

# =========================================================
# DEMO PIXEL ART PARA MAX7219 (4 matrices 8x8 = 32x8)
#
# Copia este archivo a la Pico W como main.py si quieres que
# arranque directo, o ejecútalo manualmente como pixel_art_demo.py.
#
# Hardware esperado:
#   SPI0 -> SCK=GP2, MOSI=GP3, CS=GP5
# =========================================================

DISPLAY_BRIGHTNESS = 7
ROTATE_180 = True

spi = SPI(
    0,
    baudrate=10000000,
    polarity=0,
    phase=0,
    sck=Pin(2),
    mosi=Pin(3),
)
cs = Pin(5, Pin.OUT)
display = max7219.Matrix8x8(spi, cs, 4)
display.brightness(DISPLAY_BRIGHTNESS)


def clear():
    display.fill(0)
    display.show()


def pixel(x, y, value):
    if ROTATE_180:
        x = 31 - x
        y = 7 - y
    display.pixel(x, y, value)


def plot_bitmap(x0, rows):
    for y, row in enumerate(rows):
        for x in range(8):
            pixel(x0 + x, y, (row >> (7 - x)) & 1)


def frame_pause(delay):
    display.show()
    time.sleep(delay)


def rain(seconds=8):
    drops = []
    start = time.time()
    while time.time() - start < seconds:
        display.fill(0)

        if len(drops) < 18 and urandom.getrandbits(3) > 1:
            drops.append([urandom.getrandbits(5) % 32, -1])

        alive = []
        for drop in drops:
            x, y = drop
            if 0 <= y < 8:
                pixel(x, y, 1)
            if 0 <= y - 1 < 8:
                pixel(x, y - 1, 1)
            drop[1] += 1
            if drop[1] < 10:
                alive.append(drop)
        drops = alive

        frame_pause(0.07)


def fire(seconds=8):
    heat = [0] * 32
    start = time.time()
    while time.time() - start < seconds:
        display.fill(0)

        for x in range(32):
            spark = urandom.getrandbits(4)
            heat[x] = max(1, min(8, (heat[x] + spark) // 2 + 2))
            if urandom.getrandbits(4) == 0:
                heat[x] = urandom.getrandbits(3) + 1

        for x, height in enumerate(heat):
            wobble = urandom.getrandbits(2)
            top = max(0, 8 - height + wobble)
            for y in range(top, 8):
                if urandom.getrandbits(3) != 0:
                    pixel(x, y, 1)

        frame_pause(0.08)


def waves(seconds=8):
    step = 0
    start = time.time()
    wave = [3, 2, 1, 1, 2, 3, 4, 5, 6, 6, 5, 4]
    while time.time() - start < seconds:
        display.fill(0)
        for x in range(32):
            y = wave[(x + step) % len(wave)]
            pixel(x, y, 1)
            if y + 1 < 8:
                pixel(x, y + 1, 1)
        step = (step + 1) % len(wave)
        frame_pause(0.08)


def audio_bars(seconds=8):
    levels = [1] * 16
    start = time.time()
    while time.time() - start < seconds:
        display.fill(0)
        for i in range(16):
            target = (urandom.getrandbits(3) % 8) + 1
            if levels[i] < target:
                levels[i] += 1
            elif levels[i] > target:
                levels[i] -= 1

            x0 = i * 2
            for y in range(8 - levels[i], 8):
                pixel(x0, y, 1)
                pixel(x0 + 1, y, 1)

        frame_pause(0.09)


def scroll_sprite(rows, seconds=5, delay=0.05):
    start = time.time()
    offset = 32
    while time.time() - start < seconds:
        display.fill(0)
        plot_bitmap(offset, rows)
        offset -= 1
        if offset < -8:
            offset = 32
        frame_pause(delay)


def faces_and_hearts(seconds=10):
    smile = [
        0b00111100,
        0b01000010,
        0b10100101,
        0b10000001,
        0b10100101,
        0b10011001,
        0b01000010,
        0b00111100,
    ]
    heart = [
        0b00000000,
        0b01100110,
        0b11111111,
        0b11111111,
        0b11111111,
        0b01111110,
        0b00111100,
        0b00011000,
    ]
    wink = [
        0b00111100,
        0b01000010,
        0b10100001,
        0b10000001,
        0b10100101,
        0b10011001,
        0b01000010,
        0b00111100,
    ]

    sprites = [smile, heart, wink, heart]
    start = time.time()
    index = 0
    while time.time() - start < seconds:
        display.fill(0)
        plot_bitmap(4, sprites[index % len(sprites)])
        plot_bitmap(20, sprites[(index + 1) % len(sprites)])
        frame_pause(0.6)
        index += 1


def sparkle(seconds=8):
    points = []
    start = time.time()
    while time.time() - start < seconds:
        display.fill(0)
        if len(points) < 20:
            points.append([urandom.getrandbits(5) % 32, urandom.getrandbits(3), 3])

        alive = []
        for p in points:
            x, y, life = p
            pixel(x, y, 1)
            if life > 1:
                if x > 0:
                    pixel(x - 1, y, 1)
                if x < 31:
                    pixel(x + 1, y, 1)
            p[2] -= 1
            if p[2] > 0:
                alive.append(p)
        points = alive
        frame_pause(0.12)


def main():
    clear()
    while True:
        rain()
        fire()
        waves()
        audio_bars()
        faces_and_hearts()
        sparkle()


main()
