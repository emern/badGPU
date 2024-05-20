"""
Testbench for ray tracer core functionality

"""

# SPDX-FileCopyrightText: Emery Nagy
# SPDX-License-Identifier: MIT

import cocotb
import cocotb.binary
from cocotb.triggers import Timer
import numpy as np
from matplotlib import pyplot as plt
from fxpmath import Fxp

# Enable saving sample images for visual inspection
# Should be turned off for CI
SAVE_IMAGE_OUTPUT = 0
SAVED_IMAGE_PATH = 'image_artifacts/ray_trace/'


def print_internal_state(dut):
    """
    Print ray tracer core internal state for debugging
    """

    print("--Core internals--")

    print("--Edge_1--")
    print(dut.user_project.edge_1_x.value.signed_integer)
    print(dut.user_project.edge_1_y.value.signed_integer)
    print(dut.user_project.edge_1_z.value.signed_integer)

    print("--Edge_2--")
    print(dut.user_project.edge_2_x.value.signed_integer)
    print(dut.user_project.edge_2_y.value.signed_integer)
    print(dut.user_project.edge_2_z.value.signed_integer)

    print("--Determinant--")
    print(dut.user_project.inv_det.value)
    print(dut.user_project.determinant.value.integer)

    print("--S--")
    print(dut.user_project.s_x.value.signed_integer)
    print(dut.user_project.s_y.value.signed_integer)
    print(dut.user_project.s_z.value.signed_integer)

    print("--U--")
    print(dut.user_project.u.value.signed_integer)

    print("--Q--")
    print(dut.user_project.q_x.value.signed_integer)
    print(dut.user_project.q_y.value.signed_integer)
    print(dut.user_project.q_z.value.signed_integer)

    print("--V--")
    print(dut.user_project.v.value.signed_integer)

    print("--T--")
    print(dut.user_project.unscaled_t.value.signed_integer)
    print(dut.user_project.t_exp.value)
    print(dut.user_project.t.value)

    print("--U+V--")
    print(dut.user_project.bary_sum.value.signed_integer)

    print("--Output--")
    print(dut.rasterize.value)
    print(dut.z_actual.value)

def get_gt_depth(px, py, v0, v1, v2, log=False):
    """
    Use the Moller Trombore ray tracing algorithm to calculate the depth
    """
    # O and D
    origin = np.array([px, py, 0])
    # direction = np.array([0, 0, -1])

    # Compute edge 1 and 2 vectors
    # Cached
    edge_1 = v1 - v0
    edge_2 = v2 - v0

    # Determinant
    # h = np.cross(direction, edge_2)
    # h = np.array([edge_2[1], -edge_2[0], 0])
    # a = np.dot(edge_1, h)
    a = edge_1[0]*edge_2[1] + edge_1[1]*-edge_2[0]

    # Inverse -> Lookup
    # Cached
    # Max input value = 640*480 + 480*640
    # Fits in 21 signed bits
    f = 1./a

    # Barycentric parameters
    s = origin - v0
    # u = np.dot(f, np.dot(s, h))
    # Should fit in 21 bits
    u = np.array([(s[0] * edge_2[1] +  s[1] * -edge_2[0])])

    # Compute other barycentric coordinate
    q = np.cross(s, edge_1)
    # v = np.dot(f, -q[2])
    v = -q[2]

    # Compute distance along ray
    # t = np.dot(f, np.dot(edge_2, q))
    t = f * ((edge_2[0] * q[0]) + (edge_2[1] * q[1]) + (edge_2[2] * q[2]))

    # Print debug if needed
    if log == True:
        print("--Ground Truth--")

        print("--Edges--")
        print(edge_1)
        print(edge_2)

        print("--Det--")
        print(f)
        print(a)

        print("--S--")
        print(s)

        print("--U--")
        print(u)

        print("--Q--")
        print(q)


        print("--V--")
        print(v)

        print("--T--")
        print((edge_2[0] * q[0]) + (edge_2[1] * q[1]) + (edge_2[2] * q[2]))
        print(-t)

        print("--U+V--")
        print(u+v)

    # Check if there is an intersection
    if (u > a) or (u < 0) or ((u + v) > a) or (v > a) or (v < 0):
        # No intersection means that distance is 8
        return -7., False

    # t is simply the z value
    return round(t), True


