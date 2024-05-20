/*
 * Copyright (c) 2024 Emery Nagy
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

`define DEPTH_INF 3'b000
`define BLACK_COLOR 6'b000000


module tt_um_emern_pixel_core (
    input clk,
    input rst_n,
    input pixel_clr, // Clear the pixel state
    input cmp_en, // Enable polygon rasterization
    input [8:0] pixel_row, // Current pixel row location
    input [9:0] pixel_col, // Current pixel column location
    input [5:0] background_color, // Background color to use when pixel is not within a triangle
    input [3:0] en_polygon, // One-hot code enables polygon rasterization

    // Packed polygon data struct (first polygon)
    input [8:0] polygon_a_depth,
    input [5:0] polygon_a_color,
    input [17:0] polygon_a_column,
    input [17:0] polygon_a_row,

    // Packed polygon data struct (second polygon)
    input [8:0] polygon_b_depth,
    input [5:0] polygon_b_color,
    input [17:0] polygon_b_column,
    input [17:0] polygon_b_row,

    // Packed polygon data struct (third polygon)
    input [8:0] polygon_c_depth,
    input [5:0] polygon_c_color,
    input [17:0] polygon_c_column,
    input [17:0] polygon_c_row,

    // Packed polygon data struct (fourth polygon)
    input [8:0] polygon_d_depth,
    input [5:0] polygon_d_color,
    input [17:0] polygon_d_column,
    input [17:0] polygon_d_row,

    output [5:0] pixel_out // Final value of pixel color
);

    // Registered data, hold output pixel color and depth mapping
    reg [5:0] cur_pixel;
    reg [2:0] cur_depth;

    // Polygon A unpacked data
    wire [9:0] pa_v0_x;
    wire [9:0] pa_v1_x;
    wire [9:0] pa_v2_x;

    wire [8:0] pa_v0_y;
    wire [8:0] pa_v1_y;
    wire [8:0] pa_v2_y;

    wire pa_rasterize;

    // Polygon B unpacked data
    wire [9:0] pb_v0_x;
    wire [9:0] pb_v1_x;
    wire [9:0] pb_v2_x;

    wire [8:0] pb_v0_y;
    wire [8:0] pb_v1_y;
    wire [8:0] pb_v2_y;

    wire pb_rasterize;

    // Polygon C unpacked data
    wire [9:0] pc_v0_x;
    wire [9:0] pc_v1_x;
    wire [9:0] pc_v2_x;

    wire [8:0] pc_v0_y;
    wire [8:0] pc_v1_y;
    wire [8:0] pc_v2_y;

    wire pc_rasterize;

    // Polygon D unpacked data
    wire [9:0] pd_v0_x;
    wire [9:0] pd_v1_x;
    wire [9:0] pd_v2_x;

    wire [8:0] pd_v0_y;
    wire [8:0] pd_v1_y;
    wire [8:0] pd_v2_y;

    wire pd_rasterize;

    assign pixel_out = cur_pixel;

    // Each polygon column is encoded by value 0 -> 64 which needs to be interpolated to 0 -> 640 (multiply by 10)
    assign pa_v0_x = (polygon_a_column[5:0] << 3) + (polygon_a_column[5:0] << 2);
    assign pa_v1_x = (polygon_a_column[11:6] << 3) + (polygon_a_column[11:6] << 2);
    assign pa_v2_x = (polygon_a_column[17:12] << 3) + (polygon_a_column[17:12] << 2);

    assign pb_v0_x = (polygon_b_column[5:0] << 3) + (polygon_b_column[5:0] << 2);
    assign pb_v1_x = (polygon_b_column[11:6] << 3) + (polygon_b_column[11:6] << 2);
    assign pb_v2_x = (polygon_b_column[17:12] << 3) + (polygon_b_column[17:12] << 2);

    assign pc_v0_x = (polygon_c_column[5:0] << 3) + (polygon_c_column[5:0] << 2);
    assign pc_v1_x = (polygon_c_column[11:6] << 3) + (polygon_c_column[11:6] << 2);
    assign pc_v2_x = (polygon_c_column[17:12] << 3) + (polygon_c_column[17:12] << 2);

    assign pd_v0_x = (polygon_d_column[5:0] << 3) + (polygon_d_column[5:0] << 2);
    assign pd_v1_x = (polygon_d_column[11:6] << 3) + (polygon_d_column[11:6] << 2);
    assign pd_v2_x = (polygon_d_column[17:12] << 3) + (polygon_d_column[17:12] << 2);

    // Each polygon row is encoded by value 0 -> 64 which needs to be interpolated to 0 -> 480 (multiply by 10)
    assign pa_v0_y = (polygon_a_row[5:0] << 3) + (polygon_a_row[5:0] << 2);
    assign pa_v1_y = (polygon_a_row[11:6] << 3) + (polygon_a_row[11:6] << 2);
    assign pa_v2_y = (polygon_a_row[17:12] << 3) + (polygon_a_row[17:12] << 2);

    assign pb_v0_y = (polygon_b_row[5:0] << 3) + (polygon_b_row[5:0] << 2);
    assign pb_v1_y = (polygon_b_row[11:6] << 3) + (polygon_b_row[11:6] << 2);
    assign pb_v2_y = (polygon_b_row[17:12] << 3) + (polygon_b_row[17:12] << 2);

    assign pc_v0_y = (polygon_c_row[5:0] << 3) + (polygon_c_row[5:0] << 2);
    assign pc_v1_y = (polygon_c_row[11:6] << 3) + (polygon_c_row[11:6] << 2);
    assign pc_v2_y = (polygon_c_row[17:12] << 3) + (polygon_c_row[17:12] << 2);

    assign pd_v0_y = (polygon_d_row[5:0] << 3) + (polygon_d_row[5:0] << 2);
    assign pd_v1_y = (polygon_d_row[11:6] << 3) + (polygon_d_row[11:6] << 2);
    assign pd_v2_y = (polygon_d_row[17:12] << 3) + (polygon_d_row[17:12] << 2);


    always @(posedge clk) begin

        // Synchronous reset
        if (rst_n == 1'b0) begin
            cur_pixel <= `BLACK_COLOR;
            cur_depth <= `DEPTH_INF;
        end

        // Rasterize pixel
        else if (cmp_en == 1'b1) begin

            

        end
    end

    // Each pixel core can rasterize up to 4 triangles in parallel

    // Core A
    raster_core r_a (
        .pixel_col(pixel_col),
        .pixel_row(pixel_row),
        .v0_x(pa_v0_x),
        .v1_x(pa_v1_x),
        .v2_x(pa_v2_x),
        .v0_y(pa_v0_y),
        .v1_y(pa_v1_y),
        .v2_y(pa_v2_y),
        .rasterize(pa_rasterize)
    );

    // Core B
    raster_core r_b (
        .pixel_col(pixel_col),
        .pixel_row(pixel_row),
        .v0_x(pb_v0_x),
        .v1_x(pb_v1_x),
        .v2_x(pb_v2_x),
        .v0_y(pb_v0_y),
        .v1_y(pb_v1_y),
        .v2_y(pb_v2_y),
        .rasterize(pb_rasterize)
    );

    // Core C
    raster_core r_c (
        .pixel_col(pixel_col),
        .pixel_row(pixel_row),
        .v0_x(pc_v0_x),
        .v1_x(pc_v1_x),
        .v2_x(pc_v2_x),
        .v0_y(pc_v0_y),
        .v1_y(pc_v1_y),
        .v2_y(pc_v2_y),
        .rasterize(pc_rasterize)
    );

    // Core D
    raster_core r_d (
        .pixel_col(pixel_col),
        .pixel_row(pixel_row),
        .v0_x(pd_v0_x),
        .v1_x(pd_v1_x),
        .v2_x(pd_v2_x),
        .v0_y(pd_v0_y),
        .v1_y(pd_v1_y),
        .v2_y(pd_v2_y),
        .rasterize(pd_rasterize)
    );


endmodule
