/*
 * Copyright (c) 2024 Emery Nagy
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_emern_raster_core (
    input [9:0] pixel_col,
    input [8:0] pixel_row,

    input [6:0] v0_x,
    input [6:0] v1_x,
    input [6:0] v2_x,

    input [5:0] v0_y,
    input [5:0] v1_y,
    input [5:0] v2_y,

    output rasterize
);

    wire signed [22:0] res_a;
    wire signed [10:0] a_x;
    wire signed [9:0] a_y;

    wire signed [22:0] res_b;
    wire signed [10:0] b_x;
    wire signed [9:0] b_y;

    wire signed [22:0] res_c;
    wire signed [10:0] c_x;
    wire signed [9:0] c_y;

    // Expand out polygon coordinates
    // Note if we do as many vertex subtractions BEFORE expanding out polygon coordinates as possible we save logic since (a-b)*8 == a*8 - b*8 with smaller adder circuits
    wire [9:0] v0_x_e = (v0_x << 3);
    wire [9:0] v1_x_e = (v1_x << 3);
    wire [9:0] v2_x_e = (v2_x << 3);

    wire [8:0] v0_y_e = (v0_y << 3);
    wire [8:0] v1_y_e = (v1_y << 3);
    wire [8:0] v2_y_e = (v2_y << 3);

    // Fast algo found here: https://erkaman.github.io/posts/fast_triangle_rasterization.html
    // Basically, calculate normal between of each of the triangle vertices and given point
    // If all normals are positive, we rasterize the pixel

    // Note that the order of supplied vertices is important!
    // V0 should have the largest magnitude X or column coordinate, V1 the second largest and V0 the smallest!

    // Vertex 0 -> 1
    assign a_x = ($signed({1'b0, v1_x}) - $signed({1'b0, v0_x})) << 3;
    assign a_y = ($signed({1'b0, v1_y}) - $signed({1'b0, v0_y})) << 3;
    assign res_a = ((a_x) * ($signed({14'h0, pixel_row}) - $signed({14'h0, v0_y_e}))) - ((a_y) * ($signed({13'h0, pixel_col}) - $signed({13'h0, v0_x_e})));

    // Vertex 1 -> 2
    assign b_x = ($signed({1'b0, v2_x}) - $signed({1'b0, v1_x})) << 3;
    assign b_y = ($signed({1'b0, v2_y}) - $signed({1'b0, v1_y})) << 3;
    assign res_b = ((b_x) * ($signed({14'h0, pixel_row}) - $signed({14'h0, v1_y_e}))) - ((b_y) * ($signed({13'h0, pixel_col}) - $signed({13'h0, v1_x_e})));

    // Vertex 2 -> 0
    assign c_x = ($signed({1'b0, v0_x}) - $signed({1'b0, v2_x})) << 3;
    assign c_y = ($signed({1'b0, v0_y}) - $signed({1'b0, v2_y})) << 3;
    assign res_c = ((c_x) * ($signed({14'h0, pixel_row}) - $signed({14'h0, v2_y_e}))) - ((c_y) * ($signed({13'h0, pixel_col}) - $signed({13'h0, v2_x_e})));

    // Triangle to be rasterized only if pixel fits within each of its bounding surfaces
    assign rasterize = ((res_a[22] != 1'b1) && (res_b[22] != 1'b1) && (res_c[22] != 1'b1)) ? 1'b1 : 1'b0;


endmodule
