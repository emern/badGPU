"""
Test VGA driver
"""

# SPDX-FileCopyrightText: Emery Nagy
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer

# 640x480 VGA
VGA_TOTAL_COLS = 800
VGA_TOTAL_ROWS = 525

async def reset_dut(dut):
    """
    Reset DUT automatically

    Also zero out all inputs - should be called before every test
    """
    dut._log.info("Reset")

    dut.rst_n.value = 0

    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1


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

    # Wait a small time before checking
    await Timer(1, units='ns')

    # Counters should be at 0, h/v sync should be in their default states (1)
    assert dut.row_counter.value == 0
    assert dut.col_counter.value == 0
    assert dut.h_sync.value == 1
    assert dut.v_sync.value == 1
    assert dut.screen_inactive.value == 0

    dut._log.info("Finished")


@cocotb.test()
async def test_vga_synchronization(dut):
    """
    Test VGA module synchronization
    """
    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns") # Main clock is 25Mhz to match VGA
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Run through whole VGA screen
    for row in range(VGA_TOTAL_ROWS):
        for col in range(VGA_TOTAL_COLS):

            # Wait a small time before checking
            await Timer(1, units='ns')

            # Check VGA output from current position
            assert dut.row_counter.value == row
            assert dut.col_counter.value == col

            # Check signal visibility
            if col >= 640 or row >= 480:
                assert dut.screen_inactive.value == 1
            else:
                assert dut.screen_inactive.value == 0

            # Check HSYNC signal
            if col >= 656 and col <= 751:
                assert dut.h_sync.value == 0
            else:
                assert dut.h_sync.value == 1

            # Check VSYNC signal
            if row == 490 or row == 491:
                assert dut.v_sync.value == 0
            else:
                assert dut.v_sync.value == 1

            # Check INT signal
            if row >= 480:
                assert dut.cmd_en.value == 1
            else:
                assert dut.cmd_en.value == 0

            # Cycle clock
            await ClockCycles(dut.clk, 1)

    # Run through whole VGA screen a second time
    for row in range(VGA_TOTAL_ROWS):
        for col in range(VGA_TOTAL_COLS):

            # Wait a small time before checking
            await Timer(1, units='ns')

            # Check VGA output from current position
            assert dut.row_counter.value == row
            assert dut.col_counter.value == col

            # Check signal visibility
            if col >= 640 or row >= 480:
                assert dut.screen_inactive.value == 1
            else:
                assert dut.screen_inactive.value == 0

            # Check HSYNC signal
            if col >= 656 and col <= 751:
                assert dut.h_sync.value == 0
            else:
                assert dut.h_sync.value == 1

            # Check VSYNC signal
            if row == 490 or row == 491:
                assert dut.v_sync.value == 0
            else:
                assert dut.v_sync.value == 1

            # Check INT signal
            if row >= 480:
                assert dut.cmd_en.value == 1
            else:
                assert dut.cmd_en.value == 0

            # Cycle clock
            await ClockCycles(dut.clk, 1)

    dut._log.info("Finished")


