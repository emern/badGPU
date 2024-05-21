"""
Testbench for inverse determinant functionality

"""

# SPDX-FileCopyrightText: Emery Nagy
# SPDX-License-Identifier: MIT

import cocotb
import cocotb.binary
from cocotb.triggers import Timer
import numpy as np
from fxpmath import Fxp


def gt_estimation(val, log=False):
    """
    Calculate reciprocal estimation based on algorithm found in https://observablehq.com/@drom/reciprocal-approximation
    """
    shifted = val
    amount = 0
    negative = False

    # Check input sign
    if val < 0:
        negative = True
        shifted = val * -1

    # Normalize input to range [0.5, 1]
    while shifted > 1:
        shifted = shifted / 2
        amount+=1

    # Funky operations with magic numbers
    a = shifted
    b = 1.466 - a
    c = a * b
    d = 1.0012 - c
    e = d * b
    reciprocal = e * 4

    if log == True:
        print("--Ground truth--")
        print(a)
        print(b)
        print(c)
        print(d)
        print(e)
        print(reciprocal)
        print(amount)
        print(reciprocal / (1 << amount))

    # Re-apply sign
    if negative == True:
        reciprocal = -1 * reciprocal

    # Shift output to desired range
    return reciprocal / (1 << amount)


def fixed_to_floating(val, fractional_bits):
    """
    Convert fixed point string into floating point number
    """
    c = abs(val)
    sign = 1 
    if val < 0:
        # convert back from two's complement
        c = val - 1 
        c = ~c
        sign = -1
    f = (1.0 * c) / (2 ** fractional_bits)
    f = f * sign
    return f

def print_internal_state(dut):
    """
    Print ray tracer core internal state for debugging
    """

    print("--Core internals--")

    print(fixed_to_floating(dut.user_project.a.value.signed_integer, 23))
    print(fixed_to_floating(dut.user_project.b.value.signed_integer, 23))
    print(fixed_to_floating(dut.user_project.c.value.signed_integer, 46))
    print(fixed_to_floating(dut.user_project.d.value.signed_integer, 23))
    print(fixed_to_floating(dut.user_project.e.value.signed_integer, 46))
    print(fixed_to_floating(dut.user_project.f.value.signed_integer, 23))
    print(fixed_to_floating(dut.user_project.inv_det_full.value.signed_integer, 23))
    print(fixed_to_floating(dut.inv_det.value.integer, 23))


@cocotb.test()
async def test_number_1(dut):
    """
    Test on a realistic number
    """
    dut._log.info("Start")

    test_val = 3072

    # Set input determinant
    dut.determinant.value = test_val

    # Calculate ground truth
    gt = 1./test_val
    estimation = gt_estimation(test_val)

    await Timer(40, units="ns")

    # Log result
    dut._log.info("Ground truth: " + str(gt))
    dut._log.info("Ground truth estimate: " + str(estimation))
    dut._log.info("DUT result: " + str(fixed_to_floating(dut.inv_det.value.integer, 23)))

    # Result should be within 20% of actual, appropriate sign
    assert abs(fixed_to_floating(dut.inv_det.value.integer, 23) - abs(gt)) / abs(gt) < 0.2
    assert dut.inv_det_negative.value.integer == 0

    dut._log.info("Finished")


@cocotb.test()
async def test_number_2(dut):
    """
    Test on a negative number
    """
    dut._log.info("Start")

    test_val = -3072

    # Set input determinant
    dut.determinant.value = test_val

    # Calculate ground truth
    gt = 1./test_val
    estimation = gt_estimation(test_val)

    await Timer(40, units="ns")

    # Log result
    dut._log.info("Ground truth: " + str(gt))
    dut._log.info("Ground truth estimate: " + str(estimation))
    dut._log.info("DUT result: " + str(fixed_to_floating(dut.inv_det.value.integer, 23)))

    # Result should be within 20% of actual, appropriate sign
    assert abs(fixed_to_floating(dut.inv_det.value.integer, 23) - abs(gt)) / abs(gt) < 0.2
    assert dut.inv_det_negative.value.integer == 1

    dut._log.info("Finished")


