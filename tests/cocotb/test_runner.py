import os
import shutil
from pathlib import Path

from cocotb_tools.runner import get_runner

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RTL = PROJECT_ROOT / "rtl"


def run_simulation(name, sources, top, test_module, parameters=None) -> None:
    simulator = os.getenv("SIM", "verilator")
    waves = os.getenv("WAVES") == "1"
    build_dir = PROJECT_ROOT / ".sim_build" / simulator / name
    runner = get_runner(simulator)

    # Verilator's generated makefiles default to ccache even when it is not installed.
    # Preserve an explicitly configured object cache, otherwise disable the missing wrapper.
    if simulator == "verilator" and "OBJCACHE" not in os.environ:
        if shutil.which("ccache") is None:
            os.environ["OBJCACHE"] = ""

    runner.build(
        sources=sources,
        hdl_toplevel=top,
        parameters=parameters or {},
        build_dir=build_dir,
        always=True,
        clean=True,
        timescale=("1ns", "1ps"),
        waves=waves,
    )
    runner.test(
        hdl_toplevel=top,
        test_module=test_module,
        test_dir=build_dir,
        build_dir=build_dir,
        waves=waves,
    )


def test_full_adder() -> None:
    run_simulation("full_adder", [RTL / "full_adder.sv"], "full_adder", "tb_full_adder")


def test_ripple_carry_adder() -> None:
    run_simulation(
        "ripple_carry_adder",
        [RTL / "full_adder.sv", RTL / "ripple_carry_adder.sv"],
        "ripple_carry_adder",
        "tb_ripple_carry_adder",
        {"WIDTH": 12},
    )


def test_shift_add_multiplier() -> None:
    run_simulation(
        "shift_add_multiplier",
        [
            RTL / "full_adder.sv",
            RTL / "ripple_carry_adder.sv",
            RTL / "shift_add_multiplier.sv",
        ],
        "shift_add_multiplier",
        "tb_shift_add_multiplier",
        {"WIDTH": 8},
    )


def test_top() -> None:
    run_simulation(
        "top",
        [
            RTL / "full_adder.sv",
            RTL / "ripple_carry_adder.sv",
            RTL / "shift_add_multiplier.sv",
            RTL / "q16_16_multiplier.sv",
            RTL / "top.sv",
        ],
        "top",
        "tb_top",
    )
