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
  // Hook up reciprocal calc unit for testing
  assign uio_out = 8'd0;
  assign uio_oe  = 8'd0;
  assign uo_out = {7'b0000000, rasterize_out};

  wire rasterize;
  reg [7:0] d_in;
  reg rasterize_out;

  tt_um_emern_raster_core e_raster_core (
    .pixel_col({1'b1, d_in, 1'b0}),
    .pixel_row({1'b0, uio_in}),

    .v0_x({2'b11, d_in}),
    .v1_x({2'b10, uio_in}),
    .v2_x({d_in, 2'b10}),

    .v0_y({1'b1, uio_in}),
    .v1_y({d_in, 1'b0}),
    .v2_y({uio_in, 1'b1}),

    .rasterize(rasterize)
  );


  always @(posedge clk) begin
    d_in <= ui_in;
    rasterize_out <= rasterize;
  end

endmodule
