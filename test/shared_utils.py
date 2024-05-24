"""
Shared utilities among tests
"""


from cocotb.triggers import ClockCycles, Timer
import random

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
        mosi_signal.value = cmd.get_bit_by_index(bit)

        # Wait 1 SPI clock
        await manual_clock(sck_signal, 1, 250)

    # Reset polarity of the clock
    sck_signal.value = 0
    # CS back uP
    cs_signal.value = 1
    # Reset MOSI and MISO to not screw up next transmission
    mosi_signal.value = 0
