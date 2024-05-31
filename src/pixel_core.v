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
    wire [`WPX-1:0] v0_x_a = (v0_x[`WPX-1:0]);
    wire [`WPY-1:0] v0_y_a = (v0_y[`WPY-1:0]);

    wire [`WPX-1:0] v1_x_a = (v1_x[`WPX-1:0]);
    wire [`WPY-1:0] v1_y_a = (v1_y[`WPY-1:0]);

    wire [`WPX-1:0] v2_x_a = (v2_x[`WPX-1:0]);
    wire [`WPY-1:0] v2_y_a = (v2_y[`WPY-1:0]);

    wire rasterize_a;
    wire rasterize_a_gated = rasterize_a & cmp_en[0];

    // Unpack polygon B vertices
    wire [`WPX-1:0] v0_x_b = (v0_x[`WPX*2-1:`WPX]);
    wire [`WPY-1:0] v0_y_b = (v0_y[`WPY*2-1:`WPY]);

    wire [`WPX-1:0] v1_x_b = (v1_x[`WPX*2-1:`WPX]);
    wire [`WPY-1:0] v1_y_b = (v1_y[`WPY*2-1:`WPY]);

    wire [`WPX-1:0] v2_x_b = (v2_x[`WPX*2-1:`WPX]);
    wire [`WPY-1:0] v2_y_b = (v2_y[`WPY*2-1:`WPY]);

    wire rasterize_b;
    wire rasterize_b_gated = rasterize_b & cmp_en[1];

    // Unpack polygon C vertices
    wire [`WPX-1:0] v0_x_c = (v0_x[`WPX*3-1:`WPX*2]);
    wire [`WPY-1:0] v0_y_c = (v0_y[`WPY*3-1:`WPY*2]);

    wire [`WPX-1:0] v1_x_c = (v1_x[`WPX*3-1:`WPX*2]);
    wire [`WPY-1:0] v1_y_c = (v1_y[`WPY*3-1:`WPY*2]);

    wire [`WPX-1:0] v2_x_c = (v2_x[`WPX*3-1:`WPX*2]);
    wire [`WPY-1:0] v2_y_c = (v2_y[`WPY*3-1:`WPY*2]);

    wire rasterize_c;
    wire rasterize_c_gated = rasterize_c & cmp_en[2];

    // Unpack polygon D vertices
    wire [`WPX-1:0] v0_x_d = (v0_x[`WPX*4-1:`WPX*3]);
    wire [`WPY-1:0] v0_y_d = (v0_y[`WPY*4-1:`WPY*3]);

    wire [`WPX-1:0] v1_x_d = (v1_x[`WPX*4-1:`WPX*3]);
    wire [`WPY-1:0] v1_y_d = (v1_y[`WPY*4-1:`WPY*3]);

    wire [`WPX-1:0] v2_x_d = (v2_x[`WPX*4-1:`WPX*3]);
    wire [`WPY-1:0] v2_y_d = (v2_y[`WPY*4-1:`WPY*3]);

    wire rasterize_d;
    wire rasterize_d_gated = rasterize_d & cmp_en[3];

    // Unpack polygon E vertices
    wire [`WPX-1:0] v0_x_e = (v0_x[`WPX*5-1:`WPX*4]);
    wire [`WPY-1:0] v0_y_e = (v0_y[`WPY*5-1:`WPY*4]);

    wire [`WPX-1:0] v1_x_e = (v1_x[`WPX*5-1:`WPX*4]);
    wire [`WPY-1:0] v1_y_e = (v1_y[`WPY*5-1:`WPY*4]);

    wire [`WPX-1:0] v2_x_e = (v2_x[`WPX*5-1:`WPX*4]);
    wire [`WPY-1:0] v2_y_e = (v2_y[`WPY*5-1:`WPY*4]);

    wire rasterize_e;
    wire rasterize_e_gated = rasterize_e & cmp_en[4];

    // Unpack polygon F vertices
    wire [`WPX-1:0] v0_x_f = (v0_x[`WPX*6-1:`WPX*5]);
    wire [`WPY-1:0] v0_y_f = (v0_y[`WPY*6-1:`WPY*5]);

    wire [`WPX-1:0] v1_x_f = (v1_x[`WPX*6-1:`WPX*5]);
    wire [`WPY-1:0] v1_y_f = (v1_y[`WPY*6-1:`WPY*5]);

    wire [`WPX-1:0] v2_x_f = (v2_x[`WPX*6-1:`WPX*5]);
    wire [`WPY-1:0] v2_y_f = (v2_y[`WPY*6-1:`WPY*5]);

    wire rasterize_f;
    wire rasterize_f_gated = rasterize_f & cmp_en[5];

    assign pixel_out = cur_pixel;

    always @(posedge clk) begin
        // Synchronous reset
        if (rst_n == 1'b0) begin
            cur_pixel <= `BLACK_COLOR;
        end

        // Rasterize pixel
        else begin
            casez({rasterize_a_gated, rasterize_b_gated, rasterize_c_gated, rasterize_d_gated, rasterize_e_gated, rasterize_f_gated})
                6'b000000: begin
                    // No polygon should be rasterized
                    cur_pixel <= background_color;
                end
                6'b1?????: begin
                    // Polygon A is requesting, this is the "closest" polygon
                    cur_pixel <= poly_color[`WCOLOR-1:0];
                end
                6'b01????: begin
                    // Polygon B is requesting
                    cur_pixel <= poly_color[`WCOLOR*2-1:`WCOLOR];
                end
                6'b001???: begin
                    // Polygon C is requesting
                    cur_pixel <= poly_color[`WCOLOR*3-1:`WCOLOR*2];
                end
                6'b0001??: begin
                    // Polygon D is requesting
                    cur_pixel <= poly_color[`WCOLOR*4-1:`WCOLOR*3];
                end
                6'b00001?: begin
                    // Polygon E is requesting
                    cur_pixel <= poly_color[`WCOLOR*5-1:`WCOLOR*4];
                end
                6'b000001: begin
                    // Polygon F is requesting
                    cur_pixel <= poly_color[`WCOLOR*6-1:`WCOLOR*5];
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

    // Rasterization of polygon E
    tt_um_emern_raster_core rc_e (
        .pixel_col(pixel_col),
        .pixel_row(pixel_row),

        .v0_x(v0_x_e),
        .v1_x(v1_x_e),
        .v2_x(v2_x_e),

        .v0_y(v0_y_e),
        .v1_y(v1_y_e),
        .v2_y(v2_y_e),

        .rasterize(rasterize_e)
    );


    // Rasterization of polygon F
    tt_um_emern_raster_core rc_f (
        .pixel_col(pixel_col),
        .pixel_row(pixel_row),

        .v0_x(v0_x_f),
        .v1_x(v1_x_f),
        .v2_x(v2_x_f),

        .v0_y(v0_y_f),
        .v1_y(v1_y_f),
        .v2_y(v2_y_f),

        .rasterize(rasterize_f)
    );

endmodule
