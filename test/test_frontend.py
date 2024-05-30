"""
Test GPU frontend module
"""

# SPDX-FileCopyrightText: Emery Nagy
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer
import random
from shared_utils import SPIcmd, send_spi_cmd
import shared_utils as shared

async def reset_dut(dut):
    """
    Reset DUT automatically

    Also zero out all inputs - should be called before every test
    """
    dut._log.info("Reset")

    dut.rst_n.value = 0
    dut.cs_in.value = 1
    dut.mosi_in.value = 0
    dut.sck_in.value = 0
    dut.en_load.value = 0

    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    await ClockCycles(dut.clk, 1)


def check_poly_a(dut, color: int, v0_x: int, v1_x: int, v2_x: int, v0_y: int, v1_y: int, v2_y: int):
    """
    Check polygon A stored output
    """
    assert (dut.color_a.value.integer) == color
    assert (dut.v0_x_a.value.integer) == v0_x
    assert (dut.v1_x_a.value.integer) == v1_x
    assert (dut.v2_x_a.value.integer) == v2_x
    assert (dut.v0_y_a.value.integer) == v0_y
    assert (dut.v1_y_a.value.integer) == v1_y
    assert (dut.v2_y_a.value.integer) == v2_y


def check_poly_b(dut, color: int, v0_x: int, v1_x: int, v2_x: int, v0_y: int, v1_y: int, v2_y: int):
    """
    Check polygon B stored output
    """
    assert (dut.color_b.value.integer) == color
    assert (dut.v0_x_b.value.integer) == v0_x
    assert (dut.v1_x_b.value.integer) == v1_x
    assert (dut.v2_x_b.value.integer) == v2_x
    assert (dut.v0_y_b.value.integer) == v0_y
    assert (dut.v1_y_b.value.integer) == v1_y
    assert (dut.v2_y_b.value.integer) == v2_y


def check_poly_enable(dut, enable_a: int, enable_b: int):
    """
    Check if polygon A is enabled
    """
    assert (dut.poly_enable_out.value.integer & 1) == enable_a
    assert (dut.poly_enable_out.value.integer & 2) >> 1 == enable_b


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
    dut.en_load.value = 1

    # Only the background color and polygon enable should be zeroed
    assert dut.bg_color_out.value == 0
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
    dut.en_load.value = 1

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon A
    new_cmd = SPIcmd(cmd=shared.SPI_CMD_WRITE_POLY_A, color=shared.COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in, dut.mosi_in, cmd=new_cmd)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # Polygon A should have correct changes and polygon B should remain unchanged
    check_poly_a(dut, color=shared.COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6)
    check_poly_enable(dut, enable_a=1, enable_b=0)



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
    dut.en_load.value = 1

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon B
    new_cmd = SPIcmd(cmd=shared.SPI_CMD_WRITE_POLY_B, color=shared.COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in, dut.mosi_in, cmd=new_cmd)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # Only polygon B should update
    check_poly_enable(dut, enable_a=0, enable_b=1)
    check_poly_b(dut, color=shared.COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6)



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
    dut.en_load.value = 1

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon A
    cmd_a = SPIcmd(cmd=shared.SPI_CMD_WRITE_POLY_A, color=shared.COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in, dut.mosi_in, cmd=cmd_a)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # Polygon A should have correct changes and polygon B should remain unchanged
    check_poly_a(dut, color=shared.COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6)
    check_poly_enable(dut, enable_a=1, enable_b=0)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 5)

    # Arbitrary cmd to ploygon B
    cmd_b = SPIcmd(cmd=shared.SPI_CMD_WRITE_POLY_B, color=shared.COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in, dut.mosi_in, cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 5)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # Both Polys should have the correct data
    check_poly_a(dut, color=shared.COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6)
    check_poly_b(dut, color=shared.COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17)
    check_poly_enable(dut, enable_a=1, enable_b=1)



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
    dut.en_load.value = 1

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon B
    cmd_b = SPIcmd(cmd=shared.SPI_CMD_WRITE_POLY_B, color=shared.COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 5)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # Both Polys should have the correct data
    check_poly_b(dut, color=shared.COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17)
    check_poly_enable(dut, enable_a=0, enable_b=1)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 5)

    # Arbitrary cmd to ploygon A
    cmd_a = SPIcmd(cmd=shared.SPI_CMD_WRITE_POLY_A, color=shared.COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_a)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    check_poly_a(dut, color=shared.COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6)
    check_poly_b(dut, color=shared.COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17)
    check_poly_enable(dut, enable_a=1, enable_b=1)



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
    dut.en_load.value = 1

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon B
    cmd_b = SPIcmd.generate_random(shared.SPI_CMD_WRITE_POLY_B)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 5)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # Both Polys should have the correct data
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y)
    check_poly_enable(dut, enable_a=0, enable_b=1)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 5)

    # Arbitrary cmd to ploygon A
    cmd_a = SPIcmd.generate_random(shared.SPI_CMD_WRITE_POLY_A)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_a)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y)
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y)
    check_poly_enable(dut, enable_a=1, enable_b=1)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 6)

    # Remove poly A only
    cmd_delete = SPIcmd(cmd=shared.SPI_CMD_CLEAR_POLY_A, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_delete)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # Only polygon A should be deleted
    check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0)
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y)
    check_poly_enable(dut, enable_a=0, enable_b=1)



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
    dut.en_load.value = 1

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Arbitrary cmd to ploygon B
    cmd_b = SPIcmd.generate_random(shared.SPI_CMD_WRITE_POLY_B)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 5)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # Both Polys should have the correct data
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y)
    check_poly_enable(dut, enable_a=0, enable_b=1)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 5)

    # Arbitrary cmd to ploygon A
    cmd_a = SPIcmd.generate_random(shared.SPI_CMD_WRITE_POLY_A)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_a)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y)
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y)
    check_poly_enable(dut, enable_a=1, enable_b=1)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 6)

    # Remove poly A only
    cmd_delete = SPIcmd(cmd=shared.SPI_CMD_CLEAR_POLY_B, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_delete)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # Only polygon B should be deleted
    check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y)
    check_poly_b(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0)
    check_poly_enable(dut, enable_a=1, enable_b=0)



