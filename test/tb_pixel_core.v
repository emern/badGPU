`default_nettype none
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
  reg [5:0] background_color;
  reg [5:0] pixel_out;

  // Setable TB parameters, its easier to do the slicing here than with cocotb
  reg [6:0] v0_x_a;
  reg [6:0] v0_x_b;

  reg [5:0] v0_y_a;
  reg [5:0] v0_y_b;

  reg [6:0] v1_x_a;
  reg [6:0] v1_x_b;

  reg [5:0] v1_y_a;
  reg [5:0] v1_y_b;

  reg [6:0] v2_x_a;
  reg [6:0] v2_x_b;

  reg [5:0] v2_y_a;
  reg [5:0] v2_y_b;

  reg [5:0] poly_color_a;
  reg [5:0] poly_color_b;

  reg en_a;
  reg en_b;

  // Pack bus {a_params, b_params}
  wire [13:0] v0_x = {v0_x_b, v0_x_a};
  wire [11:0] v0_y = {v0_y_b, v0_y_a};
  wire [13:0] v1_x = {v1_x_b, v1_x_a};
  wire [11:0] v1_y = {v1_y_b, v1_y_a};
  wire [13:0] v2_x = {v2_x_b, v2_x_a};
  wire [11:0] v2_y = {v2_y_b, v2_y_a};
  wire [11:0] poly_color = {poly_color_b, poly_color_a};
  wire [1:0] cmp_en = {en_b, en_a};


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
