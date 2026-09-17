`timescale 1ns / 1ps
`default_nettype none

// TerosHDL extracts comments beginning with //! into its automatic
// documentation. Ordinary // comments remain implementation notes.
// Configure the marker in TerosHDL > Configuration > Documenter > General.
//! @title Documented SystemVerilog module
//! @author Kyle Ringor
//!
//! This example demonstrates focused documentation and RTL conventions for a
//! synchronous ready/valid processing block.
//!
//! ### Transaction behavior
//!
//! - An input transfer occurs when `valid_i` and `ready_o` are both asserted.
//! - The accepted word is shifted left for `COUNT_LIMIT` cycles.
//! - `valid_o` marks the cycle in which the completed word is available on `data_o`.
module style_guide #(
    parameter int unsigned DATA_WIDTH  = 8,  //! Width of the input and output words.
    parameter int unsigned RESET_VALUE = 0   //! Value loaded into data_o on reset.
) (
    //! Rising-edge clock for all sequential logic.
    input logic clk_i,
    //! Active-low asynchronous reset.
    input logic rst_ni,
    //! High when `data_i` contains an input word.
    input logic valid_i,
    //! Input word accepted when `valid_i` and `ready_o` are high.
    input logic [DATA_WIDTH-1:0] data_i,
    //! High when the block can accept an input word.
    output logic ready_o,
    //! High when `data_o` contains a completed output word.
    output logic valid_o,
    //! Output word associated with `valid_o`.
    output logic [DATA_WIDTH-1:0] data_o
);

    //! Number of processing cycles used by this teaching example.
    localparam int unsigned COUNT_LIMIT = 4;
    //! Number of bits required to represent the processing-cycle count.
    localparam int unsigned COUNT_WIDTH = $clog2(COUNT_LIMIT);

    //! Processing states: `STATE_IDLE` accepts input, `STATE_PROCESSING` shifts
    //! the stored word, and `STATE_DONE` presents the result.
    typedef enum logic [1:0] {
        STATE_IDLE       = 2'b00,
        STATE_PROCESSING = 2'b01,
        STATE_DONE       = 2'b10
    } state_t;

    // Flop-output _q / next-state _d naming makes signal timing explicit.
    //! Current finite-state-machine state.
    state_t state_q;
    //! Next finite-state-machine state.
    state_t state_d;
    //! Registered data word.
    logic [DATA_WIDTH-1:0] data_q;
    //! Next value of the registered data word.
    logic [DATA_WIDTH-1:0] data_d;
    //! Registered processing-cycle count.
    logic [COUNT_WIDTH-1:0] count_q;
    //! Next processing-cycle count.
    logic [COUNT_WIDTH-1:0] count_d;

    //! Computes next-state values and combinational outputs with defaults that
    //! prevent inferred latches.
    always_comb begin : p_next_state
        state_d = state_q;
        data_d  = data_q;
        count_d = count_q;
        ready_o = 1'b0;
        valid_o = 1'b0;

        case (state_q)
            STATE_IDLE: begin
                ready_o = 1'b1;
                if (valid_i) begin
                    data_d  = data_i;
                    count_d = '0;
                    state_d = STATE_PROCESSING;
                end
            end

            STATE_PROCESSING: begin
                count_d = count_q + 1'b1;
                data_d  = data_q << 1;

                if (count_q == COUNT_WIDTH'(COUNT_LIMIT - 1)) begin
                    state_d = STATE_DONE;
                end
            end

            STATE_DONE: begin
                valid_o = 1'b1;
                state_d = STATE_IDLE;
            end

            default: begin
                // Recover deterministically if the state register is corrupted.
                state_d = STATE_IDLE;
            end
        endcase
    end

    //! Registers state, data, and count values; driving `rst_ni` low returns the
    //! block asynchronously to its idle state.
    always_ff @(posedge clk_i or negedge rst_ni) begin : p_registers
        if (!rst_ni) begin
            state_q <= STATE_IDLE;
            data_q  <= DATA_WIDTH'(RESET_VALUE);
            count_q <= '0;
        end else begin
            state_q <= state_d;
            data_q  <= data_d;
            count_q <= count_d;
        end
    end

    // This continuous assignment keeps the output tied to registered storage.
    assign data_o = data_q;

    // Simulation-only parameter check; synthesis tools ignore this block.
    // synthesis translate_off
    initial begin
        assert (DATA_WIDTH > 0)
        else $fatal(1, "[%m] DATA_WIDTH must be greater than 0");
    end
    // synthesis translate_on

endmodule

`default_nettype wire
