.DEFAULT_GOAL := help

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

RTL_DIR ?= rtl
RTL_PATTERN ?= *.sv
SIM ?= verilator
COCOTB_RUNNER ?= tests/cocotb/test_runner.py
DOCS_MODULE ?= tools.generate_docs
UV ?= uv
UV_RUN ?= $(UV) run --frozen
UV_SYNC ?= $(UV) sync --frozen
PYTEST ?= $(UV_RUN) pytest
VERIBLE_FORMAT_ARGS ?= --indentation_spaces=4 --column_limit=100
VERILATOR_LINT_ARGS ?= --lint-only --Wall

RTL_PKG := $(shell find $(RTL_DIR) -type f -name '*_pkg.sv' -print | LC_ALL=C sort)
RTL_MOD := $(shell find $(RTL_DIR) -type f -name '$(RTL_PATTERN)' ! -name '*_pkg.sv' -print | LC_ALL=C sort)
RTL := $(RTL_PKG) $(RTL_MOD)

.PHONY: help setup format check test waves docs ci

help:
	@awk 'BEGIN { FS = ":.*## "; print "Available commands:" } /^[A-Za-z0-9_-]+:.*## / { printf "  make %-16s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

setup:
	$(UV_SYNC)

format: ## Format Python and SystemVerilog sources
	$(UV_RUN) ruff format .
	verible-verilog-format --inplace $(VERIBLE_FORMAT_ARGS) $(RTL)

check: ## Run lint, formatting, tooling tests, and documentation checks
	$(UV_RUN) ruff check .
	verilator $(VERILATOR_LINT_ARGS) $(RTL)
	$(UV_RUN) ruff format --check .
	@for source in $(RTL); do \
		verible-verilog-format --verify $(VERIBLE_FORMAT_ARGS) "$$source"; \
	done
	SIM=$(SIM) $(PYTEST)
	$(UV_RUN) python -m $(DOCS_MODULE) --check

test: ## Run the cocotb simulations with the configured simulator
	SIM=$(SIM) $(PYTEST) $(COCOTB_RUNNER)

waves: ## Run the cocotb simulations and generate waveforms
	WAVES=1 SIM=$(SIM) $(PYTEST) $(COCOTB_RUNNER)

docs: ## Generate TeroHDL documentation
	$(UV_RUN) python -m $(DOCS_MODULE)

ci:
	$(UV) lock --check
	$(MAKE) setup
	$(MAKE) check
