`default_nettype none
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
  reg [5:0] bg_color_out;
  reg [11:0] poly_color_out;
  reg [13:0] v0_x_out;
  reg [11:0] v0_y_out;
  reg [13:0] v1_x_out;
  reg [11:0] v1_y_out;
  reg [13:0] v2_x_out;
  reg [11:0] v2_y_out;
  reg [1:0] poly_enable_out;


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
