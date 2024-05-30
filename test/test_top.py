"""
Top level testbench
"""

# SPDX-FileCopyrightText: Emery Nagy
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.clock import Clock, Timer
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge
import shared_utils as shared
from shared_utils import SPIcmd, send_spi_cmd, Polygon, upscale_color_from_components, should_pixel_be_rasterized, \
                                        upscale_color, COLOR_RED, COLOR_GREEN, COLOR_BLUE, SPI_CMD_WRITE_POLY_A, \
                                        SPI_CMD_WRITE_POLY_B, SPI_CMD_CLEAR_POLY_A, SPI_CMD_CLEAR_POLY_B
import numpy as np
from PIL import Image
from os import environ

SAVED_IMAGE_PATH = 'image_artifacts/top_level/'
VISIBLE_N_CYCLES = 800*480
SCREEN_N_CYCLES = 800*525



class VGAScreen:
    """
    Class handles internal state of VGA screen through tests
    """
    def __init__(self, dut, clk_signal):

        # Create VGA screen mock with 3 color channels
        self.screen_buf = np.zeros((525, 800, 3), dtype=np.uint8)
        self.gt_buf = np.zeros((525, 800, 3), dtype=np.uint8)
        self.background_color = np.array([0, 0, 0]) # Black bg to start
        self.pos_x = 0
        self.pos_y = 0
        self.poly_a = None
        self.poly_b = None
        self.dut = dut
        self.clk_signal = clk_signal
        self.has_been_reset = False

    async def clock(self):
        """
        Clock the VGA screen and check hsync and vsync
        """
        while True:
            # Clock testbench
            self.clk_signal.value = 0

            await Timer(20, units='ns')

            self.clk_signal.value = 1

            # Little hack here, if we split this time up a little bit it guarantees we run the code below when using even 40ns clock period
            await Timer(19, units='ns')

            # Only assert after master reset since gate level simulation will have undefined value
            if self.has_been_reset == True:

                # Update internal position counter
                self.pos_x += 1
                if self.pos_x == 800:
                    self.pos_x = 0
                    self.pos_y += 1

                if self.pos_y == 525:
                    self.pos_y = 0

                # Check HSYNC signal
                if self.pos_x >= 656 and self.pos_x <= 751:
                    assert self.dut.hsync.value == 0
                    pass
                else:
                    assert self.dut.hsync.value == 1

                # Check VSYNC signal
                if self.pos_y == 490 or self.pos_y == 491:
                    assert self.dut.vsync.value == 0
                else:
                    assert self.dut.vsync.value == 1

                # Check INT pin
                if self.pos_y >= 480:
                    assert self.dut.int_out.value == 1
                else:
                    assert self.dut.int_out.value == 0

                # Write output into screen buffer
                self.screen_buf[self.pos_y, self.pos_x, :] = upscale_color_from_components(c_red=self.dut.red_out.value,
                                                                                            c_green=self.dut.green_out.value,
                                                                                            c_blue=self.dut.blue_out.value)

                # Generate out "Ground truth" buffer value (if applicable)
                if self.pos_x < 640 and self.pos_y < 480:
                    # Rasterize poly_a if required
                    if self.poly_a != None:
                        a = bool(should_pixel_be_rasterized(v0=self.poly_a.v0,
                                                        v1=self.poly_a.v1,
                                                        v2=self.poly_a.v2,
                                                        p_x=self.pos_x,
                                                        p_y=self.pos_y))
                    else:
                        a = False

                    # Rasterize poly_b if required
                    if self.poly_b != None:
                        b = bool(should_pixel_be_rasterized(v0=self.poly_b.v0,
                                                        v1=self.poly_b.v1,
                                                        v2=self.poly_b.v2,
                                                        p_x=self.pos_x,
                                                        p_y=self.pos_y))
                    else:
                        b = False

                    # Find the "in front" polygon
                    if (a == True):
                        # Polygon A takes "priority"
                        self.gt_buf[self.pos_y, self.pos_x, :] = self.poly_a.color
                    elif (b == True):
                        self.gt_buf[self.pos_y, self.pos_x, :] = self.poly_b.color
                    else:
                        # Background color
                        self.gt_buf[self.pos_y, self.pos_x, :] = self.background_color

            else:
                # Reset internal counter
                self.pos_y = 0
                self.pos_x = 0

            # Round the clock cycle to 40ns
            await Timer(1, units='ns')


    async def set_poly_a(self, poly: Polygon, save_poly=True):
        """
        Set polygon A params (if applicable), sends data over virtual spi bus
        """

        if save_poly == True:
            self.poly_a = poly

        # Generate and send command
        new_cmd = SPIcmd.from_poly(poly=poly, cmd=SPI_CMD_WRITE_POLY_A)
        await send_spi_cmd(cs_signal=self.dut.spi_cs, sck_signal=self.dut.spi_sck, mosi_signal=self.dut.spi_mosi, cmd=new_cmd)



    async def set_poly_b(self, poly: Polygon, save_poly=True):
        """
        Set polygon B params (if applicable), sends data over virtual spi bus
        """

        if save_poly == True:
            self.poly_b = poly

        # Generate and send command
        new_cmd = SPIcmd.from_poly(poly=poly, cmd=SPI_CMD_WRITE_POLY_B)
        await send_spi_cmd(cs_signal=self.dut.spi_cs, sck_signal=self.dut.spi_sck, mosi_signal=self.dut.spi_mosi, cmd=new_cmd)


    async def clear_poly_a(self):
        """
        Clear Polygon A parameters, sends data over virtual spi bus

        Note: This will fail if not sent during the vsync period!
        """
        self.poly_a = None

        # Generate and send command
        new_cmd = SPIcmd(cmd=SPI_CMD_CLEAR_POLY_A, color=0, v0_x=0, v1_x=0, v2_x=0, v0_y=0, v1_y=0, v2_y=0)
        await send_spi_cmd(cs_signal=self.dut.spi_cs, sck_signal=self.dut.spi_sck, mosi_signal=self.dut.spi_mosi, cmd=new_cmd)


    async def clear_poly_b(self):
        """
        Clear Polygon B parameters, sends data over virtual spi bus

        Note: This will fail if not sent during the vsync period!
        """
        self.poly_b = None

        # Generate and send command
        new_cmd = SPIcmd(cmd=SPI_CMD_CLEAR_POLY_B, color=0, v0_x=0, v1_x=0, v2_x=0, v0_y=0, v1_y=0, v2_y=0)
        await send_spi_cmd(cs_signal=self.dut.spi_cs, sck_signal=self.dut.spi_sck, mosi_signal=self.dut.spi_mosi, cmd=new_cmd)


