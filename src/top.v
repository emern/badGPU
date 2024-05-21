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
  assign uio_out = test[7:0];
  assign uio_oe  = {test2, test[14:8]};

  wire [22:0] test;
  wire test2;

  tt_um_emern_inverse reciprocal (
    .determinant({uio_in[4:0], ui_in}),

    .inv_det_negative(test2),
    .inv_det(test)
  );
endmodule
