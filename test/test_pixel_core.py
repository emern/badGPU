"""
Testbench for pixel core functionality
"""

# SPDX-FileCopyrightText: Emery Nagy
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer
import numpy as np
from shared_utils import upscale_color, Polygon, should_pixel_be_rasterized
from PIL import Image
from os import environ

SAVED_IMAGE_PATH = 'image_artifacts/pixel_core/'


# Colors mapping
COLOR_BLACK = 0 # 000000
COLOR_RED = 48 # 110000
COLOR_GREEN = 12 # 001100
COLOR_BLUE = 3 # 000011

class PCPolygon(Polygon):
    """
    Structure to hold polygon params
    """
    def __init__(self, v0: np.ndarray, v1: np.ndarray, v2: np.ndarray, depth: int, color: int, enable: bool):
        super().__init__(v0=v0, v1=v1, v2=v2, depth=depth, color=color)

        # Enable is a unique parameter for the pixel core
        self.enable = enable


def set_polygon_a(dut, poly: PCPolygon):
    """
    Set ploygon A rasterization params
    """

    # Set vertices
    dut.v0_x_a.value = int(poly.v0[0] / 10)
    dut.v0_y_a.value = int(poly.v0[1] / 10)
    dut.v1_x_a.value = int(poly.v1[0] / 10)
    dut.v1_y_a.value = int(poly.v1[1] / 10)
    dut.v2_x_a.value = int(poly.v2[0] / 10)
    dut.v2_y_a.value = int(poly.v2[1] / 10)

    # Set color
    dut.poly_color_a.value = poly.raw_color

    # Set depth
    dut.poly_depth_a.value = poly.depth

    # Enable rasterization
    if poly.enable == True:
        dut.en_a.value = 1
    else:
        dut.en_a.value = 0


def set_polygon_b(dut, poly: PCPolygon):
    """
    Set ploygon B rasterization params
    """

    # Set vertices
    dut.v0_x_b.value = int(poly.v0[0] / 10)
    dut.v0_y_b.value = int(poly.v0[1] / 10)
    dut.v1_x_b.value = int(poly.v1[0] / 10)
    dut.v1_y_b.value = int(poly.v1[1] / 10)
    dut.v2_x_b.value = int(poly.v2[0] / 10)
    dut.v2_y_b.value = int(poly.v2[1] / 10)

    # Set color
    dut.poly_color_b.value = poly.raw_color

    # Set depth
    dut.poly_depth_b.value = poly.depth

    # Enable rasterization
    if poly.enable == True:
        dut.en_b.value = 1
    else:
        dut.en_b.value = 0


