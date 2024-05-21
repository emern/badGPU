/*
 * Copyright (c) 2024 Emery Nagy
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

`define BLACK_COLOR 6'b000000


module tt_um_emern_pixel_core (
    input clk,
    input rst_n,
    input cmp_en, // Enable polygon rasterization
    input [8:0] pixel_row, // Current pixel row location
    input [9:0] pixel_col, // Current pixel column location
    input [5:0] background_color, // Background color to use when pixel is not within a triangle
    input [7:0] en_polygon, // Enable polygon generation
    input [5:0] poly_color,
    input en_shading,
);

    // Registered data, hold output pixel color and depth mapping
    reg [5:0] cur_pixel;

    assign pixel_out = cur_pixel;


    always @(posedge clk) begin

        // Synchronous reset
        if (rst_n == 1'b0) begin
            cur_pixel <= `BLACK_COLOR;
        end

        // Rasterize pixel
        else if (cmp_en == 1'b1) begin
            cur_pixel <= `BLACK_COLOR;
        end
    end


endmodule
