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

# Enable saving sample images for visual inspection
# Should be turned off for CI
SAVE_IMAGE_OUTPUT = 0
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
    

def set_polygon(dut, v0, v1, v2):
    """
    Set current ploygon for rasterization
    """
    dut.v0_x.value = v0[0]
    dut.v1_x.value = v1[0]
    dut.v2_x.value = v2[0]

    dut.v0_y.value = v0[1]
    dut.v1_y.value = v1[1]
    dut.v2_y.value = v2[1]


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

            # Check rasterized output against ground truth
            if (gen_arr[row, col] != gt_arr[row, col]):
                print("Mismatch detected!")
                print(col)
                print(row)
                print("Actual: ")
                should_pixel_be_rasterized(v0, v1, v2, col, row, log=True)
                print("Device output:")
                print_internal_state(dut)
                assert 1 == 0

    # Return generated images
    return (gt_arr, gen_arr)


@cocotb.test()
async def test_small(dut):
    """
    Run smoke test on small triangle
    """
    dut._log.info("Start")

    # Reset inputs, output only valid if a valid set of unique vertices is given
    dut.pixel_col.value = 0
    dut.pixel_row.value = 0

    # Note: Order here on the vertices is important, the GPU frontend must arrange them in the proper order
    v0 = [1, 0]
    v1 = [0, 1]
    v2 = [0, 0]

    set_polygon(dut, v0, v1, v2)

    # Wait 1 clock cycle
    await Timer(40, units="ns")

    # [(1,0), (0,1), (0,0)] is a valid polygon to draw when the pixel is (0,0) -> Single point
    assert dut.rasterize.value == 1

    # Check all points on given triangle

    # (0, 1)
    dut.pixel_col.value = 0
    dut.pixel_row.value = 1

    await Timer(40, units="ns")

    assert dut.rasterize.value == 1

    # (1, 0)
    dut.pixel_col.value = 1
    dut.pixel_row.value = 0

    await Timer(40, units="ns")

    assert dut.rasterize.value == 1

    # Check points outside the triangle are not drawn

    # (1, 1)
    dut.pixel_col.value = 1
    dut.pixel_row.value = 1

    await Timer(40, units="ns")

    assert dut.rasterize.value == 0

    # (2, 1)
    dut.pixel_col.value = 2
    dut.pixel_row.value = 1

    await Timer(40, units="ns")

    assert dut.rasterize.value == 0

    dut._log.info("Passed")


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

    # Save rasterized images if desired
    if SAVE_IMAGE_OUTPUT == 1:
        plt.imsave(SAVED_IMAGE_PATH + 'gt_whole_screen.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_whole_screen.png', gen_arr)
    
    dut._log.info("Passed")


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

    # Save rasterized images if desired
    if SAVE_IMAGE_OUTPUT == 1:
        plt.imsave(SAVED_IMAGE_PATH + 'gt_top_left_screen.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_top_left_screen.png', gen_arr)

    dut._log.info("Passed")


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

    # Save rasterized images if desired
    if SAVE_IMAGE_OUTPUT == 1:
        plt.imsave(SAVED_IMAGE_PATH + 'gt_top_right_screen.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_top_right_screen.png', gen_arr)

    dut._log.info("Passed")


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

    # Save rasterized images if desired
    if SAVE_IMAGE_OUTPUT == 1:
        plt.imsave(SAVED_IMAGE_PATH + 'gt_bottom_right_screen.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_bottom_right_screen.png', gen_arr)

    dut._log.info("Passed")


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

    # Save rasterized images if desired
    if SAVE_IMAGE_OUTPUT == 1:
        plt.imsave(SAVED_IMAGE_PATH + 'gt_bottom_left_screen.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_bottom_left_screen.png', gen_arr)

    dut._log.info("Passed")
