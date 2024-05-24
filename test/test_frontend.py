"""
Test GPU frontend module
"""

# SPDX-FileCopyrightText: Emery Nagy
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.clock import Clock
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

        # Start with rising edge of clock
        in_sig.value = 1

        await Timer(period_ns/2, units='ns')

        in_sig.value = 0

        await Timer(period_ns/2, units='ns')



async def send_spi_cmd(dut, cmd: SPIcmd):
    """
    Send a fully formed SPI command

    Note only Mode 0 SPI is supported here
    """

    # CS down
    dut.cs_in.value = 0

    for bit in range(SPI_CMD_TOTAL_BITS):

        # Real micro typically has a several SCK delay in between sending each byte
        # We simulate this by adding a ~2 SCK delay every byte
        if bit % 8 == 0:

            # Reset polarity of the clock
            dut.sck_in.value = 0

            # Reset MOSI and MISO to not screw up next transmission
            dut.mosi_in.value = 0
            dut.miso_in.value = 0

            # Wait delay time
            await Timer(500, units='ns')


        # Set MOSI
        dut.mosi_in.value = cmd.get_bit_by_index(bit)

        # Let signal settle first, clock method starts immediately with the posedge in simulation
        await Timer(50, units='ns')

        # Wait 1 SPI clock
        await manual_clock(dut.sck_in, 1, 250)



    # Reset polarity of the clock
    dut.sck_in.value = 0
    # CS back uP
    dut.cs_in.value = 1
    # Reset MOSI and MISO to not screw up next transmission
    dut.mosi_in.value = 0
    dut.miso_in.value = 0


async def reset_dut(dut):
    """
    Reset DUT automatically

    Also zero out all inputs - should be called before every test
    """
    dut._log.info("Reset")

    dut.rst_n.value = 0
    dut.cs_in.value = 1
    dut.mosi_in.value = 0
    dut.miso_in.value = 0
    dut.sck_in.value = 0
    dut.en_load.value = 0

    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    await ClockCycles(dut.clk, 1)


def check_poly_a(dut, color: int, v0_x: int, v1_x: int, v2_x: int, v0_y: int, v1_y: int, v2_y: int, depth: int, enable: int):
    """
    Check polygon A stored output
    """
    assert (dut.poly_enable_out.value.integer & 1) == enable
    assert (dut.poly_color_out.value.integer & 63) == color
    assert (dut.v0_x_out.value.integer & 127) == v0_x
    assert (dut.v1_x_out.value.integer & 127) == v1_x
    assert (dut.v2_x_out.value.integer & 127) == v2_x
    assert (dut.v0_y_out.value.integer & 63) == v0_y
    assert (dut.v1_y_out.value.integer & 63) == v1_y
    assert (dut.v2_y_out.value.integer & 63) == v2_y
    assert (dut.poly_depth_out.value.integer & 7) == depth


def check_poly_b(dut, color: int, v0_x: int, v1_x: int, v2_x: int, v0_y: int, v1_y: int, v2_y: int, depth: int, enable: int):
    """
    Check polygon B stored output
    """
    assert (dut.poly_enable_out.value.integer & 2) >> 1 == enable
    assert (dut.poly_color_out.value.integer & (63 << 6)) >> 6 == color
    assert (dut.v0_x_out.value.integer & (127 << 7)) >> 7 == v0_x
    assert (dut.v1_x_out.value.integer & (127 << 7)) >> 7 == v1_x
    assert (dut.v2_x_out.value.integer & (127 << 7)) >> 7== v2_x
    assert (dut.v0_y_out.value.integer & (63 << 6)) >> 6 == v0_y
    assert (dut.v1_y_out.value.integer & (63 << 6)) >> 6 == v1_y
    assert (dut.v2_y_out.value.integer & (63 << 6)) >> 6 == v2_y
    assert (dut.poly_depth_out.value.integer & (7 << 3)) >> 3 == depth


