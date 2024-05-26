"""
Shared utilities among tests
"""


from cocotb.triggers import ClockCycles, Timer
import random
import numpy as np

SPI_CMD_TOTAL_BITS = 56

# Valid SPI commands
SPI_CMD_DEV_ID = 0
SPI_CMD_WRITE_POLY_A = 0x80
SPI_CMD_CLEAR_POLY_A = 0x40
SPI_CMD_WRITE_POLY_B = 0x81
SPI_CMD_CLEAR_POLY_B = 0x41
SPI_CMD_ENABLE_SCREEN = 0x21
SPI_CMD_DISABLE_SCREEN = 0x20
SPI_CMD_SET_BG_COLOR = 0x01

# Colors mapping
COLOR_BLACK = 0 # 000000
COLOR_RED = 48 # 110000
COLOR_GREEN = 12 # 001100
COLOR_BLUE = 3 # 000011


class Polygon:
    """
    Structure to hold polygon params
    """
    def __init__(self, v0: np.ndarray, v1: np.ndarray, v2: np.ndarray, depth: int, color: int):
        self.v0 = v0
        self.v1 = v1
        self.v2 = v2
        self.raw_color = color
        self.depth = depth

        # Save as array for gt
        self.color = upscale_color(color)


class SPIcmd:
    """
    Generic SPI cmd

    Yes, this could be done with ctypes, my current python version has a known issue with packing odd sized bitfields fixed in python 3.11
    """
    def __init__(self, cmd: int,
                        color: int,
                        v0_x: int,
                        v1_x: int,
                        v2_x: int,
                        v0_y: int,
                        v1_y: int,
                        v2_y: int,
                        depth: int):

        self.color = color
        self.v0_x = v0_x
        self.v1_x = v1_x
        self.v2_x = v2_x
        self.v0_y = v0_y
        self.v1_y = v1_y
        self.v2_y = v2_y
        self.depth = depth
        self.cmd_str = (cmd) | (color << 8) | (v0_x << 14) | (v1_x << 21) | (v2_x << 28) | (v0_y << 35) | (v1_y << 41) | (v2_y << 47) | (depth << 53)

    def as_bytes(self) -> bytes:
        """
        Encode the CMD as a 7 byte packed buffer
        """
        return self.cmd_str.to_bytes(length=7, byteorder='little')

    def get_bit_by_index(self, index: int) -> int:
        """
        Get individual bit at index in CMD buffer
        """
        return (self.cmd_str & (1 << index)) >> index

    @classmethod
    def generate_random(cls, cmd: int):
        """
        Generate random polygon parameters for better fuzzing
        """
        if cmd == SPI_CMD_WRITE_POLY_A or cmd == SPI_CMD_WRITE_POLY_B:
            color = random.randrange(start=0, stop=64, step=1)
            v0_x = random.randrange(start=0, stop=128, step=1)
            v1_x = random.randrange(start=0, stop=128, step=1)
            v2_x = random.randrange(start=0, stop=128, step=1)
            v0_y = random.randrange(start=0, stop=64, step=1)
            v1_y = random.randrange(start=0, stop=64, step=1)
            v2_y = random.randrange(start=0, stop=64, step=1)
            depth = random.randrange(start=0, stop=8, step=1)
            return cls(cmd, color, v0_x, v1_x, v2_x, v0_y, v1_y, v2_y, depth)
        else:
            return cls(cmd, 0, 0, 0, 0, 0, 0, 0, 0)

    @classmethod
    def from_poly(cls, poly: Polygon, cmd: int):
        """
        Create SPI CMD from a polygon struct
        """
        return cls(cmd, poly.raw_color, int(poly.v0[0]/10), int(poly.v1[0]/10), int(poly.v2[0]/10), int(poly.v0[1]/10),
                                                                    int(poly.v1[1]/10), int(poly.v2[1]/10), poly.depth)


async def manual_clock(in_sig, cycles: int, period_ns: int):
    """
    Manually throw the clock since the coroutine caused issues with the precise requirements for the SPI input waveform
    """
    for _ in range(cycles):

        # Start with falling edge of clock
        in_sig.value = 0

        await Timer(period_ns/2, units='ns')

        in_sig.value = 1

        await Timer(period_ns/2, units='ns')


async def send_spi_cmd(cs_signal, sck_signal, mosi_signal, cmd: SPIcmd):
    """
    Send a fully formed SPI command

    Note only Mode 0 SPI is supported here
    """

    # CS down
    cs_signal.value = 0

    for bit in range(SPI_CMD_TOTAL_BITS):

        # Real micro typically has a several SCK delay in between sending each byte
        # We simulate this by adding a ~2 SCK delay every byte
        if bit % 8 == 0:

            # Reset polarity of the clock
            sck_signal.value = 0

            # Reset MOSI and MISO to not screw up next transmission
            mosi_signal.value = 0

            # Wait delay time
            await Timer(500, units='ns')


        # Set MOSI
        mosi_signal.value = int(cmd.get_bit_by_index(bit))

        # Wait 1 SPI clock
        await manual_clock(sck_signal, 1, 250)

    # Reset polarity of the clock
    sck_signal.value = 0
    # CS back uP
    cs_signal.value = 1
    # Reset MOSI and MISO to not screw up next transmission
    mosi_signal.value = 0


def upscale_color(color : int) -> np.ndarray:
    """
    Upscale color into RGB channels from 6 bit integer form to 8 bit RGB
    """

    # Split out RGB components seperately and apply scaling factor to each color
    r_comp = ((color & COLOR_RED) >> 4) * 64
    g_comp = ((color & COLOR_GREEN) >> 2) * 64
    b_comp = (color & COLOR_BLUE) * 64

    return np.array([r_comp, g_comp, b_comp])


def upscale_color_from_components(c_red: int, c_green: int, c_blue: int) -> np.ndarray:
    """
    Upscale color into RGB channels from 3x2 bit integer form to 8 bit RGB
    """

    # Split out RGB components seperately and apply scaling factor to each color
    r_comp = c_red * 64
    g_comp = c_green * 64
    b_comp = c_blue * 64

    return np.array([r_comp, g_comp, b_comp])


def should_pixel_be_rasterized(v0, v1, v2, p_x, p_y, log=False):
    """
    Manual check of rasterization algorithm
    """
    p0 = (v1[0] - v0[0]) * (p_y - v0[1]) - (v1[1] - v0[1]) * (p_x - v0[0])
    p1 = (v2[0] - v1[0]) * (p_y - v1[1]) - (v2[1] - v1[1]) * (p_x - v1[0])
    p2 = (v0[0] - v2[0]) * (p_y - v2[1]) - (v0[1] - v2[1]) * (p_x - v2[0])

    if log == True:
        print((v1[0] - v0[0]) * (p_y - v0[1]))
        print((v1[1] - v0[1]) * (p_x - v0[0]))
        print((v2[0] - v1[0]) * (p_y - v1[1]))
        print((v2[1] - v1[1]) * (p_x - v1[0]))
        print((v0[0] - v2[0]) * (p_y - v2[1]))
        print((v0[1] - v2[1]) * (p_x - v2[0]))

    if (p0 >= 0) and (p1 >= 0) and (p2 >= 0):
        return 1
    else:
        return 0
