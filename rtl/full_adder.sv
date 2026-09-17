`timescale 1ns / 1ps
`default_nettype none

//! @title Full Adder
//! @author Kyle Ringor
//!
//! One-bit combinational full adder used as the primitive for the structural adder chain.
module full_adder (
    input  wire  a_i,    //! First input
    input  wire  b_i,    //! Second input
    input  wire  cin_i,  //! Carry in
    output logic sum_o,  //! Sum
    output logic cout_o  //! Carry out
);

    assign sum_o  = a_i ^ b_i ^ cin_i;
    assign cout_o = (a_i & b_i) | (b_i & cin_i) | (a_i & cin_i);

endmodule

`default_nettype wire
