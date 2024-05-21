/*
 * Copyright (c) 2024 Emery Nagy
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Determinant inverse fits in Q23.23
`define QM 23
`define QF 23

module tt_um_emern_ray_tracer_core (
    input [9:0] pixel_col,
    input [8:0] pixel_row,

    // Triangles are stored by their two edges and based point

    // Edge 1 data - signed
    input [10:0] edge_1_x,
    input [9:0] edge_1_y,
    input [3:0] edge_1_z,

    // Edge 2 data - signed
    input [10:0] edge_2_x,
    input [9:0] edge_2_y,
    input [3:0] edge_2_z,

    // Vertex 0 data
    input [9:0] vertex_0_x,
    input [8:0] vertex_0_y,
    input [2:0] vertex_0_z,

    // Pre-computed triangle values
    input [`QM-1:0] determinant,
    input [`QM-1:-`QF] inv_det,

    output rasterize,
    output [2:0] z_actual
);

    // Calculate the vector S = origin - V0
    wire signed [10:0] s_x = $signed({1'b0, pixel_col}) - $signed({1'b0, vertex_0_x});
    wire signed [10:0] s_y = $signed({2'b00, pixel_row}) - $signed({2'b00, vertex_0_y});
    wire signed [10:0] s_z = ~vertex_0_z + 1'b1; // origin_z = 0

    // Compute Barycentric coordinate: u
    wire signed [`QM-1:0] u = (s_x * $signed(edge_2_y)) + (s_y * $signed(~edge_2_x + 1'b1));

    // Compute vector q -> Cross product :(
    // q = s X edge_1
    wire signed [`QM-1:0] q_x = (s_y * $signed(edge_1_z)) - (s_z * $signed(edge_1_y));
    wire signed [`QM-1:0] q_y = (s_z * $signed(edge_1_x)) - (s_x * $signed(edge_1_z));
    wire signed [`QM-1:0] q_z = (s_x * $signed(edge_1_y)) - (s_y * $signed(edge_1_x));

    // Compute Barycentric coordinate: v
    wire signed [`QM-1:0] v = ~q_z + 1'b1;

    // Calculate unscaled ray vector distance "t" -> z value
    wire signed [`QM:0] unscaled_t = (($signed(edge_2_x) * q_x) + ($signed(edge_2_y) * q_y) + ($signed(edge_2_z) * q_z));

    // Calculate actual ray distance scaled by inverse determinant
    // Extract only the valid section of the ray distance since it is known to only be 3 bits wide
    wire signed [`QM-1+`QF:-`QF] t_exp = ($signed(inv_det) * (unscaled_t <<< `QF));
    // Round up -> Subtract since t values are implicitly negative
    // This fails for the case where t_exp == 0, check to ensure t_exp is negative
    wire [`QM-1:-`QF] t = -$signed((t_exp >> `QF) - (((t_exp[`QF-1] == 1'b0) && (t_exp[`QM-1+`QF] == 1'b1)) ? (1'b1 << `QF) : 1'b0));


    // Extract the only bits of interest here
    assign z_actual = t[2:0];

    wire signed [`QM-1:0] bary_sum = u + v;

    // Do NOT rasterize if (u > a) or (u < 0) or ((u + v) > a) or (v > a) or (v < 0):
    assign rasterize = (u[`QM-1] == 1'b1) ? 1'b0 :
                        (v[`QM-1] == 1'b1) ? 1'b0 :
                        (bary_sum > determinant) ? 1'b0 :
                        (u > determinant) ? 1'b0 :
                        (v > determinant) ? 1'b0 : 1'b1; 

endmodule