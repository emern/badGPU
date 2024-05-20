`default_nettype none
`timescale 1ns / 1ps

module tb_ray_tracer_core ();

  // Dump the signals to a VCD file. You can view it with gtkwave.
  initial begin
    $dumpfile("tb_ray_tracer_core.vcd");
    $dumpvars(0, tb_ray_tracer_core);
    #1;
  end

    // Vertex 1 data
    reg [9:0] vertex_1_x;
    reg [8:0] vertex_1_y;
    reg [2:0] vertex_1_z;

    // Vertex 2 data
    reg [9:0] vertex_2_x;
    reg [8:0] vertex_2_y;
    reg [2:0] vertex_2_z;


    // Wire up the inputs and outputs:
    reg [9:0] pixel_col;
    reg [8:0] pixel_row;

    // Triangles are stored by their two edges and based point

    // Edge 1 data - signed
    wire [10:0] edge_1_x = vertex_1_x - vertex_0_x;
    wire [9:0] edge_1_y = vertex_1_y - vertex_0_y;
    wire [3:0] edge_1_z = $signed({1'b0, vertex_1_z}) - $signed({1'b0, vertex_0_z});

    // Edge 2 data - signed
    wire [10:0] edge_2_x = vertex_2_x - vertex_0_x;
    wire [9:0] edge_2_y = vertex_2_y - vertex_0_y;
    wire [3:0] edge_2_z = $signed({1'b0, vertex_2_z}) - $signed({1'b0, vertex_0_z});

    // Vertex 0 data
    reg [9:0] vertex_0_x;
    reg [8:0] vertex_0_y;
    reg [2:0] vertex_0_z;

    // Pre-computed triangle values
    reg [`QM-1:0] determinant;
    reg [`QM-1:-`QF] inv_det;

    reg rasterize;
    reg [2:0] z_actual;

  tt_um_emern_ray_tracer_core user_project (

    .pixel_col(pixel_col),
    .pixel_row(pixel_row),

    // Triangles are stored by their two edges and based point

    // Edge 1 data - signed
    .edge_1_x(edge_1_x),
    .edge_1_y(edge_1_y),
    .edge_1_z(edge_1_z),

    // Edge 2 data - signed
    .edge_2_x(edge_2_x),
    .edge_2_y(edge_2_y),
    .edge_2_z(edge_2_z),

    // Vertex 0 data
    .vertex_0_x(vertex_0_x),
    .vertex_0_y(vertex_0_y),
    .vertex_0_z(vertex_0_z),

    // Pre-computed triangle values
    .determinant(determinant),
    .inv_det(inv_det),

    .rasterize(rasterize),
    .z_actual(z_actual)
  );

endmodule
