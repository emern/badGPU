/*
 * Copyright (c) 2024 Emery Nagy
 * SPDX-License-Identifier: Apache-2.0
 */

/*
 * Compute the approximate inverse of the given polygon determinant
 * Adopted from: https://observablehq.com/@drom/reciprocal-approximation and https://github.com/ameetgohil/reciprocal-sv/blob/master/rtl/reciprocal.sv
 * as well as: https://github.com/algofoogle/raybox-zero/blob/main/src/rtl/reciprocal.v
*/

`default_nettype none

module tt_um_emern_inverse (
    input [12:0] determinant, // packed determinant, signed

    output inv_det_negative, // flag for negative result
    output [22:0] inv_det // lower 23 bits of the QM,Q23 fixed point inverse determinant
);

    // Make the determinant strictly positive for the computation
    wire [12:0] det_negative = ~determinant + 1'b1;
    wire [11:0] det_pos = (determinant[12] == 1'b0) ? determinant[11:0] : det_negative[11:0];
    assign inv_det_negative = determinant[12];

    // Leading zero count lookup
    reg [3:0] lzc;

    // Scale to [0.5, 1] in Q3.23 (signed)
    // We essentially start with an unsigned Q12.23 and slice out Q3.23 with an extra sign bit
    wire [11:-23] a_full = ({det_pos, {(23){1'b0}}} >> (4'd12 - lzc));
    wire signed [3:-23] a = a_full[3:-23];

    // 1.446 in signed Q3.23
    wire signed [3:-23] b = 27'h0BBA5E3 - a;

    wire signed [3 + 23:-23] c = $signed(a) * $signed(b);

    // 1.0012 in signed Q3.23
    wire signed [3:-23] d = 27'h0802752 - $signed(c[26:0]);

    wire signed [3 + 23:-23] e = $signed(d) * $signed(b);

    // Final result, multiplied by 4
    // No need to worry about overflow here since the input is guaranteed to be > 0, we should never saturate the M region of the QM.N fixed point
    wire signed [3:-23] f = e[26:0] << 2;

    // Rescale result by lzc
    // Take lower 23 bits (fractional part)
    // Not worried about overflow since input is always much larger than 0
    wire [3:-35] inv_det_full = f << (lzc);
    assign inv_det = inv_det_full[0:-23];

    // Hardcoded for leading zeros lookup, only need to support range of inputs given by polygon determinants: 64*48 <-> -1*64*48
    always @(*) begin
        casez(det_pos)
            12'b1???_????_????: lzc = 0;
            12'b01??_????_????: lzc = 1;
            12'b001?_????_????: lzc = 2;
            12'b0001_????_????: lzc = 3;
            12'b0000_1???_????: lzc = 4;
            12'b0000_01??_????: lzc = 5;
            12'b0000_001?_????: lzc = 6;
            12'b0000_0001_????: lzc = 7;
            12'b0000_0000_1???: lzc = 8;
            12'b0000_0000_01??: lzc = 9;
            12'b0000_0000_001?: lzc = 10;
            12'b0000_0000_0001: lzc = 11;
            12'b0000_0000_0000: lzc = 12;
            default: lzc = 12;
        endcase
    end


endmodule