@cocotb.test()
async def test_send_enable_load(dut):
    """
    Test enable load functionality
    """

    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset - Since the screen has been fully disabled, we should be able to write commands
    await reset_dut(dut)

    # De-assert en_load signal (i.e VGA is not in HSYNC portion), polygon content should NOT update!
    dut.en_load.value = 0

    await Timer(50, units='ns')

    # Arbitrary cmd to ploygon B
    cmd_b = SPIcmd.generate_random(shared.SPI_CMD_WRITE_POLY_B)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # All polygons should be clear
    check_poly_enable(dut, enable_a=0, enable_b=0)

    # Wait some clock cycles
    await ClockCycles(dut.clk, 1)

    # Assert en_load - we should be able to complete new SPI transactions now
    dut.en_load.value = 1
    await Timer(50, units='ns')

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_b)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # New polygon data should be present
    check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y)
    check_poly_enable(dut, enable_a=0, enable_b=1)



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
    dut.en_load.value = 1

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Write new background color
    new_cmd = SPIcmd(cmd=shared.SPI_CMD_SET_BG_COLOR, color=shared.COLOR_RED, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=new_cmd)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background should update
    assert dut.bg_color_out.value == shared.COLOR_RED

    # All polygons should be clear
    check_poly_enable(dut, enable_a=0, enable_b=0)

    # Wait a small amount before sending the command
    await Timer(50, units='ns')

    # Write new background color
    new_cmd = SPIcmd(cmd=shared.SPI_CMD_SET_BG_COLOR, color=shared.COLOR_GREEN, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=new_cmd)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 1)
    await Timer(1, units='ns')

    # Background should update
    assert dut.bg_color_out.value == shared.COLOR_GREEN

    # All polygons should be clear
    check_poly_enable(dut, enable_a=0, enable_b=0)



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
    dut.en_load.value = 1

    # Wait a small amount before sending the command
    await Timer(50, units='ns')

    # Send 10 random polygons to Polygon slot A
    for _ in range(10):
        # Arbitrary cmd to ploygon A
        cmd_a = SPIcmd.generate_random(shared.SPI_CMD_WRITE_POLY_A)
        # Send command
        await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_a)

        # Wait 1 clock cycle on DUT side
        await ClockCycles(dut.clk, 1)
        await Timer(1, units='ns')

        # Background and screen enable CMDs should not have changed
        assert dut.bg_color_out.value == 0


        # Polygon A should be updated
        check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y)
        check_poly_enable(dut, enable_a=1, enable_b=0)

        # Wait some random and short number of clock cycles
        n_clk = random.randrange(start=2, stop=15, step=1)
        await ClockCycles(dut.clk, n_clk)

    # Send 10 random polygons to Polygon slot B
    for _ in range(10):
        # Arbitrary cmd to ploygon B
        cmd_b = SPIcmd.generate_random(shared.SPI_CMD_WRITE_POLY_B)
        # Send command
        await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_b)

        # Wait 1 clock cycle on DUT side
        await ClockCycles(dut.clk, 1)
        await Timer(1, units='ns')

        # Background and screen enable CMDs should not have changed
        assert dut.bg_color_out.value == 0


        # Polygon B should be updated
        check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y)
        check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y)
        check_poly_enable(dut, enable_a=1, enable_b=1)

        # Wait some random and short number of clock cycles
        n_clk = random.randrange(start=2, stop=15, step=1)
        await ClockCycles(dut.clk, n_clk)

    # Send 10 random polygons to A and B
    for _ in range(10):
        # Arbitrary cmd to both polygons
        cmd_a = SPIcmd.generate_random(shared.SPI_CMD_WRITE_POLY_A)
        cmd_b = SPIcmd.generate_random(shared.SPI_CMD_WRITE_POLY_B)
        # Send command
        await send_spi_cmd(dut.cs_in, dut.sck_in,  dut.mosi_in, cmd=cmd_b)

        # Wait some random and short number of clock cycles
        n_clk = random.randrange(start=2, stop=15, step=1)
        await ClockCycles(dut.clk, n_clk)

        # Send command
        await send_spi_cmd(dut.cs_in, dut.sck_in, dut.mosi_in, cmd=cmd_a)

        await ClockCycles(dut.clk, 2)

        # Background and screen enable CMDs should not have changed
        assert dut.bg_color_out.value == 0


        # Polygon B should be updated
        check_poly_a(dut, color=cmd_a.color, v0_x=cmd_a.v0_x, v1_x=cmd_a.v1_x, v2_x=cmd_a.v2_x, v0_y=cmd_a.v0_y, v1_y=cmd_a.v1_y, v2_y=cmd_a.v2_y)
        check_poly_b(dut, color=cmd_b.color, v0_x=cmd_b.v0_x, v1_x=cmd_b.v1_x, v2_x=cmd_b.v2_x, v0_y=cmd_b.v0_y, v1_y=cmd_b.v1_y, v2_y=cmd_b.v2_y)
        check_poly_enable(dut, enable_a=1, enable_b=1)

        # Wait some random and short number of clock cycles
        n_clk = random.randrange(start=2, stop=15, step=1)
        await ClockCycles(dut.clk, n_clk)