def calc_cycles(n_cycles) -> int:
    """
    Calculate number of ns per n_cycles
    """
    return n_cycles*40


def save_images(gt: np.ndarray, gen: np.ndarray, name: str):
    """
    Helper to save images
    """
    # Save images - Only save 640x480 RGB data
    if environ['SAVE_IMGS'] == 'True':
        gt_img = Image.fromarray(gt[0:479, 0:639, :], mode='RGB')
        gt_img.save(SAVED_IMAGE_PATH + 'gt_' + name + '.png')

        gen_img = Image.fromarray(gen[0:479, 0:639, :], mode='RGB')
        gen_img.save(SAVED_IMAGE_PATH + 'gen_' + name + '.png')


def check_frame_error(dut, gt: np.ndarray, gen: np.ndarray, tolerance: float):
    """
    Helper checks absolute mean error between frames (normalized)
    """
    error = (np.absolute(gt[0:479, 0:639, :] - gen[0:479, 0:639, :]) / 255).mean()
    dut._log.info("Frame error is " + str(error))
    if (error > tolerance):
        assert 1 == 0


async def reset_device(dut, screen: VGAScreen):
    """
    Reset top level module
    
    Also bring SPI back to default state
    """

    dut.spi_sck.value = 0
    dut.spi_mosi.value = 0
    dut.spi_cs.value = 1

    dut.rst_n.value = 0
    await Timer(calc_cycles(10), units='ns')
    dut.rst_n.value = 1
    await Timer(calc_cycles(1), units='ns')
    screen.has_been_reset = True


@cocotb.test()
async def test_reset(dut):
    """
    Test module reset functionality
    """
    dut._log.info("Start")

    # Generate screen and start clock
    screen = VGAScreen(dut=dut, clk_signal=dut.clk)
    cocotb.start_soon(screen.clock())

    # Reset device
    await reset_device(dut, screen=screen)

    # Clock asserts screen state signals automatically
    await Timer(calc_cycles(4), units='ns')

    dut._log.info("Finished")


