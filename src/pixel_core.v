/*
 * Copyright (c) 2024 Emery Nagy
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

`include "constants.v"
`define BLACK_COLOR 6'b000000

module tt_um_emern_pixel_core (
    input clk,
    input rst_n,
    input [`N_POLY-1:0] cmp_en, // Enable polygon rasterization (one-hot encoded)
    input [8:0] pixel_row, // Current pixel row location
    input [9:0] pixel_col, // Current pixel column location
    input [`WCOLOR-1:0] background_color, // Background color to use when pixel is not within a triangle
    input [`WCOLOR*`N_POLY-1:0] poly_color, // Packed polygon color
    input [`WPX*`N_POLY-1:0] v0_x, // Packed polygon v0_x
    input [`WPY*`N_POLY-1:0] v0_y, // Packed polygon v0_y
    input [`WPX*`N_POLY-1:0] v1_x, // Packed polygon v1_x
    input [`WPY*`N_POLY-1:0] v1_y, // Packed polygon v1_y
    input [`WPX*`N_POLY-1:0] v2_x, // Packed polygon v2_x
    input [`WPY*`N_POLY-1:0] v2_y, // Packed polygon v2_y

    output [5:0] pixel_out // Output color for that pixel, rrggbb
);
    // Registered data, hold output pixel color and depth mapping
    reg [5:0] cur_pixel;

    // Unpack polygon A vertices
    wire [6:0] v0_x_a = (v0_x[6:0]);
    wire [5:0] v0_y_a = (v0_y[5:0]);

    wire [6:0] v1_x_a = (v1_x[6:0]);
    wire [5:0] v1_y_a = (v1_y[5:0]);

    wire [6:0] v2_x_a = (v2_x[6:0]);
    wire [5:0] v2_y_a = (v2_y[5:0]);

    wire rasterize_a;
    wire rasterize_a_gated = rasterize_a & cmp_en[0];

    // Unpack polygon B vertices
    wire [6:0] v0_x_b = (v0_x[13:7]);
    wire [5:0] v0_y_b = (v0_y[11:6]);

    wire [6:0] v1_x_b = (v1_x[13:7]);
    wire [5:0] v1_y_b = (v1_y[11:6]);

    wire [6:0] v2_x_b = (v2_x[13:7]);
    wire [5:0] v2_y_b = (v2_y[11:6]);

    wire rasterize_b;
    wire rasterize_b_gated = rasterize_b & cmp_en[1];

    // Unpack polygon C vertices
    wire [6:0] v0_x_c = (v0_x[20:14]);
    wire [5:0] v0_y_c = (v0_y[17:12]);

    wire [6:0] v1_x_c = (v1_x[20:14]);
    wire [5:0] v1_y_c = (v1_y[17:12]);

    wire [6:0] v2_x_c = (v2_x[20:14]);
    wire [5:0] v2_y_c = (v2_y[17:12]);

    wire rasterize_c;
    wire rasterize_c_gated = rasterize_c & cmp_en[2];

    // Unpack polygon D vertices
    wire [6:0] v0_x_d = (v0_x[27:21]);
    wire [5:0] v0_y_d = (v0_y[23:18]);

    wire [6:0] v1_x_d = (v1_x[27:21]);
    wire [5:0] v1_y_d = (v1_y[23:18]);

    wire [6:0] v2_x_d = (v2_x[27:21]);
    wire [5:0] v2_y_d = (v2_y[23:18]);

    wire rasterize_d;
    wire rasterize_d_gated = rasterize_d & cmp_en[3];

    assign pixel_out = cur_pixel;

    always @(posedge clk) begin
        // Synchronous reset
        if (rst_n == 1'b0) begin
            cur_pixel <= `BLACK_COLOR;
        end

        // Rasterize pixel
        else begin
            casez({rasterize_a_gated, rasterize_b_gated, rasterize_c_gated, rasterize_d_gated})
                4'b0000: begin
                    // No polygon should be rasterized
                    cur_pixel <= background_color;
                end
                4'b1???: begin
                    // Polygon A is requesting, this is the "closest" polygon
                    cur_pixel <= poly_color[5:0];
                end
                4'b01??: begin
                    // Polygon B is requesting
                    cur_pixel <= poly_color[11:6];
                end
                4'b001?: begin
                    // Polygon C is requesting
                    cur_pixel <= poly_color[17:12];
                end
                4'b0001: begin
                    // Polygon D is requesting
                    cur_pixel <= poly_color[23:18];
                end
            endcase
        end
    end

    // Rasterization of polygon A
    tt_um_emern_raster_core rc_a (
        .pixel_col(pixel_col),
        .pixel_row(pixel_row),

        .v0_x(v0_x_a),
        .v1_x(v1_x_a),
        .v2_x(v2_x_a),

        .v0_y(v0_y_a),
        .v1_y(v1_y_a),
        .v2_y(v2_y_a),

        .rasterize(rasterize_a)
    );

    // Rasterization of polygon B
    tt_um_emern_raster_core rc_b (
        .pixel_col(pixel_col),
        .pixel_row(pixel_row),

        .v0_x(v0_x_b),
        .v1_x(v1_x_b),
        .v2_x(v2_x_b),

        .v0_y(v0_y_b),
        .v1_y(v1_y_b),
        .v2_y(v2_y_b),

        .rasterize(rasterize_b)
    );


    // Rasterization of polygon C
    tt_um_emern_raster_core rc_c (
        .pixel_col(pixel_col),
        .pixel_row(pixel_row),

        .v0_x(v0_x_c),
        .v1_x(v1_x_c),
        .v2_x(v2_x_c),

        .v0_y(v0_y_c),
        .v1_y(v1_y_c),
        .v2_y(v2_y_c),

        .rasterize(rasterize_c)
    );

    // Rasterization of polygon D
    tt_um_emern_raster_core rc_d (
        .pixel_col(pixel_col),
        .pixel_row(pixel_row),

        .v0_x(v0_x_d),
        .v1_x(v1_x_d),
        .v2_x(v2_x_d),

        .v0_y(v0_y_d),
        .v1_y(v1_y_d),
        .v2_y(v2_y_d),

        .rasterize(rasterize_d)
    );


endmodule
