`timescale 1ns / 1ps
`default_nettype none

//! @title Ripple Carry Adder
//! @author Kyle Ringor
//!
//! A parametrizable combinational adder built as a generated chain of one-bit full adders.
module ripple_carry_adder #(
    parameter int unsigned WIDTH = 16
) (
    input wire [WIDTH - 1:0] a_i,  //! First input
    input wire [WIDTH - 1:0] b_i,  //! Second input
    input wire cin_i,  //! Carry in
    output logic [WIDTH - 1:0] sum_o,  //! Sum
    output logic cout_o  //! Carry out
);

    logic [WIDTH:0] carry;
    assign carry[0] = cin_i;
    assign cout_o   = carry[WIDTH];

    genvar i;
    generate
        for (i = 0; i < WIDTH; i = i + 1) begin : g_rca_i
            full_adder u_full_adder (
                .a_i(a_i[i]),
                .b_i(b_i[i]),
                .cin_i(carry[i]),
                .sum_o(sum_o[i]),
                .cout_o(carry[i+1])
            );
        end
    endgenerate

endmodule

`default_nettype wire
