`timescale 1ns / 1ps
`default_nettype none

//! @title Q16.16 Multiplier
//! @author Kyle Ringor
//!
//! Fixed-width public wrapper for signed Q16.16 multiplication. The core produces a signed
//! Q32.32 product after 32 calculation cycles. This wrapper arithmetically shifts that product
//! right by 16 bits, which truncates negative fractions toward negative infinity, then saturates
//! values outside the signed 32-bit Q16.16 range and asserts overflow.
module q16_16_multiplier (
    input wire clk,  //! Clock
    input wire rst,  //! Synchronous active-high reset
    input wire in_valid,  //! Input operands are valid
    output logic in_ready,  //! Multiplier can accept the operands
    input wire signed [31:0] operand_a,  //! First signed Q16.16 operand
    input wire signed [31:0] operand_b,  //! Second signed Q16.16 operand
    output logic out_valid,  //! Result and overflow are valid
    input wire out_ready,  //! Consumer can accept the result
    output logic signed [31:0] result,  //! Saturated signed Q16.16 result
    output logic overflow  //! Rescaled product exceeded the Q16.16 range
);

    localparam int unsigned                       Q_WIDTH         = 32;
    localparam int unsigned                       Q_FRAC_WIDTH    = 16;
    localparam int unsigned                       Q_PRODUCT_WIDTH = 2 * Q_WIDTH;
    localparam logic signed [Q_PRODUCT_WIDTH-1:0] MAX_Q16_16      = 64'sh0000_0000_7fff_ffff;
    localparam logic signed [Q_PRODUCT_WIDTH-1:0] MIN_Q16_16      = -64'sh0000_0000_8000_0000;
    localparam logic signed [        Q_WIDTH-1:0] SAT_POS         = 32'sh7fff_ffff;
    localparam logic signed [        Q_WIDTH-1:0] SAT_NEG         = -32'sh8000_0000;

    logic signed [Q_PRODUCT_WIDTH-1:0] exact_product;
    logic signed [Q_PRODUCT_WIDTH-1:0] scaled_product;

    shift_add_multiplier #(
        .WIDTH(Q_WIDTH)
    ) u_multiplier (
        .clk(clk),
        .rst(rst),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .operand_a(operand_a),
        .operand_b(operand_b),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .product(exact_product)
    );

    always_comb begin
        scaled_product = exact_product >>> Q_FRAC_WIDTH;
        overflow       = 1'b0;
        if (scaled_product > MAX_Q16_16) begin
            result   = SAT_POS;
            overflow = 1'b1;
        end else if (scaled_product < MIN_Q16_16) begin
            result   = SAT_NEG;
            overflow = 1'b1;
        end else begin
            result = scaled_product[Q_WIDTH-1:0];
        end
    end

`ifndef SYNTHESIS
    // SVA protocol verification
    // Outputs must remain stable during backpressure (when out_valid && !out_ready)
    property p_output_stable_under_backpressure;
        @(posedge clk) disable iff (rst) (out_valid && !out_ready) |=> (out_valid && $stable(
            result
        ) && $stable(
            overflow
        ));
    endproperty
    a_output_stable_under_backpressure :
    assert property (p_output_stable_under_backpressure)
    else $error("[%m] Output changed during backpressure!");
`endif

endmodule

`default_nettype wire
