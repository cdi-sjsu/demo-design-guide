`timescale 1ns / 1ps
`default_nettype none

//! @title Signed Shift-and-Add Multiplier
//! @author Kyle Ringor
//!
//! A reusable signed multiplier that accepts one transaction through a ready/valid input,
//! performs one unsigned-magnitude radix-2 iteration per cycle, and returns the exact signed
//! double-width product. The output remains valid and stable until it is accepted. A new input
//! is accepted no earlier than the cycle after the preceding output transfer.
module shift_add_multiplier #(
    parameter int unsigned WIDTH = 32
) (
    input wire clk,  //! Clock
    input wire rst,  //! Synchronous active-high reset
    input wire in_valid,  //! Input operands are valid
    output logic in_ready,  //! Core can accept an input transaction
    input wire signed [WIDTH - 1:0] operand_a,  //! First signed integer operand
    input wire signed [WIDTH - 1:0] operand_b,  //! Second signed integer operand
    output logic out_valid,  //! Exact product is valid
    input wire out_ready,  //! Consumer can accept the product
    output logic signed [(2 * WIDTH) - 1:0] product  //! Exact signed product
);

    localparam int unsigned PRODUCT_WIDTH = 2 * WIDTH;
    localparam int unsigned COUNT_WIDTH   = (WIDTH > 1) ? $clog2(WIDTH) : 1;

    typedef enum logic [1:0] {
        IDLE,
        CALCULATE,
        OUTPUT_VALID
    } state_t;

    state_t state;
    logic [COUNT_WIDTH - 1:0] iteration;
    logic result_negative;
    logic [PRODUCT_WIDTH - 1:0] accumulator;
    logic [PRODUCT_WIDTH - 1:0] multiplicand;
    logic [WIDTH - 1:0] multiplier;
    logic [PRODUCT_WIDTH - 1:0] addend;
    logic [PRODUCT_WIDTH - 1:0] adder_sum;
    logic adder_carry;
    logic [WIDTH - 1:0] magnitude_a;
    logic [WIDTH - 1:0] magnitude_b;

    assign in_ready = (state == IDLE);
    assign out_valid = (state == OUTPUT_VALID);
    assign magnitude_a = operand_a[WIDTH-1] ? (~operand_a + 1'b1) : operand_a;
    assign magnitude_b = operand_b[WIDTH-1] ? (~operand_b + 1'b1) : operand_b;
    assign addend = multiplier[0] ? multiplicand : '0;

    ripple_carry_adder #(
        .WIDTH(PRODUCT_WIDTH)
    ) u_accumulator_adder (
        .a_i(accumulator),
        .b_i(addend),
        .cin_i(1'b0),
        .sum_o(adder_sum),
        .cout_o(adder_carry)
    );

    always_ff @(posedge clk) begin
        if (rst) begin
            state           <= IDLE;
            iteration       <= '0;
            result_negative <= 1'b0;
            accumulator     <= '0;
            multiplicand    <= '0;
            multiplier      <= '0;
            product         <= '0;
        end else begin
            case (state)
                IDLE: begin
                    if (in_valid) begin
                        iteration       <= '0;
                        result_negative <= operand_a[WIDTH-1] ^ operand_b[WIDTH-1];
                        accumulator     <= '0;
                        multiplicand    <= {{WIDTH{1'b0}}, magnitude_a};
                        multiplier      <= magnitude_b;
                        state           <= CALCULATE;
                    end
                end

                CALCULATE: begin
                    accumulator  <= adder_sum;
                    multiplicand <= multiplicand << 1;
                    multiplier   <= multiplier >> 1;
                    assert (!adder_carry);
                    if (iteration == COUNT_WIDTH'(WIDTH - 1)) begin
                        if (result_negative) begin
                            product <= $signed(~adder_sum + 1'b1);
                        end else begin
                            product <= $signed(adder_sum);
                        end
                        state <= OUTPUT_VALID;
                    end else begin
                        iteration <= iteration + 1'b1;
                    end
                end

                OUTPUT_VALID: begin
                    if (out_ready) begin
                        state <= IDLE;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

`ifndef SYNTHESIS
    initial begin
        assert (WIDTH > 0)
        else $fatal(1, "[%m] WIDTH must be greater than 0");
    end

    // SVA protocol verification
    // Product must remain stable while backpressured
    property p_product_stable_under_backpressure;
        @(posedge clk) disable iff (rst) (out_valid && !out_ready) |=> (out_valid && $stable(
            product
        ));
    endproperty
    a_product_stable_under_backpressure :
    assert property (p_product_stable_under_backpressure)
    else $error("[%m] Product changed during backpressure!");
`endif

endmodule

`default_nettype wire
