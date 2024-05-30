"""
Testbench for rasterization core functionality

Rasterization follows the following algorithm: https://erkaman.github.io/posts/fast_triangle_rasterization.html
"""

# SPDX-FileCopyrightText: Emery Nagy
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.triggers import Timer
import numpy as np
from matplotlib import pyplot as plt
from os import environ
from shared_utils import should_pixel_be_rasterized

SAVED_IMAGE_PATH = 'image_artifacts/rasterization/'


def print_internal_state(dut):
    """
    Print raster core internal state for debugging
    """
    print("State --- ")
    print(dut.user_project.l_res_a.value)
    print(dut.user_project.r_res_a.value)
    print(dut.user_project.l_res_b.value)
    print(dut.user_project.r_res_b.value)
    print(dut.user_project.l_res_c.value)
    print(dut.user_project.r_res_c.value)
    print(dut.rasterize.value)
    print("End State ---")

def set_polygon(dut, v0, v1, v2):
    """
    Set current ploygon for rasterization

    Polygon vertices are compressed by / 8
    """
    dut.v0_x.value = int(v0[0] / 8)
    dut.v1_x.value = int(v1[0] / 8)
    dut.v2_x.value = int(v2[0] / 8)

    dut.v0_y.value = int(v0[1] / 8)
    dut.v1_y.value = int(v1[1] / 8)
    dut.v2_y.value = int(v2[1] / 8)


async def draw_polygon_on_screen(dut, v0, v1, v2):
    """
    Draw a polygon on screen, check against ground truth algorithm
    """

    set_polygon(dut, v0, v1, v2)

    gt_arr = np.zeros((480, 640))
    gen_arr = np.zeros((480, 640))

    # Loop over entire screen
    for row in range(480):
        for col in range(640):
            # Generate ground truth
            gt_arr[row, col] = should_pixel_be_rasterized(v0, v1, v2, col, row)

            # Get rasterizer output
            dut.pixel_col.value = col
            dut.pixel_row.value = row

            await Timer(40, units="ns")

            gen_arr[row, col] = dut.rasterize.value

    # Return generated images
    return (gt_arr, gen_arr)


@cocotb.test()
async def test_whole_screen(dut):
    """
    Test whole screen with a nicely formatted, large triangle
    """
    dut._log.info("Start")

    # Reset input address
    dut.pixel_col.value = 0
    dut.pixel_row.value = 0

    # Make a large triangle
    v0 = [600, 200]
    v1 = [446, 412]
    v2 = [1, 1]

    gt_arr, gen_arr = await draw_polygon_on_screen(dut, v0, v1, v2)

    # Generated rasterization should be within 1% tolerance value
    error = (np.absolute(gt_arr - gen_arr)).mean()
    dut._log.info("Error is: " + str(error))
    if error > 0.01:
        assert 1 == 0

    # Save rasterized images if desired
    if environ['SAVE_IMGS'] == 'True':
        plt.imsave(SAVED_IMAGE_PATH + 'gt_whole_screen.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_whole_screen.png', gen_arr)
    
    dut._log.info("Finished")


@cocotb.test()
async def test_corner_top_left(dut):
    """
    Test large triangle on top left of screen
    """

    dut._log.info("Start")

    # Reset input address
    dut.pixel_col.value = 0
    dut.pixel_row.value = 0

    # Make large corner triangle
    v0 = [640, 0]
    v1 = [0, 480]
    v2 = [0, 0]

    gt_arr, gen_arr = await draw_polygon_on_screen(dut, v0, v1, v2)

    # Generated rasterization should be within 1% tolerance value
    error = (np.absolute(gt_arr - gen_arr)).mean()
    dut._log.info("Error is: " + str(error))
    if error > 0.01:
        assert 1 == 0

    # Save rasterized images if desired
    if environ['SAVE_IMGS'] == 'True':
        plt.imsave(SAVED_IMAGE_PATH + 'gt_top_left_screen.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_top_left_screen.png', gen_arr)

    dut._log.info("Finished")


@cocotb.test()
async def test_corner_top_right(dut):
    """
    Test large triangle on top right of screen
    """

    dut._log.info("Start")

    # Reset input address
    dut.pixel_col.value = 0
    dut.pixel_row.value = 0

    # Make large corner triangle
    v0 = [640, 0]
    v1 = [640, 480]
    v2 = [0, 0]

    gt_arr, gen_arr = await draw_polygon_on_screen(dut, v0, v1, v2)

    # Generated rasterization should be within 1% tolerance value
    error = (np.absolute(gt_arr - gen_arr)).mean()
    dut._log.info("Error is: " + str(error))
    if error > 0.01:
        assert 1 == 0

    # Save rasterized images if desired
    if environ['SAVE_IMGS'] == 'True':
        plt.imsave(SAVED_IMAGE_PATH + 'gt_top_right_screen.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_top_right_screen.png', gen_arr)

    dut._log.info("Finished")


@cocotb.test()
async def test_corner_bottom_right(dut):
    """
    Test large triangle on bottom right of screen
    """

    dut._log.info("Start")

    # Reset input address
    dut.pixel_col.value = 0
    dut.pixel_row.value = 0

    # Make large corner triangle
    v0 = [640, 0]
    v1 = [640, 480]
    v2 = [0, 480]

    gt_arr, gen_arr = await draw_polygon_on_screen(dut, v0, v1, v2)

    # Generated rasterization should be within 1% tolerance value
    error = (np.absolute(gt_arr - gen_arr)).mean()
    dut._log.info("Error is: " + str(error))
    if error > 0.01:
        assert 1 == 0

    # Save rasterized images if desired
    if environ['SAVE_IMGS'] == 'True':
        plt.imsave(SAVED_IMAGE_PATH + 'gt_bottom_right_screen.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_bottom_right_screen.png', gen_arr)

    dut._log.info("Finished")


@cocotb.test()
async def test_corner_bottom_left(dut):
    """
    Test large triangle on bottom left of screen
    """

    dut._log.info("Start")

    # Reset input address
    dut.pixel_col.value = 0
    dut.pixel_row.value = 0

    # Make large corner triangle
    v0 = [640, 480]
    v1 = [0, 480]
    v2 = [0, 0]

    gt_arr, gen_arr = await draw_polygon_on_screen(dut, v0, v1, v2)

    # Generated rasterization should be within 1% tolerance value
    error = (np.absolute(gt_arr - gen_arr)).mean()
    dut._log.info("Error is: " + str(error))
    if error > 0.01:
        assert 1 == 0

    # Save rasterized images if desired
    if environ['SAVE_IMGS'] == 'True':
        plt.imsave(SAVED_IMAGE_PATH + 'gt_bottom_left_screen.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_bottom_left_screen.png', gen_arr)

    dut._log.info("Finished")
