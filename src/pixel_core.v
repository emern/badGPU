/*
 * Copyright (c) 2024 Emery Nagy
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

`define BLACK_COLOR 6'b000000

module tt_um_emern_pixel_core (
    input clk,
    input rst_n,
    input [1:0] cmp_en, // Enable polygon rasterization (one-hot encoded)
    input [8:0] pixel_row, // Current pixel row location
    input [9:0] pixel_col, // Current pixel column location
    input [5:0] background_color, // Background color to use when pixel is not within a triangle
    input [11:0] poly_color, // Packed polygon color
    input [13:0] v0_x, // Packed polygon v0_x
    input [11:0] v0_y, // Packed polygon v0_y
    input [13:0] v1_x, // Packed polygon v1_x
    input [11:0] v1_y, // Packed polygon v1_y
    input [13:0] v2_x, // Packed polygon v2_x
    input [11:0] v2_y, // Packed polygon v2_y

    output [5:0] pixel_out // Output color for that pixel, rrggbb
);
    // Registered data, hold output pixel color and depth mapping
    reg [5:0] cur_pixel;

    // TODO: check if its more efficient to share hardware for this and just register all bits
    // Unpack polygon A vertices, should be multiplied by 10
    wire [9:0] v0_x_a = (v0_x[6:0] << 3) + (v0_x[6:0] << 1);
    wire [8:0] v0_y_a = (v0_y[5:0] << 3) + (v0_y[5:0] << 1);

    wire [9:0] v1_x_a = (v1_x[6:0] << 3) + (v1_x[6:0] << 1);
    wire [8:0] v1_y_a = (v1_y[5:0] << 3) + (v1_y[5:0] << 1);

    wire [9:0] v2_x_a = (v2_x[6:0] << 3) + (v2_x[6:0] << 1);
    wire [8:0] v2_y_a = (v2_y[5:0] << 3) + (v2_y[5:0] << 1);

    wire rasterize_a;
    wire rasterize_a_gated = rasterize_a & cmp_en[0];

    // Unpack polygon B vertices, should be multiplied by 10
    wire [9:0] v0_x_b = (v0_x[13:7] << 3) + (v0_x[13:7] << 1);
    wire [8:0] v0_y_b = (v0_y[11:6] << 3) + (v0_y[11:6] << 1);

    wire [9:0] v1_x_b = (v1_x[13:7] << 3) + (v1_x[13:7] << 1);
    wire [8:0] v1_y_b = (v1_y[11:6] << 3) + (v1_y[11:6] << 1);

    wire [9:0] v2_x_b = (v2_x[13:7] << 3) + (v2_x[13:7] << 1);
    wire [8:0] v2_y_b = (v2_y[11:6] << 3) + (v2_y[11:6] << 1);

    wire rasterize_b;
    wire rasterize_b_gated = rasterize_b & cmp_en[1];


    assign pixel_out = cur_pixel;

    always @(posedge clk) begin
        // Synchronous reset
        if (rst_n == 1'b0) begin
            cur_pixel <= `BLACK_COLOR;
        end

        // Rasterize pixel
        else begin
            casez({rasterize_a_gated, rasterize_b_gated})
                2'b00: begin
                    // No polygon should be rasterized
                    cur_pixel <= background_color;
                end
                2'b1?: begin
                    // Polygon A is requesting, this is the "closest" polygon
                    cur_pixel <= poly_color[5:0];
                end
                2'b01: begin
                    // Polygon B is requesting, this is the "furthest" polygon and should be rasterized in last priority
                    cur_pixel <= poly_color[11:6];
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

endmodule
