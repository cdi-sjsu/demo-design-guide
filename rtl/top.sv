`timescale 1ns / 1ps
`default_nettype none

//! @title Q16.16 Multiplier Top
//! @author Kyle Ringor
//!
//! Repository-level wrapper around the reusable Q16.16 multiplier core.
module top (
    input wire clk,  //! Clock
    input wire rst,  //! Synchronous active-high reset
    input wire in_valid,  //! Input operands are valid
    output wire in_ready,  //! Multiplier can accept the operands
    input wire signed [31:0] operand_a,  //! First signed Q16.16 operand
    input wire signed [31:0] operand_b,  //! Second signed Q16.16 operand
    output wire out_valid,  //! Result and overflow are valid
    input wire out_ready,  //! Consumer can accept the result
    output wire signed [31:0] result,  //! Saturated signed Q16.16 result
    output wire overflow  //! Rescaled product exceeded the Q16.16 range
);

    q16_16_multiplier u_q16_16_multiplier (
        .clk(clk),
        .rst(rst),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .operand_a(operand_a),
        .operand_b(operand_b),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .result(result),
        .overflow(overflow)
    );

endmodule

`default_nettype wire
