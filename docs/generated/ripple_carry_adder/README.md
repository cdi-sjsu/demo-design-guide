
# Entity: ripple_carry_adder 
- **File**: ripple_carry_adder.sv
- **Title:**  Ripple Carry Adder
- **Author:**  Kyle Ringor

## Diagram
![Diagram](ripple_carry_adder.svg "Diagram")
## Description


A parametrizable combinational adder built as a generated chain of one-bit full adders.

## Generics

| Generic name | Type         | Value | Description |
| ------------ | ------------ | ----- | ----------- |
| WIDTH        | int unsigned | 16    |             |

## Ports

| Port name | Direction | Type               | Description  |
| --------- | --------- | ------------------ | ------------ |
| a_i       | input     | wire [WIDTH - 1:0] | First input  |
| b_i       | input     | wire [WIDTH - 1:0] | Second input |
| cin_i     | input     | wire               | Carry in     |
| sum_o     | output    | [WIDTH - 1:0]      | Sum          |
| cout_o    | output    |                    | Carry out    |

## Signals

| Name  | Type            | Description |
| ----- | --------------- | ----------- |
| carry | logic [WIDTH:0] |             |
