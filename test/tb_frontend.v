`default_nettype none

`include "constants.v"
`timescale 1ns / 1ps

module tb_frontend ();

  initial begin
    $dumpfile("tb_frontend.vcd");
    $dumpvars(0, tb_frontend);
    #1;
  end

  // Inputs
  reg clk;
  reg rst_n;
  reg cs_in;
  reg mosi_in;
  reg miso_out;
  reg sck_in;
  reg en_load;

  // Outputs
  reg [`WCOLOR-1:0] bg_color_out;
  reg [`WCOLOR*`N_POLY-1:0] poly_color_out;
  reg [`WPX*`N_POLY-1:0] v0_x_out;
  reg [`WPY*`N_POLY-1:0] v0_y_out;
  reg [`WPX*`N_POLY-1:0] v1_x_out;
  reg [`WPY*`N_POLY-1:0] v1_y_out;
  reg [`WPX*`N_POLY-1:0] v2_x_out;
  reg [`WPY*`N_POLY-1:0] v2_y_out;
  reg [`N_POLY-1:0] poly_enable_out;


  // Unpack polygon A outputs
  wire [`WPX-1:0] v0_x_a = v0_x_out[`WPX-1:0];
  wire [`WPX-1:0] v1_x_a = v1_x_out[`WPX-1:0];
  wire [`WPX-1:0] v2_x_a = v2_x_out[`WPX-1:0];
  wire [`WPY-1:0] v0_y_a = v0_y_out[`WPY-1:0];
  wire [`WPY-1:0] v1_y_a = v1_y_out[`WPY-1:0];
  wire [`WPY-1:0] v2_y_a = v2_y_out[`WPY-1:0];
  wire [`WCOLOR-1:0] color_a = poly_color_out[`WCOLOR-1:0];

  // Unpack polygon B outputs
  wire [`WPX-1:0] v0_x_b = v0_x_out[`WPX*2-1:`WPX];
  wire [`WPX-1:0] v1_x_b = v1_x_out[`WPX*2-1:`WPX];
  wire [`WPX-1:0] v2_x_b = v2_x_out[`WPX*2-1:`WPX];
  wire [`WPY-1:0] v0_y_b = v0_y_out[`WPY*2-1:`WPY];
  wire [`WPY-1:0] v1_y_b = v1_y_out[`WPY*2-1:`WPY];
  wire [`WPY-1:0] v2_y_b = v2_y_out[`WPY*2-1:`WPY];
  wire [`WCOLOR-1:0] color_b = poly_color_out[`WCOLOR*2-1:`WCOLOR];

  // Unpack polygon C outputs
  wire [`WPX-1:0] v0_x_c = v0_x_out[`WPX*3-1:`WPX*2];
  wire [`WPX-1:0] v1_x_c = v1_x_out[`WPX*3-1:`WPX*2];
  wire [`WPX-1:0] v2_x_c = v2_x_out[`WPX*3-1:`WPX*2];
  wire [`WPY-1:0] v0_y_c = v0_y_out[`WPY*3-1:`WPY*2];
  wire [`WPY-1:0] v1_y_c = v1_y_out[`WPY*3-1:`WPY*2];
  wire [`WPY-1:0] v2_y_c = v2_y_out[`WPY*3-1:`WPY*2];
  wire [`WCOLOR-1:0] color_c = poly_color_out[`WCOLOR*3-1:`WCOLOR*2];

  // Unpack polygon D outputs
  wire [`WPX-1:0] v0_x_d = v0_x_out[`WPX*4-1:`WPX*3];
  wire [`WPX-1:0] v1_x_d = v1_x_out[`WPX*4-1:`WPX*3];
  wire [`WPX-1:0] v2_x_d = v2_x_out[`WPX*4-1:`WPX*3];
  wire [`WPY-1:0] v0_y_d = v0_y_out[`WPY*4-1:`WPY*3];
  wire [`WPY-1:0] v1_y_d = v1_y_out[`WPY*4-1:`WPY*3];
  wire [`WPY-1:0] v2_y_d = v2_y_out[`WPY*4-1:`WPY*3];
  wire [`WCOLOR-1:0] color_d = poly_color_out[`WCOLOR*4-1:`WCOLOR*3];

  // Unpack polygon E outputs
  wire [`WPX-1:0] v0_x_e = v0_x_out[`WPX*5-1:`WPX*4];
  wire [`WPX-1:0] v1_x_e = v1_x_out[`WPX*5-1:`WPX*4];
  wire [`WPX-1:0] v2_x_e = v2_x_out[`WPX*5-1:`WPX*4];
  wire [`WPY-1:0] v0_y_e = v0_y_out[`WPY*5-1:`WPY*4];
  wire [`WPY-1:0] v1_y_e = v1_y_out[`WPY*5-1:`WPY*4];
  wire [`WPY-1:0] v2_y_e = v2_y_out[`WPY*5-1:`WPY*4];
  wire [`WCOLOR-1:0] color_e = poly_color_out[`WCOLOR*5-1:`WCOLOR*4];

  // Unpack polygon F outputs
  wire [`WPX-1:0] v0_x_f = v0_x_out[`WPX*6-1:`WPX*5];
  wire [`WPX-1:0] v1_x_f = v1_x_out[`WPX*6-1:`WPX*5];
  wire [`WPX-1:0] v2_x_f = v2_x_out[`WPX*6-1:`WPX*5];
  wire [`WPY-1:0] v0_y_f = v0_y_out[`WPY*6-1:`WPY*5];
  wire [`WPY-1:0] v1_y_f = v1_y_out[`WPY*6-1:`WPY*5];
  wire [`WPY-1:0] v2_y_f = v2_y_out[`WPY*6-1:`WPY*5];
  wire [`WCOLOR-1:0] color_f = poly_color_out[`WCOLOR*6-1:`WCOLOR*5];


  tt_um_emern_frontend user_project (
    .clk(clk),
    .rst_n(rst_n),

    .cs_in(cs_in),
    .mosi_in(mosi_in),
    .miso_out(miso_out),
    .sck_in(sck_in),
    .en_load(en_load),

    .bg_color_out(bg_color_out),
    .poly_color_out(poly_color_out),
    .v0_x_out(v0_x_out),
    .v0_y_out(v0_y_out),
    .v1_x_out(v1_x_out),
    .v1_y_out(v1_y_out),
    .v2_x_out(v2_x_out),
    .v2_y_out(v2_y_out),
    .poly_enable_out(poly_enable_out)
  );

endmodule