@cocotb.test()
async def test_empty_screen(dut):
    """
    Test that device stays stable with empty screen
    """
    dut._log.info("Start")

    # Generate screen and start clock
    screen = VGAScreen(dut=dut, clk_signal=dut.clk)
    cocotb.start_soon(screen.clock())

    # Reset
    dut._log.info("Reset")
    await reset_device(dut, screen=screen)

    # Run 2 whole frames of the timing to be sure
    await Timer(calc_cycles(SCREEN_N_CYCLES*2 + 1), units='ns')
    dut._log.info("Finished")


@cocotb.test()
async def test_draw_single_polygon_per_frame(dut):
    """
    Test drawing a single polygon per frame
    """
    dut._log.info("Start")

    # Generate screen and start clock
    screen = VGAScreen(dut=dut, clk_signal=dut.clk)
    cocotb.start_soon(screen.clock())

    # Reset device
    await reset_device(dut, screen=screen)

    # Run until we are at the hsync portion of drawing the screen
    await Timer(calc_cycles(VISIBLE_N_CYCLES+1), units='ns')

    dut._log.info("Setting Polygon A")

    # Polygon parameters
    p_a = Polygon(v0=[600, 0],
                v1=[200, 410],
                v2=[10, 10],
                color=COLOR_RED)

    # Set polygons internally
    await screen.set_poly_a(poly=p_a)

    # Fill in the rest of the screen blanking period
    await Timer(calc_cycles((SCREEN_N_CYCLES) - (800 * screen.pos_y + screen.pos_x)), units='ns')

    dut._log.info("Writing new frame")

    # Generate the new frame with the polygon included
    await Timer(calc_cycles(VISIBLE_N_CYCLES+1), units='ns')

    dut._log.info("Saving frame")


    save_images(gt=screen.gt_buf, gen=screen.screen_buf, name='draw_single_poly_frame_1')

    # Check gt vs generated to 1%
    check_frame_error(dut, gt=screen.gt_buf, gen=screen.screen_buf, tolerance=0.01)

    dut._log.info("Setting Polygon B")

    # Write a second polygon
    p_b = Polygon(v0=[100, 0],
                v1=[50, 480],
                v2=[1, 1],
                color=COLOR_GREEN)

    # Set polygons internally
    await screen.set_poly_b(poly=p_b)

    # Fill in the rest of the screen blanking period
    await Timer(calc_cycles((SCREEN_N_CYCLES) - (800 * screen.pos_y + screen.pos_x)), units='ns')

    dut._log.info("Writing new frame")

    # Generate the new frame with the polygon included
    await Timer(calc_cycles(VISIBLE_N_CYCLES+1), units='ns')

    dut._log.info("Saving frame")

    # Save new frame
    save_images(gt=screen.gt_buf, gen=screen.screen_buf, name='draw_single_poly_frame_2')

    # Check gt vs generated to 1%
    check_frame_error(dut, gt=screen.gt_buf, gen=screen.screen_buf, tolerance=0.01)


    dut._log.info("Clearing Polygon A")

    # Clear poly A
    await screen.clear_poly_a()

    # Fill in the rest of the screen blanking period
    await Timer(calc_cycles((SCREEN_N_CYCLES) - (800 * screen.pos_y + screen.pos_x)), units='ns')

    dut._log.info("Writing new frame")

    # Generate the new visible frame
    await Timer(calc_cycles(VISIBLE_N_CYCLES+1), units='ns')

    # Save new frame
    save_images(gt=screen.gt_buf, gen=screen.screen_buf, name='draw_single_poly_frame_3')

    # Check gt vs generated to 1%
    check_frame_error(dut, gt=screen.gt_buf, gen=screen.screen_buf, tolerance=0.01)


    dut._log.info("Clearing Polygon B")

    # Clear poly B
    await screen.clear_poly_b()

    # Fill in the rest of the screen blanking period
    await Timer(calc_cycles((SCREEN_N_CYCLES) - (800 * screen.pos_y + screen.pos_x)), units='ns')

    dut._log.info("Writing new frame")

    # Generate the new visible frame
    await Timer(calc_cycles(VISIBLE_N_CYCLES+1), units='ns')

    # Save new frame
    save_images(gt=screen.gt_buf, gen=screen.screen_buf, name='draw_single_poly_frame_4')

    # Check gt vs generated to 1%
    check_frame_error(dut, gt=screen.gt_buf, gen=screen.screen_buf, tolerance=0.01)

    dut._log.info("Finished")