def set_polygon(dut, v0, v1, v2):
    """
    Set current ploygon for rasterization
    """

    dut.vertex_0_x.value = int(v0[0])
    dut.vertex_0_y.value = int(v0[1])
    dut.vertex_0_z.value = cocotb.binary.BinaryValue(int(v0[2]), 3, bigEndian=False)

    dut.vertex_1_x.value = int(v1[0])
    dut.vertex_1_y.value = int(v1[1])
    dut.vertex_1_z.value = cocotb.binary.BinaryValue(int(v1[2]), 3, bigEndian=False)

    dut.vertex_2_x.value = int(v2[0])
    dut.vertex_2_y.value = int(v2[1])
    dut.vertex_2_z.value = cocotb.binary.BinaryValue(int(v2[2]), 3, bigEndian=False)

    # Inverse determinant needs to be set specifically by TB as its a floating point division
    # TODO: Figure out how to handle this on the testbench side
    det = ((v1[0] - v0[0]) * (v2[1] - v0[1])) + ((v1[1] - v0[1]) * -(v2[0] - v0[0]))
    dut.determinant.value = cocotb.binary.BinaryValue(int(det), n_bits=23, bigEndian=False)

    inv_det = 1/det
    inv_det_converted = Fxp(inv_det, signed=False, n_word=46, n_frac=23)

    dut.inv_det.value = cocotb.binary.BinaryValue(inv_det_converted.bin(), 46)


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
            gt_arr[row, col], r = get_gt_depth(col, row, v0, v1, v2)

            # Get rasterizer output
            dut.pixel_col.value = col
            dut.pixel_row.value = row

            await Timer(40, units="ns")

            # Only set output value if device detects raterization
            if dut.rasterize.value == 1:
                gen_arr[row, col] = -1 * int(dut.z_actual.value.integer)
            else:
                gen_arr[row, col] = -7.

    # Return generated images
    return (gt_arr, gen_arr)


# @cocotb.test()
# async def test_small(dut):
#     """
#     Run smoke test on small triangle
#     """
#     dut._log.info("Start")

#     # Reset inputs, output only valid if a valid set of unique vertices is given
#     dut.pixel_col.value = 0
#     dut.pixel_row.value = 0

#     # Note: Order here on the vertices is important, the GPU frontend must arrange them in the proper order
#     v0 = [1, 0]
#     v1 = [0, 1]
#     v2 = [0, 0]

#     set_polygon(dut, v0, v1, v2)

#     # Wait 1 clock cycle
#     await Timer(40, units="ns")

#     # [(1,0), (0,1), (0,0)] is a valid polygon to draw when the pixel is (0,0) -> Single point
#     assert dut.rasterize.value == 1

#     # Check all points on given triangle

#     # (0, 1)
#     dut.pixel_col.value = 0
#     dut.pixel_row.value = 1

#     await Timer(40, units="ns")

#     assert dut.rasterize.value == 1

#     # (1, 0)
#     dut.pixel_col.value = 1
#     dut.pixel_row.value = 0

#     await Timer(40, units="ns")

#     assert dut.rasterize.value == 1

#     # Check points outside the triangle are not drawn

#     # (1, 1)
#     dut.pixel_col.value = 1
#     dut.pixel_row.value = 1

#     await Timer(40, units="ns")

#     assert dut.rasterize.value == 0

#     # (2, 1)
#     dut.pixel_col.value = 2
#     dut.pixel_row.value = 1

#     await Timer(40, units="ns")

#     assert dut.rasterize.value == 0

