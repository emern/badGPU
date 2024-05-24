`default_nettype none
`timescale 1ns / 1ps

module tb_vga ();

  initial begin
    $dumpfile("tb_vga.vcd");
    $dumpvars(0, tb_vga);
    #1;
  end

	reg clk;
	reg rst_n;
	reg h_sync;
  reg v_sync;
	reg [9:0] row_counter;
	reg [9:0] col_counter;
	reg screen_inactive;

  // DUT
  tt_um_emern_vga user_project (
    .clk(clk),
    .rst_n(rst_n),
    .h_sync(h_sync),
    .v_sync(v_sync),
    .row_counter(row_counter),
    .col_counter(col_counter),
    .screen_inactive(screen_inactive)
  );

endmodule
