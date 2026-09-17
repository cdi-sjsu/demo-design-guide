
# Entity: q16_16_multiplier 
- **File**: q16_16_multiplier.sv
- **Title:**  Q16.16 Multiplier
- **Author:**  Kyle Ringor

## Diagram
![Diagram](q16_16_multiplier.svg "Diagram")
## Description


Fixed-width public wrapper for signed Q16.16 multiplication. The core produces a signed
Q32.32 product after 32 calculation cycles. This wrapper arithmetically shifts that product
right by 16 bits, which truncates negative fractions toward negative infinity, then saturates
values outside the signed 32-bit Q16.16 range and asserts overflow.

## Ports

| Port name | Direction | Type               | Description                                |
| --------- | --------- | ------------------ | ------------------------------------------ |
| clk       | input     | wire               | Clock                                      |
| rst       | input     | wire               | Synchronous active-high reset              |
| in_valid  | input     | wire               | Input operands are valid                   |
| in_ready  | output    |                    | Multiplier can accept the operands         |
| operand_a | input     | wire signed [31:0] | First signed Q16.16 operand                |
| operand_b | input     | wire signed [31:0] | Second signed Q16.16 operand               |
| out_valid | output    |                    | Result and overflow are valid              |
| out_ready | input     | wire               | Consumer can accept the result             |
| result    | output    | [31:0]             | Saturated signed Q16.16 result             |
| overflow  | output    |                    | Rescaled product exceeded the Q16.16 range |

## Signals

| Name           | Type                               | Description |
| -------------- | ---------------------------------- | ----------- |
| exact_product  | logic signed [Q_PRODUCT_WIDTH-1:0] |             |
| scaled_product | logic signed [Q_PRODUCT_WIDTH-1:0] |             |

## Constants

| Name            | Type | Value                     | Description |
| --------------- | ---- | ------------------------- | ----------- |
| Q_WIDTH         |      | 32                        |             |
| Q_FRAC_WIDTH    |      | 16                        |             |
| Q_PRODUCT_WIDTH |      | 2 * Q_WIDTH               |             |
| MAX_Q16_16      |      | 64'sh0000_0000_7fff_ffff  |             |
| MIN_Q16_16      |      | -64'sh0000_0000_8000_0000 |             |
| SAT_POS         |      | 32'sh7fff_ffff            |             |
| SAT_NEG         |      | -32'sh8000_0000           |             |

## Processes
- unnamed: (  )
  - **Type:** always_comb

## Instantiations

- u_multiplier: shift_add_multiplier