#     dut._log.info("Passed")


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
    v0 = np.array([600, 200, 0])
    v1 = np.array([446, 412, 7])
    v2 = np.array([1, 1, 4])

    gt_arr, gen_arr = await draw_polygon_on_screen(dut, v0, v1, v2)

    # Save rasterized images if desired
    if SAVE_IMAGE_OUTPUT == 1:
        plt.imsave(SAVED_IMAGE_PATH + 'gt_test_whole_screen.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_test_whole_screen.png', gen_arr)

    # Results will not be exactly the same due to floating point precision, should be within 20% of ground truth
    error = np.sqrt(np.mean(np.square((gt_arr - gen_arr))))
    dut._log.info("test_whole_screen absolute error is " + str(error))
    if error > 0.2:
        assert 1 == 0

    # Corners should be the known ground truth values, note that the ray tracer core output is saved as a negative z value
    assert gen_arr[v0[1], v0[0]] == -v0[2]
    assert gen_arr[v1[1], v1[0]] == -v1[2]
    assert gen_arr[v2[1], v2[0]] == -v2[2]

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
    v0 = np.array([639, 0, 7])
    v1 = np.array([0, 479, 0])
    v2 = np.array([0, 0, 3])

    gt_arr, gen_arr = await draw_polygon_on_screen(dut, v0, v1, v2)

    # Save rasterized images if desired
    if SAVE_IMAGE_OUTPUT == 1:
        plt.imsave(SAVED_IMAGE_PATH + 'gt_test_corner_top_left.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_test_corner_top_left.png', gen_arr)

    # Results will not be exactly the same due to floating point precision, should be within 20% of ground truth
    error = np.sqrt(np.mean(np.square((gt_arr - gen_arr))))
    dut._log.info("test_corner_top_left absolute error is " + str(error))
    if error > 0.2:
        assert 1 == 0

    # Corners should be the known ground truth values, note that the ray tracer core output is saved as a negative z value
    assert gen_arr[v0[1], v0[0]] == -v0[2]
    assert gen_arr[v1[1], v1[0]] == -v1[2]
    assert gen_arr[v2[1], v2[0]] == -v2[2]

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
    v0 = np.array([639, 0, 1])
    v1 = np.array([639, 479, 2])
    v2 = np.array([0, 0, 3])

    gt_arr, gen_arr = await draw_polygon_on_screen(dut, v0, v1, v2)

    # Save rasterized images if desired
    if SAVE_IMAGE_OUTPUT == 1:
        plt.imsave(SAVED_IMAGE_PATH + 'gt_test_corner_top_right.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_test_corner_top_right.png', gen_arr)

    # Results will not be exactly the same due to floating point precision, should be within 20% of ground truth
    error = np.sqrt(np.mean(np.square((gt_arr - gen_arr))))
    dut._log.info("test_corner_top_right absolute error is " + str(error))
    if error > 0.2:
        assert 1 == 0

    # Corners should be the known ground truth values, note that the ray tracer core output is saved as a negative z value
    assert gen_arr[v0[1], v0[0]] == -v0[2]
    assert gen_arr[v1[1], v1[0]] == -v1[2]
    assert gen_arr[v2[1], v2[0]] == -v2[2]

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
    v0 = np.array([639, 0, 2])
    v1 = np.array([639, 479, 6])
    v2 = np.array([0, 479, 5])

    gt_arr, gen_arr = await draw_polygon_on_screen(dut, v0, v1, v2)

    # Save rasterized images if desired
    if SAVE_IMAGE_OUTPUT == 1:
        plt.imsave(SAVED_IMAGE_PATH + 'gt_test_corner_bottom_right.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_test_corner_bottom_right.png', gen_arr)

    # Results will not be exactly the same due to floating point precision, should be within 20% of ground truth
    error = np.sqrt(np.mean(np.square((gt_arr - gen_arr))))
    dut._log.info("test_corner_bottom_right absolute error is " + str(error))
    if error > 0.2:
        assert 1 == 0

    # Corners should be the known ground truth values, note that the ray tracer core output is saved as a negative z value
    assert gen_arr[v0[1], v0[0]] == -v0[2]
    assert gen_arr[v1[1], v1[0]] == -v1[2]
    assert gen_arr[v2[1], v2[0]] == -v2[2]

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
    v0 = np.array([639, 479, 7])
    v1 = np.array([0, 479, 0])
    v2 = np.array([0, 0, 7])

    gt_arr, gen_arr = await draw_polygon_on_screen(dut, v0, v1, v2)

    # Save rasterized images if desired
    if SAVE_IMAGE_OUTPUT == 1:
        plt.imsave(SAVED_IMAGE_PATH + 'gt_test_corner_bottom_left.png', gt_arr)
        plt.imsave(SAVED_IMAGE_PATH + 'gen_test_corner_bottom_left.png', gen_arr)

    # Results will not be exactly the same due to floating point precision, should be within 20% of ground truth
    error = np.sqrt(np.mean(np.square((gt_arr - gen_arr))))
    dut._log.info("test_corner_bottom_left absolute error is " + str(error))
    if error > 0.2:
        assert 1 == 0

    # Corners should be the known ground truth values, note that the ray tracer core output is saved as a negative z value
    assert gen_arr[v0[1], v0[0]] == -v0[2]
    assert gen_arr[v1[1], v1[0]] == -v1[2]
    assert gen_arr[v2[1], v2[0]] == -v2[2]

    dut._log.info("Passed")