async def reset_dut(dut):
    """
    Reset DUT automatically
    """
    dut._log.info("Reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    await ClockCycles(dut.clk, 1)


async def draw_screen(dut):
    """
    Draw whole screen from DUT
    """
    gen_arr = np.zeros((480, 640, 3), dtype=np.uint8)

    # Loop over entire screen
    for row in range(480):
        for col in range(640):

            # Get rasterizer output
            dut.pixel_col.value = col
            dut.pixel_row.value = row

            await ClockCycles(dut.clk, 1)

            # Wait a small amount to measure the registered output
            await Timer(1, units='ns')

            # Save into seperate RGB channels
            gen_arr[row, col, :] = upscale_color(dut.pixel_out.value.integer)

    # Return generated images
    return gen_arr


def draw_screen_gt(poly_a: PCPolygon, poly_b: PCPolygon, bg_color: int):
    """
    Ground truth generation of whole screen
    """
    gt_arr = np.zeros((480, 640, 3), dtype=np.uint8)

    # Loop over entire screen
    for row in range(480):
        for col in range(640):

            # Check poly A
            if (poly_a.enable):
                a = bool(should_pixel_be_rasterized(poly_a.v0, poly_a.v1, poly_a.v2, col, row))
            else:
                a = False

            # Check poly B
            if (poly_b.enable):
                b = bool(should_pixel_be_rasterized(poly_b.v0, poly_b.v1, poly_b.v2, col, row))
            else:
                b = False

            # Find the "in front" polygon
            if (a == True) and (b == False):
                gt_arr[row, col, :] = poly_a.color
            elif (a == False) and (b == True):
                gt_arr[row, col, :] = poly_b.color
            elif (a == False) and (b == False):
                gt_arr[row, col, :] = upscale_color(bg_color)
            else:
                gt_arr[row, col, :] = poly_a.color if (poly_a.depth < poly_b.depth) else poly_b.color

    return gt_arr


@cocotb.test()
async def test_reset(dut):
    """
    Test internal state reset
    """
    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    assert dut.pixel_out.value == 0

    dut._log.info("Finished")


@cocotb.test()
async def test_multi_polygons(dut):
    """
    Test superimposed polygons
    """
    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Polygon parameters
    p_a = PCPolygon(v0=np.array([600, 200]),
                v1=np.array([440, 410]),
                v2=np.array([0, 0]),
                depth=0,
                color=COLOR_RED,
                enable=True)

    p_b = PCPolygon(v0=np.array([640, 0]),
                v1=np.array([0, 480]),
                v2=np.array([0, 0]),
                depth=4,
                color=COLOR_GREEN,
                enable=True)

    # Generate ground truth
    gt_arr = draw_screen_gt(p_a, p_b, COLOR_BLACK)

    # Run DUT
    dut.background_color.value = COLOR_BLACK
    set_polygon_a(dut, p_a)
    set_polygon_b(dut, p_b)
    gen_arr = await draw_screen(dut)

    if environ['SAVE_IMGS'] == 'True':
        gt_img = Image.fromarray(gt_arr, mode='RGB')
        gt_img.save(SAVED_IMAGE_PATH + 'gt_multi_poly_test.png')

        gen_img = Image.fromarray(gen_arr, mode='RGB')
        gen_img.save(SAVED_IMAGE_PATH + 'gen_multi_poly_test.png')

    # Check error
    error = np.absolute(gt_arr - gen_arr).mean()
    dut._log.info("Multilayered test error is " + str(error))
    if error > 0.2:
        assert 1 == 0

    dut._log.info("Finished")


@cocotb.test()
async def test_empty_screen(dut):
    """
    Test empty screen with only background colors
    """
    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Polygon parameters - should be disabled
    p_a = PCPolygon(v0=np.array([600, 200]),
                v1=np.array([446, 412]),
                v2=np.array([1, 1]),
                depth=0,
                color=COLOR_BLUE,
                enable=False)

    p_b = PCPolygon(v0=np.array([639, 0]),
                v1=np.array([0, 479]),
                v2=np.array([0, 0]),
                depth=4,
                color=COLOR_GREEN,
                enable=False)

    # Generate ground truth
    gt_arr = draw_screen_gt(p_a, p_b, COLOR_RED)

    # Run DUT
    dut.background_color.value = COLOR_RED
    set_polygon_a(dut, p_a)
    set_polygon_b(dut, p_b)
    gen_arr = await draw_screen(dut)

    if environ['SAVE_IMGS'] == 'True':
        gt_img = Image.fromarray(gt_arr, mode='RGB')
        gt_img.save(SAVED_IMAGE_PATH + 'gt_empty_screen.png')

        gen_img = Image.fromarray(gen_arr, mode='RGB')
        gen_img.save(SAVED_IMAGE_PATH + 'gen_empty_screen.png')

    # Check error
    error = np.absolute(gt_arr - gen_arr).mean()
    dut._log.info("Red background test error is " + str(error))
    if error > 0.001:
        assert 1 == 0

    dut._log.info("Finished")


@cocotb.test()
async def test_polygon_a(dut):
    """
    Test polygon A only
    """
    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Polygon parameters
    p_a = PCPolygon(v0=np.array([640, 200]),
                v1=np.array([300, 480]),
                v2=np.array([100, 100]),
                depth=0,
                color=COLOR_BLUE,
                enable=True)

    p_b = PCPolygon(v0=np.array([640, 0]),
                v1=np.array([0, 480]),
                v2=np.array([0, 0]),
                depth=4,
                color=COLOR_GREEN,
                enable=False)

    # Generate ground truth
    gt_arr = draw_screen_gt(p_a, p_b, COLOR_BLACK)

    # Run DUT
    dut.background_color.value = COLOR_BLACK
    set_polygon_a(dut, p_a)
    set_polygon_b(dut, p_b)
    gen_arr = await draw_screen(dut)

    if environ['SAVE_IMGS'] == 'True':
        gt_img = Image.fromarray(gt_arr, mode='RGB')
        gt_img.save(SAVED_IMAGE_PATH + 'gt_poly_a_test.png')

        gen_img = Image.fromarray(gen_arr, mode='RGB')
        gen_img.save(SAVED_IMAGE_PATH + 'gen_poly_a_test.png')

    # Check error
    error = np.absolute(gt_arr - gen_arr).mean()
    dut._log.info("Poly A test error is " + str(error))
    if error > 0.2:
        assert 1 == 0

    dut._log.info("Finished")


@cocotb.test()
async def test_polygon_b(dut):
    """
    Test polygon B only
    """
    dut._log.info("Start")

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset_dut(dut)

    # Polygon parameters
    p_a = PCPolygon(v0=np.array([640, 200]),
                v1=np.array([300, 480]),
                v2=np.array([100, 100]),
                depth=0,
                color=COLOR_BLUE,
                enable=False)

    p_b = PCPolygon(v0=np.array([220, 20]),
                v1=np.array([110, 300]),
                v2=np.array([10, 30]),
                depth=4,
                color=COLOR_GREEN,
                enable=True)

    # Generate ground truth
    gt_arr = draw_screen_gt(p_a, p_b, COLOR_BLACK)

    # Run DUT
    dut.background_color.value = COLOR_BLACK
    set_polygon_a(dut, p_a)
    set_polygon_b(dut, p_b)
    gen_arr = await draw_screen(dut)

    if environ['SAVE_IMGS'] == 'True':
        gt_img = Image.fromarray(gt_arr, mode='RGB')
        gt_img.save(SAVED_IMAGE_PATH + 'gt_poly_b_test.png')

        gen_img = Image.fromarray(gen_arr, mode='RGB')
        gen_img.save(SAVED_IMAGE_PATH + 'gen_poly_b_test.png')

    # Check error
    error = np.absolute(gt_arr - gen_arr).mean()
    dut._log.info("Poly B test error is " + str(error))
    if error > 0.2:
        assert 1 == 0

    dut._log.info("Finished")
