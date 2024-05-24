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
  assign uio_out = {3'b000, screen_inactive, 1'b0, miso, 2'b00}; // INT and MISO pins
  assign uio_oe  = 8'b00010100; // Output for INT and MISO
  assign uo_out = {h_sync, pixel_out[0], pixel_out[2], pixel_out[4], v_sync, pixel_out[1], pixel_out[3], pixel_out[5]};

  wire [9:0] row_counter;
  wire [9:0] col_counter;

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
  wire en_screen; // TODO: Decide if its worth supporting this... Might not be worth the hardware
  wire screen_inactive;
  wire h_sync;
  wire v_sync;
  wire miso;

  // VGA handles timing of pixels w/monitor
  tt_um_emern_vga vga (
    .clk(clk),
    .rst_n(rst_n),
    .h_sync(h_sync),
    .v_sync(v_sync),
    .row_counter(row_counter),
    .col_counter(col_counter),
    .screen_inactive(screen_inactive)
  );

  // Frontend handles SPI transfers and logic
  tt_um_emern_frontend frontend (
    .clk(clk),
    .rst_n(rst_n),

    // SPI params
    .cs_in(uio_in[0]),
    .mosi_in(uio_in[1]),
    .miso_out(miso),
    .sck_in(uio_in[3]),
    .en_load(screen_inactive),

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
    .pixel_row(row_counter[8:0]), // Current pixel row location - only care about the first 479 counts
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

    .pixel_out(pixel_out) // Output color for that pixel, r1r0g1g0b1b0
  );

endmodule
