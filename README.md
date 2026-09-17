# Demo Design Guide: Q16.16 Multiplier

This repository serves as a CDI SJSU reference demo design guide, implementing a signed Q16.16 fixed-point multiplier in SystemVerilog with
layered Cocotb verification, strict Verilator and Verible quality gates, and TeroHDL project
integration with Yosys-backed schematic visualization. The design is structural and iterative: a
one-bit full adder builds a ripple-carry adder, which supplies the accumulation adder in a radix-2
shift-and-add multiplier.

## Quick start

### Required Dev Container

This project must be opened in its Dev Container. The container provides the required HDL tools,
Python dependencies, and VS Code extensions.

1. Install [Visual Studio Code](https://code.visualstudio.com/). Then install the
   [Dev Containers extension][dev-containers-extension].
2. Prepare the container runtime for your operating system:
   - **macOS:** Install
     [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/), then open
     Docker Desktop and wait for it to start.
   - **Windows:** Continue to the next step. The Dev Containers extension will guide you through
     installing [WSL 2][install-wsl], Ubuntu, and Docker inside WSL when you reopen the project in
     its container. Docker Desktop is not required for this setup.
3. Clone this repository and open its folder in VS Code.
4. When VS Code detects `.devcontainer/devcontainer.json`, select **Reopen in Container** in the
   notification. If the notification is no longer visible, open the Command Palette and run
   **Dev Containers: Reopen in Container**.

   Open the Command Palette from **View > Command Palette**, with `F1`, with `Shift+Command+P` on
   macOS, or with `Ctrl+Shift+P` on Windows.
5. On a new Windows setup, follow all prompts, restart Windows when requested, and finish Ubuntu's
   first-run setup. Then return to VS Code and reopen the project in its container.
6. After VS Code finishes building and opening the container, run `make` to see all available
   workflows.

```sh
make
```

### Key Workflows

- `make check`: Run the complete quality gate (Python format & lint via Ruff, Verilator `-Wall` lint, Verible format verify, Cocotb simulations with full coverage assertion, and TerosHDL documentation manifest check).
- `make test`: Run the Cocotb test suites across all hierarchy levels with Verilator.
- `make waves`: Run simulations and generate VCD waveform traces for inspection in Surfer. The
  full-design trace is `.sim_build/verilator/top/dump.vcd`.
- `make format`: Format all Python sources (Ruff) and SystemVerilog files (Verible).
- `make docs`: Regenerate HTML, Markdown, and interface SVG documentation via TerosHDL.

### TeroHDL project

The Dev Container includes TeroHDL and its dependencies. To load the design into TeroHDL:

1. Select the TeroHDL icon in the VS Code Activity Bar.
2. Under **Projects**, select **Add Project**.
3. Select **Load project from YAML EDAM**.
4. In the file picker, select `edam.yml` from the repository root, then select
   **Select YAML EDAM files**.
5. Select `q16x16_multiplier` to make it the current project. Its name turns green, all five RTL
   files appear under **Files**, and `top` appears as the selected top level under **Hierarchy**.
6. Open the **Dependency Viewer** to see the complete module hierarchy from `top` through
   `full_adder`.
