from micropython import const

_DIGIT0 = const(0x1)
_DECODEMODE = const(0x9)
_INTENSITY = const(0xA)
_SCANLIMIT = const(0xB)
_SHUTDOWN = const(0xC)
_DISPLAYTEST = const(0xF)

class Matrix8x8:
    def __init__(self, spi, cs, num):
        self.spi = spi
        self.cs = cs
        self.cs.init(self.cs.OUT, True)
        self.num = num
        self.buffer = bytearray(8 * num)
        self.init_display()

    def _write(self, command, data):
        self.cs(0)
        for _ in range(self.num):
            self.spi.write(bytearray([command, data]))
        self.cs(1)

    def init_display(self):
        for cmd, data in (
            (_SHUTDOWN, 0),
            (_DISPLAYTEST, 0),
            (_SCANLIMIT, 7),
            (_DECODEMODE, 0),
            (_SHUTDOWN, 1),
        ):
            self._write(cmd, data)
        self.brightness(5)
        self.fill(0)
        self.show()

    def brightness(self, value):
        if 0 <= value <= 15:
            self._write(_INTENSITY, value)

    def fill(self, c):
        for i in range(len(self.buffer)):
            self.buffer[i] = 0xFF if c else 0x00

    def pixel(self, x, y, c):
        if 0 <= x < self.num * 8 and 0 <= y < 8:
            idx = x // 8
            shift = x % 8
            if c:
                self.buffer[idx * 8 + y] |= (1 << shift)
            else:
                self.buffer[idx * 8 + y] &= ~(1 << shift)

    def show(self):
        for y in range(8):
            self.cs(0)
            for m in range(self.num):
                self.spi.write(bytearray([y + 1, self.buffer[(self.num - m - 1) * 8 + y]]))
            self.cs(1)
