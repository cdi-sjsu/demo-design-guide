import random

import cocotb
from cocotb.triggers import Timer

WIDTH = 12
MASK = (1 << WIDTH) - 1


async def check_addition(dut, a, b, carry_in):
    dut.a_i.value = a
    dut.b_i.value = b
    dut.cin_i.value = carry_in
    await Timer(1, unit="ns")

    expected = a + b + carry_in
    assert int(dut.sum_o.value) == (expected & MASK)
    assert int(dut.cout_o.value) == ((expected >> WIDTH) & 1)


@cocotb.test()
async def test_ripple_carry_adder_directed_and_random(dut):
    """Verify carry propagation, wraparound, and fixed-seed random additions."""
    directed = [
        (0, 0, 0),
        (0, 0, 1),
        (MASK, 0, 0),
        (MASK, 0, 1),
        (MASK, MASK, 0),
        (0x555, 0xAAA, 1),
        (1 << (WIDTH - 1), 1 << (WIDTH - 1), 0),
    ]
    for values in directed:
        await check_addition(dut, *values)

    rng = random.Random(0xADD3)
    for _ in range(500):
        await check_addition(
            dut,
            rng.randrange(1 << WIDTH),
            rng.randrange(1 << WIDTH),
            rng.randrange(2),
        )