@cocotb.test()
async def test_reset(dut):
    """
    Test internal state reset
    """
    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # All outputs should be zeroed
    assert dut.bg_color_out.value == 0
    assert dut.poly_color_out.value == 0
    assert dut.v0_x_out.value == 0
    assert dut.v0_y_out.value == 0
    assert dut.v1_x_out.value == 0
    assert dut.v1_y_out.value == 0
    assert dut.v2_x_out.value == 0
    assert dut.v2_y_out.value == 0
    assert dut.poly_depth_out.value == 0
    assert dut.en_screen_out.value == 0
    assert dut.poly_enable_out.value == 0

    dut._log.info("Finished")



@cocotb.test()
async def test_send_write_poly_a_cmd(dut):
    """
    Test writing polygon A parameters
    """

    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset - Since the screen has been fully disabled, we should be able to write commands
    await reset_dut(dut)

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon A
    new_cmd = SPIcmd(cmd=SPI_CMD_WRITE_POLY_A, color=COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6, depth=7)

    # Send command
    await send_spi_cmd(dut,  cmd=new_cmd)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    # Polygon A should have correct changes and polygon B should remain unchanged
    check_poly_a(dut, color=COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6, depth=7, enable=1)
    check_poly_b(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)



@cocotb.test()
async def test_send_write_poly_b_cmd(dut):
    """
    Test writing polygon B parameters
    """

    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset - Since the screen has been fully disabled, we should be able to write commands
    await reset_dut(dut)

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon B
    new_cmd = SPIcmd(cmd=SPI_CMD_WRITE_POLY_B, color=COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6, depth=7)

    # Send command
    await send_spi_cmd(dut,  cmd=new_cmd)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    # Only polygon B should update
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)
    check_poly_b(dut, color=COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6, depth=7, enable=1)



@cocotb.test()
async def test_send_write_poly_a_then_b(dut):
    """
    Test writing polygon A then B parameters
    """

    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset - Since the screen has been fully disabled, we should be able to write commands
    await reset_dut(dut)

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon A
    cmd_a = SPIcmd(cmd=SPI_CMD_WRITE_POLY_A, color=COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6, depth=7)

    # Send command
    await send_spi_cmd(dut,  cmd=cmd_a)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    # Polygon A should have correct changes and polygon B should remain unchanged
    check_poly_a(dut, color=COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6, depth=7, enable=1)
    check_poly_b(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 5)

    # Arbitrary cmd to ploygon B
    cmd_b = SPIcmd(cmd=SPI_CMD_WRITE_POLY_B, color=COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17, depth=2)

    # Send command
    await send_spi_cmd(dut,  cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 5)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    # Both Polys should have the correct data
    check_poly_a(dut, color=COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6, depth=7, enable=1)
    check_poly_b(dut, color=COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17, depth=2, enable=1)



@cocotb.test()
async def test_send_write_poly_b_then_a(dut):
    """
    Test writing polygon B then A parameters
    """

    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset - Since the screen has been fully disabled, we should be able to write commands
    await reset_dut(dut)

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon B
    cmd_b = SPIcmd(cmd=SPI_CMD_WRITE_POLY_B, color=COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17, depth=2)

    # Send command
    await send_spi_cmd(dut, cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 5)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    # Both Polys should have the correct data
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)
    check_poly_b(dut, color=COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17, depth=2, enable=1)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 5)

    # Arbitrary cmd to ploygon A
    cmd_a = SPIcmd(cmd=SPI_CMD_WRITE_POLY_A, color=COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6, depth=7)

    # Send command
    await send_spi_cmd(dut, cmd=cmd_a)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    check_poly_a(dut, color=COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6, depth=7, enable=1)
    check_poly_b(dut, color=COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17, depth=2, enable=1)



