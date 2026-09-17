import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

WIDTH = 8
MASK = (1 << (2 * WIDTH)) - 1


def signed(value, width=2 * WIDTH):
    value &= (1 << width) - 1
    return value - (1 << width) if value & (1 << (width - 1)) else value


async def sample(dut):
    await Timer(1, unit="ns")
    return {
        "in_ready": int(dut.in_ready.value),
        "out_valid": int(dut.out_valid.value),
        "product": signed(int(dut.product.value)),
    }


async def reset(dut):
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 0
    dut.operand_a.value = 0
    dut.operand_b.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0


async def launch(dut, a, b):
    assert (await sample(dut))["in_ready"] == 1
    dut.operand_a.value = a & ((1 << WIDTH) - 1)
    dut.operand_b.value = b & ((1 << WIDTH) - 1)
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    state = await sample(dut)
    assert state["in_ready"] == 0
    assert state["out_valid"] == 0


async def wait_exact_latency(dut, expected):
    for _ in range(WIDTH - 1):
        await RisingEdge(dut.clk)
        assert (await sample(dut))["out_valid"] == 0
    await RisingEdge(dut.clk)
    state = await sample(dut)
    assert state["out_valid"] == 1
    assert state["product"] == expected


async def consume(dut):
    dut.out_ready.value = 1
    await RisingEdge(dut.clk)
    dut.out_ready.value = 0
    state = await sample(dut)
    assert state["out_valid"] == 0
    assert state["in_ready"] == 1


@cocotb.test()
async def test_signed_products_latency_and_repeated_transactions(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    directed = [(0, 0), (1, -1), (-128, -1), (127, 127), (-128, 127), (-37, -11)]
    rng = random.Random(0x51A7)
    cases = directed + [(rng.randrange(-128, 128), rng.randrange(-128, 128)) for _ in range(80)]
    for a, b in cases:
        await launch(dut, a, b)
        await wait_exact_latency(dut, a * b)
        await consume(dut)


@cocotb.test()
async def test_busy_rejection_and_output_backpressure(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)
    await launch(dut, -23, 17)

    dut.in_valid.value = 1
    dut.operand_a.value = 99
    dut.operand_b.value = 99
    await wait_exact_latency(dut, -23 * 17)
    dut.in_valid.value = 0

    held = (await sample(dut))["product"]
    for _ in range(7):
        await RisingEdge(dut.clk)
        state = await sample(dut)
        assert state["out_valid"] == 1
        assert state["in_ready"] == 0
        assert state["product"] == held
    await consume(dut)


@cocotb.test()
async def test_reset_cancels_calculation_and_held_output(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)
    await launch(dut, 100, -100)
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    state = await sample(dut)
    assert state == {"in_ready": 1, "out_valid": 0, "product": 0}
    dut.rst.value = 0

    await launch(dut, -128, -128)
    await wait_exact_latency(dut, 16384)
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    state = await sample(dut)
    assert state == {"in_ready": 1, "out_valid": 0, "product": 0}
