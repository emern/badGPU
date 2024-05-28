/*
 * Copyright (c) 2024 Emery Nagy
 * SPDX-License-Identifier: Apache-2.0
 */

// Build design using Quartus 2 for Cyclone V FPGA

`default_nettype none

module quartus_top (
    input [3:0] KEY,
    output [9:0] LEDR,
    input CLOCK_50,
    input [35:0] GPIO_0,
    output [35:0] GPIO_1,
    output VGA_VS,
    output VGA_HS,
    output [7:0] VGA_R,
    output [7:0] VGA_G,
    output [7:0] VGA_B,
    output VGA_CLK,
    output VGA_SYNC_N,
    output VGA_BLANK_N
);

    reg clk_25;
    reg [2:0] count;
    wire [7:0] uo_out;

    wire [2:0] red_out = {uo_out[0], uo_out[4]};
    wire [2:0] green_out = {uo_out[1], uo_out[5]};
    wire [2:0] blue_out = {uo_out[2], uo_out[6]};

    tt_um_emern_top main_gpu (
        .ui_in(),
        .uo_out(uo_out),
        .uio_in(GPIO_0[7:0]), // 0 = CS, 1 = MOSI, 3 = SCK
        .uio_out(GPIO_1[7:0]), // 4 =  INT
        .uio_oe(),
        .ena(1'b1),
        .clk(clk_25),
        .rst_n(KEY[0])
    );

    // Clock divider
    always @(posedge CLOCK_50) begin
        if (KEY[0] == 1'b0) begin
            clk_25  <= 1'b0;
        end else begin
            clk_25  <= ~clk_25;
        end
    end

    // VGA signals
    assign VGA_BLANK_N = 1'b1;
    assign VGA_SYNC_N = 1'b1;
    assign VGA_CLK = clk_25;

    assign VGA_R = {red_out[1], 3'b000, red_out[0], 3'b000};
    assign VGA_G = {green_out[1], 3'b000, green_out[0], 3'b000};
    assign VGA_B = {blue_out[1], 3'b000, blue_out[0], 3'b000};

    assign VGA_VS = uo_out[3];
    assign VGA_HS = uo_out[7];


    // LEDS for debug
    assign LEDR = 8'b10101010;

endmodule