@cocotb.test()
async def test_number_3(dut):
    """
    Test on the smallest possible input value
    """
    dut._log.info("Start")

    test_val = 10

    # Set input determinant
    dut.determinant.value = test_val

    # Calculate ground truth
    gt = 1./test_val
    estimation = gt_estimation(test_val)

    await Timer(40, units="ns")

    # Log result
    dut._log.info("Ground truth: " + str(gt))
    dut._log.info("Ground truth estimate: " + str(estimation))
    dut._log.info("DUT result: " + str(fixed_to_floating(dut.inv_det.value.integer, 23)))

    # Result should be within 20% of actual, appropriate sign
    assert abs(fixed_to_floating(dut.inv_det.value.integer, 23) - abs(gt)) / abs(gt) < 0.2
    assert dut.inv_det_negative.value.integer == 0

    dut._log.info("Finished")


@cocotb.test()
async def test_number_4(dut):
    """
    Test on the smallest possible negative input value
    """
    dut._log.info("Start")

    test_val = -10

    # Set input determinant
    dut.determinant.value = test_val

    # Calculate ground truth
    gt = 1./test_val
    estimation = gt_estimation(test_val)

    await Timer(40, units="ns")

    # Log result
    dut._log.info("Ground truth: " + str(gt))
    dut._log.info("Ground truth estimate: " + str(estimation))
    dut._log.info("DUT result: " + str(fixed_to_floating(dut.inv_det.value.integer, 23)))

    # Result should be within 20% of actual, appropriate sign
    assert abs(fixed_to_floating(dut.inv_det.value.integer, 23) - abs(gt)) / abs(gt) < 0.2
    assert dut.inv_det_negative.value.integer == 1

    dut._log.info("Finished")


@cocotb.test()
async def test_number_5(dut):
    """
    Test on the largest possible input value
    """
    dut._log.info("Start")

    # Technically it wouldn't be possible to hit this value as long as we have 3 proper triangle vertices but ideally the hardware should support this
    test_val = 64*48

    # Set input determinant
    dut.determinant.value = test_val

    # Calculate ground truth
    gt = 1./test_val
    estimation = gt_estimation(test_val)

    await Timer(40, units="ns")

    # Log result
    dut._log.info("Ground truth: " + str(gt))
    dut._log.info("Ground truth estimate: " + str(estimation))
    dut._log.info("DUT result: " + str(fixed_to_floating(dut.inv_det.value.integer, 23)))

    # Result should be within 20% of actual, appropriate sign
    assert abs(fixed_to_floating(dut.inv_det.value.integer, 23) - abs(gt)) / abs(gt) < 0.2
    assert dut.inv_det_negative.value.integer == 0

    dut._log.info("Finished")


@cocotb.test()
async def test_number_6(dut):
    """
    Test on the largest possible negative input value
    """
    dut._log.info("Start")

    # Technically it wouldn't be possible to hit this value as long as we have 3 proper triangle vertices but ideally the hardware should support this
    test_val = -64*48

    # Set input determinant
    dut.determinant.value = test_val

    # Calculate ground truth
    gt = 1./test_val
    estimation = gt_estimation(test_val)

    await Timer(40, units="ns")

    # Log result
    dut._log.info("Ground truth: " + str(gt))
    dut._log.info("Ground truth estimate: " + str(estimation))
    dut._log.info("DUT result: " + str(fixed_to_floating(dut.inv_det.value.integer, 23)))

    # Result should be within 20% of actual, appropriate sign
    assert abs(fixed_to_floating(dut.inv_det.value.integer, 23) - abs(gt)) / abs(gt) < 0.2
    assert dut.inv_det_negative.value.integer == 1

    dut._log.info("Finished")