@cocotb.test()
async def test_send_delete_poly_a(dut):
    """
    Test deleting poly A params
    """

    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset - Since the screen has been fully disabled, we should be able to write commands
    await reset_dut(dut)

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon B
    cmd_b = SPIcmd.generate_random(SPI_CMD_WRITE_POLY_B)

    # Send command
    await send_spi_cmd(dut, cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 5)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    # Both Polys should have the correct data
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y, depth=cmd_b.depth, enable=1)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 5)

    # Arbitrary cmd to ploygon A
    cmd_a = SPIcmd.generate_random(SPI_CMD_WRITE_POLY_A)

    # Send command
    await send_spi_cmd(dut, cmd=cmd_a)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y, depth=cmd_a.depth, enable=1)
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y, depth=cmd_b.depth, enable=1)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 6)

    # Remove poly A only
    cmd_delete = SPIcmd(cmd=SPI_CMD_CLEAR_POLY_A, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0)

    # Send command
    await send_spi_cmd(dut, cmd=cmd_delete)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    # Only polygon A should be deleted
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y, depth=cmd_b.depth, enable=1)



@cocotb.test()
async def test_send_delete_poly_b(dut):
    """
    Test deleting polygon B params
    """

    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset - Since the screen has been fully disabled, we should be able to write commands
    await reset_dut(dut)

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon B
    cmd_b = SPIcmd.generate_random(SPI_CMD_WRITE_POLY_B)

    # Send command
    await send_spi_cmd(dut, cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 5)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    # Both Polys should have the correct data
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y, depth=cmd_b.depth, enable=1)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 5)

    # Arbitrary cmd to ploygon A
    cmd_a = SPIcmd.generate_random(SPI_CMD_WRITE_POLY_A)

    # Send command
    await send_spi_cmd(dut, cmd=cmd_a)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y, depth=cmd_a.depth, enable=1)
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y, depth=cmd_b.depth, enable=1)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 6)

    # Remove poly A only
    cmd_delete = SPIcmd(cmd=SPI_CMD_CLEAR_POLY_B, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0)

    # Send command
    await send_spi_cmd(dut, cmd=cmd_delete)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    # Only polygon B should be deleted
    check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y, depth=cmd_a.depth, enable=1)
    check_poly_b(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)



@cocotb.test()
async def test_send_enable_screen(dut):
    """
    Test enable screen cmd functionality
    """

    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset - Since the screen has been fully disabled, we should be able to write commands
    await reset_dut(dut)

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon A
    new_cmd = SPIcmd(cmd=SPI_CMD_ENABLE_SCREEN, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0)

    # Send command
    await send_spi_cmd(dut, cmd=new_cmd)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 1

    # All polygons should be clear
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)
    check_poly_b(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)

    # De-assert en_load signal (i.e VGA is not in HSYNC portion), polygon content should NOT update!
    dut.en_load.value = 0

    await Timer(50, units='ns')

    # Arbitrary cmd to ploygon B
    cmd_b = SPIcmd.generate_random(SPI_CMD_WRITE_POLY_B)

    # Send command
    await send_spi_cmd(dut, cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 1

    # All polygons should be clear
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)
    check_poly_b(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 1)

    # Assert en_load - we should be able to complete new SPI transactions now
    dut.en_load.value = 1
    await Timer(50, units='ns')

    # Send command
    await send_spi_cmd(dut, cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 1

    # New polygon data should be present
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y, depth=cmd_b.depth, enable=1)

    # Disable the screen again
    new_cmd = SPIcmd(cmd=SPI_CMD_DISABLE_SCREEN, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0)

    # Send command
    await send_spi_cmd(dut, cmd=new_cmd)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Screen should be disabled
    assert dut.bg_color_out.value == 0
    assert dut.en_screen_out.value == 0

    # Poly data should be the same
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y, depth=cmd_b.depth, enable=1)



