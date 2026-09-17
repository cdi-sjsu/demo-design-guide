
# Entity: top 
- **File**: top.sv
- **Title:**  Q16.16 Multiplier Top
- **Author:**  Kyle Ringor

## Diagram
![Diagram](top.svg "Diagram")
## Description


Repository-level wrapper around the reusable Q16.16 multiplier core.

## Ports

| Port name | Direction | Type               | Description                                |
| --------- | --------- | ------------------ | ------------------------------------------ |
| clk       | input     | wire               | Clock                                      |
| rst       | input     | wire               | Synchronous active-high reset              |
| in_valid  | input     | wire               | Input operands are valid                   |
| in_ready  | output    | wire               | Multiplier can accept the operands         |
| operand_a | input     | wire signed [31:0] | First signed Q16.16 operand                |
| operand_b | input     | wire signed [31:0] | Second signed Q16.16 operand               |
| out_valid | output    | wire               | Result and overflow are valid              |
| out_ready | input     | wire               | Consumer can accept the result             |
| result    | output    | wire signed [31:0] | Saturated signed Q16.16 result             |
| overflow  | output    | wire               | Rescaled product exceeded the Q16.16 range |

## Instantiations

- u_q16_16_multiplier: q16_16_multiplier
