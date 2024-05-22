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

  reg [15:0] d_in;
  reg [9:0] row_counter;
  reg [9:0] col_counter;

  // Random hooks to top level module
  wire [1:0] cmp_en = {d_in[1], d_in[4]};
  wire [5:0] background_color = 6'b000000;
  wire [11:0] poly_color = d_in[15:4];
  wire [13:0] v0_x = d_in & 14'b11000011110011;
  wire [11:0] v0_y = d_in[15:4] & 12'b110011110011;
  wire [13:0] v1_x = d_in;
  wire [11:0] v1_y = d_in & 12'b111100001100;
  wire [13:0] v2_x = ~d_in;
  wire [11:0] v2_y = d_in[15:4] & 12'b101100101100;
  wire [5:0] poly_depth = d_in | 6'b110100;

  wire [5:0] pixel_out;


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
      d_in <= 0;
      row_counter <= 0;
      col_counter <= 0;
    end

    else begin
      d_in <= {uio_in, ui_in};
      // TODO: Saturate these counters at the right point
      row_counter <= row_counter + 1'b1;
      col_counter <= col_counter + 1'b1;
    end
  end

endmodule