@cocotb.test()
async def test_send_background(dut):
    """
    Test the screen background command
    """

    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset - Since the screen has been fully disabled, we should be able to write commands
    await reset_dut(dut)

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Write new background color
    new_cmd = SPIcmd(cmd=SPI_CMD_SET_BG_COLOR, color=COLOR_RED, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0)

    # Send command
    await send_spi_cmd(dut, cmd=new_cmd)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background should update
    assert dut.bg_color_out.value == COLOR_RED
    assert dut.en_screen_out.value == 0

    # All polygons should be clear
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)
    check_poly_b(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)

    # Wait a small amount before sending the command
    await Timer(50, units='ns')

    # Write new background color
    new_cmd = SPIcmd(cmd=SPI_CMD_SET_BG_COLOR, color=COLOR_GREEN, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0)

    # Send command
    await send_spi_cmd(dut, cmd=new_cmd)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background should update
    assert dut.bg_color_out.value == COLOR_GREEN
    assert dut.en_screen_out.value == 0

    # All polygons should be clear
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)
    check_poly_b(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)



@cocotb.test()
async def test_write_many_polygons(dut):
    """
    Test writing many polygons in different orders
    """

    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset - Since the screen has been fully disabled, we should be able to write commands
    await reset_dut(dut)

    # Wait a small amount before sending the command
    await Timer(50, units='ns')

    # Send 10 random polygons to Polygon slot A
    for _ in range(10):
        # Arbitrary cmd to ploygon A
        cmd_a = SPIcmd.generate_random(SPI_CMD_WRITE_POLY_A)
        # Send command
        await send_spi_cmd(dut, cmd=cmd_a)

        # Wait 1 clock cycle on DUT side
        await ClockCycles(dut.clk, 1)
        await Timer(1, units='ns')

        # Background and screen enable CMDs should not have changed
        assert dut.bg_color_out.value == 0
        assert dut.en_screen_out.value == 0

        # Polygon A should be updated
        check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y, depth=cmd_a.depth, enable=1)
        check_poly_b(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, depth=0, enable=0)

        # Wait some random and short number of clock cycles
        n_clk = random.randrange(start=2, stop=15, step=1)
        await ClockCycles(dut.clk, n_clk)

    # Send 10 random polygons to Polygon slot B
    for _ in range(10):
        # Arbitrary cmd to ploygon B
        cmd_b = SPIcmd.generate_random(SPI_CMD_WRITE_POLY_B)
        # Send command
        await send_spi_cmd(dut, cmd=cmd_b)

        # Wait 1 clock cycle on DUT side
        await ClockCycles(dut.clk, 1)
        await Timer(1, units='ns')

        # Background and screen enable CMDs should not have changed
        assert dut.bg_color_out.value == 0
        assert dut.en_screen_out.value == 0

        # Polygon B should be updated
        check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y, depth=cmd_a.depth, enable=1)
        check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y, depth=cmd_b.depth, enable=1)

        # Wait some random and short number of clock cycles
        n_clk = random.randrange(start=2, stop=15, step=1)
        await ClockCycles(dut.clk, n_clk)

    # Send 10 random polygons to A and B
    for _ in range(10):
        # Arbitrary cmd to both polygons
        cmd_a = SPIcmd.generate_random(SPI_CMD_WRITE_POLY_A)
        cmd_b = SPIcmd.generate_random(SPI_CMD_WRITE_POLY_B)
        # Send command
        await send_spi_cmd(dut, cmd=cmd_b)

        # Wait some random and short number of clock cycles
        n_clk = random.randrange(start=2, stop=15, step=1)
        await ClockCycles(dut.clk, n_clk)

        # Send command
        await send_spi_cmd(dut, cmd=cmd_a)

        # Background and screen enable CMDs should not have changed
        assert dut.bg_color_out.value == 0
        assert dut.en_screen_out.value == 0

        # Polygon B should be updated
        check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y, depth=cmd_a.depth, enable=1)
        check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y, depth=cmd_b.depth, enable=1)

        # Wait some random and short number of clock cycles
        n_clk = random.randrange(start=2, stop=15, step=1)
        await ClockCycles(dut.clk, n_clk)