@cocotb.test()
async def test_send_bad_cmd(dut):
    """
    Test writing a bad command to the SPI handler
    """

    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset - Since the screen has been fully disabled, we should be able to write commands
    await reset_dut(dut)
    dut.en_load.value = 1

    # Wait a small amount before sending the command
    await Timer(1, units='ns')

    # Send all possible invalid cmd bytes
    for bad_cmd in range(256):
        if SPIcmd.is_cmd_valid(bad_cmd) == False:
            # Send command to polygon A with bad CMD parameter
            cmd_a = SPIcmd(cmd=bad_cmd, color=shared.COLOR_GREEN, v0_x=1, v0_y=2, v2_x=3, v1_x=4, v1_y=5, v2_y=6)

            # Send command
            await send_spi_cmd(dut.cs_in, dut.sck_in, dut.mosi_in, cmd=cmd_a)

            # Wait 1 clock cycle on DUT side
            await ClockCycles(dut.clk, 1)
            await Timer(1, units='ns')

            # Background and screen enable CMDs should not have changed
            assert dut.bg_color_out.value == 0

            # Both polygons should remain unchanged
            check_poly_a(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, enable=0)
            check_poly_b(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, enable=0)

            # Wait some clock cycles
            await ClockCycles(dut.clk, 5)

    # Now write a real command to poly A
    cmd_a = SPIcmd(cmd=shared.SPI_CMD_WRITE_POLY_A, color=shared.COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17)

    # Send command
    await send_spi_cmd(dut.cs_in, dut.sck_in, dut.mosi_in, cmd=cmd_a)

    # Wait 1 clock cycle on DUT side
    await ClockCycles(dut.clk, 5)
    await Timer(1, units='ns')

    # Background and screen enable CMDs should not have changed
    assert dut.bg_color_out.value == 0

    # Both Polys should have the correct data
    check_poly_a(dut, color=shared.COLOR_RED, v0_x=40, v0_y=12, v2_x=22, v1_x=11, v1_y=14, v2_y=17, enable=1)
    check_poly_b(dut, color=0, v0_x=0, v0_y=0, v2_x=0, v1_x=0, v1_y=0, v2_y=0, enable=0)
