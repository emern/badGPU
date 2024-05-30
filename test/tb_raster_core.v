`default_nettype none
`timescale 1ns / 1ps

module tb_raster_core ();

  // Dump the signals to a VCD file. You can view it with gtkwave.
  initial begin
    $dumpfile("tb_raster_core.vcd");
    $dumpvars(0, tb_raster_core);
    #1;
  end

  // Wire up the inputs and outputs:
    reg [9:0] pixel_col;
    reg [8:0] pixel_row;

    reg [6:0] v0_x;
    reg [6:0] v1_x;
    reg [6:0] v2_x;

    reg [5:0] v0_y;
    reg [5:0] v1_y;
    reg [5:0] v2_y;

    reg rasterize;

  // Replace tt_um_example with your module name:
  tt_um_emern_raster_core user_project (

    .pixel_col(pixel_col),
    .pixel_row(pixel_row),

    .v0_x(v0_x),
    .v1_x(v1_x),
    .v2_x(v2_x),

    .v0_y(v0_y),
    .v1_y(v1_y),
    .v2_y(v2_y),

    .rasterize(rasterize)
  );

endmodule
