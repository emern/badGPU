`default_nettype none
`timescale 1ns / 1ps

module tb_top ();

  // Dump the signals to a VCD file. You can view it with gtkwave.
  initial begin
    $dumpfile("tb_top.vcd");
    $dumpvars(0, tb_top);
    #1;
  end

  // Wire up the inputs and outputs:
  reg clk;
  reg rst_n;
  reg ena;
  reg [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;

  wire [2:0] red_out = {uo_out[0], uo_out[4]};
  wire [2:0] green_out = {uo_out[1], uo_out[5]};
  wire [2:0] blue_out = {uo_out[2], uo_out[6]};
  wire hsync = uo_out[7];
  wire vsync = uo_out[3];

  wire spi_sck;
  wire spi_mosi;
  wire spi_cs;

  assign uio_in[3] = spi_sck;
  assign uio_in[1] = spi_mosi;
  assign uio_in[0] = spi_cs;

  wire int_out = uio_out[4];

  // Replace tt_um_example with your module name:
  tt_um_emern_top user_project (

      // Include power ports for the Gate Level test:
`ifdef GL_TEST
      .VPWR(1'b1),
      .VGND(1'b0),
`endif

      .ui_in  (ui_in),    // Dedicated inputs
      .uo_out (uo_out),   // Dedicated outputs
      .uio_in (uio_in),   // IOs: Input path
      .uio_out(uio_out),  // IOs: Output path
      .uio_oe (uio_oe),   // IOs: Enable path (active high: 0=input, 1=output)
      .ena    (ena),      // enable - goes high when design is selected
      .clk    (clk),      // clock
      .rst_n  (rst_n)     // not reset
  );

endmodule
