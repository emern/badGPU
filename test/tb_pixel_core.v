`default_nettype none
`include "constants.v"
`timescale 1ns / 1ps

module tb_pixel_core ();

  // Dump the signals to a VCD file. You can view it with gtkwave.
  initial begin
    $dumpfile("tb_pixel_core.vcd");
    $dumpvars(0, tb_pixel_core);
    #1;
  end

  // Direct to DUT parameters
  reg clk;
  reg rst_n;
  reg [8:0] pixel_row;
  reg [9:0] pixel_col;
  reg [`WCOLOR-1:0] background_color;
  reg [`WCOLOR-1:0] pixel_out;

  // Setable TB parameters, its easier to do the slicing here than with cocotb
  reg [`WPX-1:0] v0_x_a;
  reg [`WPX-1:0] v0_x_b;
  reg [`WPX-1:0] v0_x_c;
  reg [`WPX-1:0] v0_x_d;
  reg [`WPX-1:0] v0_x_e;
  reg [`WPX-1:0] v0_x_f;

  reg [`WPY-1:0] v0_y_a;
  reg [`WPY-1:0] v0_y_b;
  reg [`WPY-1:0] v0_y_c;
  reg [`WPY-1:0] v0_y_d;
  reg [`WPY-1:0] v0_y_e;
  reg [`WPY-1:0] v0_y_f;

  reg [`WPX-1:0] v1_x_a;
  reg [`WPX-1:0] v1_x_b;
  reg [`WPX-1:0] v1_x_c;
  reg [`WPX-1:0] v1_x_d;
  reg [`WPX-1:0] v1_x_e;
  reg [`WPX-1:0] v1_x_f;

  reg [`WPY-1:0] v1_y_a;
  reg [`WPY-1:0] v1_y_b;
  reg [`WPY-1:0] v1_y_c;
  reg [`WPY-1:0] v1_y_d;
  reg [`WPY-1:0] v1_y_e;
  reg [`WPY-1:0] v1_y_f;

  reg [`WPX-1:0] v2_x_a;
  reg [`WPX-1:0] v2_x_b;
  reg [`WPX-1:0] v2_x_c;
  reg [`WPX-1:0] v2_x_d;
  reg [`WPX-1:0] v2_x_e;
  reg [`WPX-1:0] v2_x_f;

  reg [`WPY-1:0] v2_y_a;
  reg [`WPY-1:0] v2_y_b;
  reg [`WPY-1:0] v2_y_c;
  reg [`WPY-1:0] v2_y_d;
  reg [`WPY-1:0] v2_y_e;
  reg [`WPY-1:0] v2_y_f;

  reg [`WCOLOR-1:0] poly_color_a;
  reg [`WCOLOR-1:0] poly_color_b;
  reg [`WCOLOR-1:0] poly_color_c;
  reg [`WCOLOR-1:0] poly_color_d;
  reg [`WCOLOR-1:0] poly_color_e;
  reg [`WCOLOR-1:0] poly_color_f;

  reg en_a;
  reg en_b;
  reg en_c;
  reg en_d;
  reg en_e;
  reg en_f;

  // Pack bus {a_params, b_params}
  wire [`WPX*`N_POLY-1:0] v0_x = {v0_x_f, v0_x_e, v0_x_d, v0_x_c, v0_x_b, v0_x_a};
  wire [`WPY*`N_POLY-1:0] v0_y = {v0_y_f, v0_y_e, v0_y_d, v0_y_c, v0_y_b, v0_y_a};
  wire [`WPX*`N_POLY-1:0] v1_x = {v1_x_f, v1_x_e, v1_x_d, v1_x_c, v1_x_b, v1_x_a};
  wire [`WPY*`N_POLY-1:0] v1_y = {v1_y_f, v1_y_e, v1_y_d, v1_y_c, v1_y_b, v1_y_a};
  wire [`WPX*`N_POLY-1:0] v2_x = {v2_x_f, v2_x_e, v2_x_d, v2_x_c, v2_x_b, v2_x_a};
  wire [`WPY*`N_POLY-1:0] v2_y = {v2_y_f, v2_y_e, v2_y_d, v2_y_c, v2_y_b, v2_y_a};
  wire [`WCOLOR*`N_POLY-1:0] poly_color = {poly_color_f, poly_color_e, poly_color_d, poly_color_c, poly_color_b, poly_color_a};
  wire [`N_POLY-1:0] cmp_en = {en_f, en_e, en_d, en_c, en_b, en_a};


  // Device under test
  tt_um_emern_pixel_core user_project (
    .clk(clk),
    .rst_n(rst_n),
    .cmp_en(cmp_en), // Enable polygon rasterization
    .pixel_row(pixel_row), // Current pixel row location
    .pixel_col(pixel_col), // Current pixel column location
    .background_color(background_color), // Background color to use when pixel is not within a triangle
    .poly_color(poly_color), // Packed polygon color
    .v0_x(v0_x), // Packed polygon v0_x
    .v0_y(v0_y), // Packed polygon v0_y
    .v1_x(v1_x), // Packed polygon v1_x
    .v1_y(v1_y), // Packed polygon v1_y
    .v2_x(v2_x), // Packed polygon v2_x
    .v2_y(v2_y), // Packed polygon v2_y
    .pixel_out(pixel_out) // Output color for that pixel, rrggbb
  );

endmodule
