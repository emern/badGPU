/*
 * Copyright (c) 2024 Emery Nagy
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_emern_top (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
  assign uio_out = 8'd0;
  assign uio_oe  = 8'd0;
  assign uo_out = {2'b00, pixel_out};

  reg [9:0] row_counter;
  reg [9:0] col_counter;

  wire [1:0] cmp_en;
  wire [5:0] background_color;
  wire [11:0] poly_color;
  wire [13:0] v0_x;
  wire [11:0] v0_y;
  wire [13:0] v1_x;
  wire [11:0] v1_y;
  wire [13:0] v2_x;
  wire [11:0] v2_y;
  wire [5:0] poly_depth;
  wire [5:0] pixel_out;
  wire en_screen;


  // Frontend handles SPI transfers and logic
  tt_um_emern_frontend frontend (
    .clk(clk),
    .rst_n(rst_n),

    // SPI params
    .cs_in(ui_in[0]),
    .mosi_in(ui_in[1]),
    .miso_in(ui_in[2]),
    .sck_in(ui_in[3]),
    .en_load(1'b1), // TODO: Fix

    // Stored outputs
    .bg_color_out(background_color), // Background register
    .poly_color_out(poly_color), // Packed polygon color
    .v0_x_out(v0_x), // Packed polygon v0 x
    .v0_y_out(v0_y), // Packed polygon v0 y
    .v1_x_out(v1_x), // Packed polygon v1 x
    .v1_y_out(v1_y), // Packed polygon v1 y
    .v2_x_out(v2_x), // Packed polygon v2 x
    .v2_y_out(v2_y), // Packed polygon v2 y
    .poly_depth_out(poly_depth), // Packed polygon depth
    .en_screen_out(en_screen), // Enable screen output
    .poly_enable_out(cmp_en) // Enable polygons individually
);

  // Pixel core drives all rasterization logic and has internal state
  tt_um_emern_pixel_core pixel_core (
    .clk(clk),
    .rst_n(rst_n),
    .cmp_en(cmp_en), // Enable polygon rasterization (one-hot encoded)
    .pixel_row(row_counter[8:0]), // Current pixel row location
    .pixel_col(col_counter), // Current pixel column location
    .background_color(background_color), // Background color to use when pixel is not within a triangle
    .poly_color(poly_color), // Packed polygon color
    .v0_x(v0_x), // Packed polygon v0_x
    .v0_y(v0_y), // Packed polygon v0_y
    .v1_x(v1_x), // Packed polygon v1_x
    .v1_y(v1_y), // Packed polygon v1_y
    .v2_x(v2_x), // Packed polygon v2_x
    .v2_y(v2_y), // Packed polygon v2_y
    .poly_depth(poly_depth), // Packed polygon depth

    .pixel_out(pixel_out) // Output color for that pixel, rrggbb
  );

  // Register for data input and row/col counters
  always @(posedge clk) begin
    if (rst_n == 1'b0) begin
      row_counter <= 0;
      col_counter <= 0;
    end

    else begin
      // TODO: Saturate these counters at the right point
      row_counter <= row_counter + 1'b1;
      col_counter <= col_counter + 1'b1;
    end
  end

endmodule
