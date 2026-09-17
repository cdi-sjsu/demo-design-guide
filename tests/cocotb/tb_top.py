import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

WIDTH = 32
MINIMUM = -(1 << 31)
MAXIMUM = (1 << 31) - 1
MASK = (1 << WIDTH) - 1


def to_signed(value, width=WIDTH):
    value &= (1 << width) - 1
    return value - (1 << width) if value & (1 << (width - 1)) else value


def reference(a, b):
    scaled = (a * b) >> 16
    if scaled > MAXIMUM:
        return MAXIMUM, 1
    if scaled < MINIMUM:
        return MINIMUM, 1
    return scaled, 0


class FunctionalCoverage:
    """Tracks coverage of operand quadrants, saturation modes, and protocol backpressure."""

    def __init__(self):
        self.quadrants = {
            "pos_pos": 0,
            "pos_neg": 0,
            "neg_pos": 0,
            "neg_neg": 0,
            "zero": 0,
        }
        self.saturation = {
            "none": 0,
            "pos_saturation": 0,
            "neg_saturation": 0,
        }
        self.backpressure_cycles = {0: 0, 1: 0, 2: 0, "3_or_more": 0}
        self.corners = {
            "max_pos": 0,
            "min_neg": 0,
            "one_pos": 0,
            "one_neg": 0,
        }

    def sample(self, a, b, result, overflow, hold_cycles):
        if a == 0 or b == 0:
            self.quadrants["zero"] += 1
        elif a > 0 and b > 0:
            self.quadrants["pos_pos"] += 1
        elif a > 0 and b < 0:
            self.quadrants["pos_neg"] += 1
        elif a < 0 and b > 0:
            self.quadrants["neg_pos"] += 1
        else:
            self.quadrants["neg_neg"] += 1

        if overflow:
            if result == MAXIMUM:
                self.saturation["pos_saturation"] += 1
            elif result == MINIMUM:
                self.saturation["neg_saturation"] += 1
        else:
            self.saturation["none"] += 1

        if hold_cycles in (0, 1, 2):
            self.backpressure_cycles[hold_cycles] += 1
        else:
            self.backpressure_cycles["3_or_more"] += 1

        if a == MAXIMUM or b == MAXIMUM:
            self.corners["max_pos"] += 1
        if a == MINIMUM or b == MINIMUM:
            self.corners["min_neg"] += 1
        if a == 0x0001_0000 or b == 0x0001_0000:
            self.corners["one_pos"] += 1
        if a == -0x0001_0000 or b == -0x0001_0000:
            self.corners["one_neg"] += 1

    def assert_full_coverage(self):
        for category, bins in [
            ("Quadrants", self.quadrants),
            ("Saturation", self.saturation),
            ("Backpressure", self.backpressure_cycles),
            ("Corners", self.corners),
        ]:
            for bin_name, count in bins.items():
                assert count > 0, f"Uncovered functional bin: {category}['{bin_name}']"


coverage = FunctionalCoverage()


async def sample(dut):
    await Timer(1, unit="ns")
    return (
        int(dut.in_ready.value),
        int(dut.out_valid.value),
        to_signed(int(dut.result.value)),
        int(dut.overflow.value),
    )


async def reset(dut):
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 0
    dut.operand_a.value = 0
    dut.operand_b.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert await sample(dut) == (1, 0, 0, 0)
    dut.rst.value = 0


async def multiply(dut, a, b, hold_cycles=0):
    assert (await sample(dut))[0] == 1
    dut.operand_a.value = a & MASK
    dut.operand_b.value = b & MASK
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    assert (await sample(dut))[:2] == (0, 0)

    for _ in range(WIDTH - 1):
        await RisingEdge(dut.clk)
        assert (await sample(dut))[1] == 0
    await RisingEdge(dut.clk)
    state = await sample(dut)
    assert state[1] == 1
    assert state[2:] == reference(a, b)
    coverage.sample(a, b, state[2], state[3], hold_cycles)

    for _ in range(hold_cycles):
        await RisingEdge(dut.clk)
        assert await sample(dut) == state

    dut.out_ready.value = 1
    await RisingEdge(dut.clk)
    dut.out_ready.value = 0
    assert (await sample(dut))[:2] == (1, 0)


@cocotb.test()
async def test_q16_16_boundaries_saturation_and_truncation(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    cases = [
        (0, MAXIMUM),
        (0x0001_0000, 0x0001_0000),
        (-0x0001_0000, 0x0001_0000),
        (0x0000_8000, 0x0000_8000),
        (-1, 1),
        (-0x0000_8001, 0x0000_8000),
        (MAXIMUM, 0x0001_0000),
        (MINIMUM, 0x0001_0000),
        (MAXIMUM, MAXIMUM),
        (MINIMUM, MINIMUM),
        (MINIMUM, MAXIMUM),
    ]
    for index, values in enumerate(cases):
        await multiply(dut, *values, hold_cycles=index % 4)


@cocotb.test()
async def test_q16_16_fixed_seed_random_and_busy_input(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)
    rng = random.Random(0x1616)

    for _ in range(100):
        a = rng.randrange(MINIMUM, MAXIMUM + 1)
        b = rng.randrange(MINIMUM, MAXIMUM + 1)
        await multiply(dut, a, b, hold_cycles=rng.randrange(3))

    dut.operand_a.value = 0x0002_0000
    dut.operand_b.value = 0x0003_0000
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    dut.operand_a.value = 0x0100_0000
    dut.operand_b.value = 0x0100_0000
    for _ in range(WIDTH):
        await RisingEdge(dut.clk)
    state = await sample(dut)
    assert state[2:] == (0x0006_0000, 0)
    dut.in_valid.value = 0
    coverage.assert_full_coverage()


@cocotb.test()
async def test_q16_16_reset_cancellation(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)
    dut.operand_a.value = MAXIMUM
    dut.operand_b.value = MAXIMUM
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    for _ in range(12):
        await RisingEdge(dut.clk)
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    assert await sample(dut) == (1, 0, 0, 0)
    dut.rst.value = 0

    dut.operand_a.value = 0x0001_0000
    dut.operand_b.value = 0x0002_0000
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    for _ in range(WIDTH):
        await RisingEdge(dut.clk)
    assert (await sample(dut))[1] == 1
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    assert await sample(dut) == (1, 0, 0, 0)
