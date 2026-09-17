import itertools

import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_full_adder_truth_table(dut):
    """Exhaustively verify all eight one-bit full-adder input combinations."""
    for a, b, carry_in in itertools.product(range(2), repeat=3):
        dut.a_i.value = a
        dut.b_i.value = b
        dut.cin_i.value = carry_in
        await Timer(1, unit="ns")

        total = a + b + carry_in
        assert int(dut.sum_o.value) == (total & 1)
        assert int(dut.cout_o.value) == (total >> 1)
