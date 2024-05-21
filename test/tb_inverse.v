`default_nettype none
`timescale 1ns / 1ps

module tb_inverse ();

  initial begin
    $dumpfile("tb_inverse.vcd");
    $dumpvars(0, tb_inverse);
    #1;
  end

  reg [12:0] determinant; // packed determinant, signed

  reg inv_det_negative; // flag for negative result
  reg [22:0] inv_det; // lower 23 bits of the QM,Q23 fixed point inverse determinant

  tt_um_emern_inverse user_project (
    .determinant(determinant),

    .inv_det_negative(inv_det_negative),
    .inv_det(inv_det)
  );

endmodule
