"""
Top level testbench
"""

# SPDX-FileCopyrightText: Emery Nagy
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
import shared_utils as shared
from shared_utils import SPIcmd, send_spi_cmd

async def reset_device(dut):
    """
    Reset top level module
    """

    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

@cocotb.test()
async def test_reset(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")

    

