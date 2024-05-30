/*
 * Copyright (c) 2024 Emery Nagy
 * SPDX-License-Identifier: Apache-2.0
 */

// GPU frontend recieves SPI data and stores polygon information

`default_nettype none

`define SPI_CMD_WRITE_POLY_A 8'h80
`define SPI_CMD_CLEAR_POLY_A 8'h40
`define SPI_CMD_WRITE_POLY_B 8'h81
`define SPI_CMD_CLEAR_POLY_B 8'h41
`define SPI_CMD_SET_BG_COLOR 8'h01


module tt_um_emern_frontend (
    input clk,
    input rst_n,

    // SPI params
    input cs_in,
    input mosi_in,
    output miso_out,
    input sck_in,
    input en_load,

    // Stored outputs
    output [5:0] bg_color_out, // Background register
    output [11:0] poly_color_out, // Packed polygon color
    output [13:0] v0_x_out, // Packed polygon v0 x
    output [11:0] v0_y_out, // Packed polygon v0 y
    output [13:0] v1_x_out, // Packed polygon v1 x
    output [11:0] v1_y_out, // Packed polygon v1 y
    output [13:0] v2_x_out, // Packed polygon v2 x
    output [11:0] v2_y_out, // Packed polygon v2 y
    output [1:0] poly_enable_out // Enable polygons individually
);

    // Stored polygon and screen data
    reg [5:0] bg_color;
    reg [1:0] poly_en;

    // Polygon A
    reg [5:0] poly_a_color;
    reg [6:0] poly_a_v0_x;
    reg [6:0] poly_a_v1_x;
    reg [6:0] poly_a_v2_x;
    reg [5:0] poly_a_v0_y;
    reg [5:0] poly_a_v1_y;
    reg [5:0] poly_a_v2_y;

    // Polygon B
    reg [5:0] poly_b_color;
    reg [6:0] poly_b_v0_x;
    reg [6:0] poly_b_v1_x;
    reg [6:0] poly_b_v2_x;
    reg [5:0] poly_b_v0_y;
    reg [5:0] poly_b_v1_y;
    reg [5:0] poly_b_v2_y;

    // SPI data
    reg [52:0] spi_buf_reversed;
    wire [52:0] spi_buf;
    reg [5:0] spi_counter;
    reg [2:0] sck_buf;
    reg [1:0] cs_buf;
    reg [1:0] mosi_buf;

    assign miso_out = 0;

    // SPI data registers are shift registers to handle timing
    always @(posedge clk) begin
        if (rst_n == 1'b0) begin
            sck_buf <= 0;
            cs_buf <= 0;
            mosi_buf <= 0;
        end
        else begin
            sck_buf <= {sck_buf[1:0], sck_in};
            cs_buf <= {cs_buf[0], cs_in};
            mosi_buf <= {mosi_buf[0], mosi_in};
        end
    end

    // SPI buffer and counter
    always @(posedge clk) begin
        if (cs | (rst_n == 1'b0)) begin
            // CS high means SPI should be not active
            spi_counter <= 0;
            spi_buf_reversed <= 0;
        end
        else if ((sck_rise & en_load) & ~spi_complete) begin
            // Run off the rising edge of the SPI clock
            // Only accept SPI communication when we are in the HSYNC section of the VGA display
            // Optionally, SPI communication is allowed when the display is turned off
            // Also do not update the spi buffer or counter once the buffer has been filled
            spi_counter <= spi_complete ? 6'd0 : (spi_counter + 1'b1);
            spi_buf_reversed <= {spi_buf_reversed[51:0], mosi};
        end
    end

    // Detect rise and fall in SCK
    wire sck_rise = (sck_buf[2:1] == 2'b01);

    // For actual MOSI and cs_in data we do not care about the signal edges
    wire mosi = mosi_buf[1];
    wire cs = cs_buf[1];

    // All CMDS are CMD byte + 6 byte payload
    // SPI transfer is complete after 53 bits are finalized
    wire spi_complete = (spi_counter == 6'b110101);

    // Actual SPI buffer is the reversed version of the full bus since host processor streams data with LSB first
    genvar i;
    generate
        for (i=0; i<53; i=i+1) begin: reverse
            assign spi_buf[i]=spi_buf_reversed[53-i-1];
        end
    endgenerate

    // First received byte is the cmd byte
    wire [7:0] spi_cmd = spi_buf[7:0];

    // Save incoming data once SPI buffer is full
    always @(posedge clk) begin
        if (rst_n == 1'b0) begin
            // 0 out all registers
            bg_color <= 0;
            poly_en <= 0;
            poly_a_color <= 0;
            poly_a_v0_x <= 0;
            poly_a_v1_x <= 0;
            poly_a_v2_x <= 0;
            poly_a_v0_y <= 0;
            poly_a_v1_y <= 0;
            poly_a_v2_y <= 0;
            poly_b_color <= 0;
            poly_b_v0_x <= 0;
            poly_b_v1_x <= 0;
            poly_b_v2_x <= 0;
            poly_b_v0_y <= 0;
            poly_b_v1_y <= 0;
            poly_b_v2_y <= 0;
        end
        else if (spi_complete == 1'b1) begin
            case(spi_cmd)
                `SPI_CMD_WRITE_POLY_A: begin
                    // Polygon A data comes as a packed struct
                    poly_a_color <= spi_buf[13:8];
                    poly_a_v0_x <= spi_buf[20:14];
                    poly_a_v1_x <= spi_buf[27:21];
                    poly_a_v2_x <= spi_buf[34:28];
                    poly_a_v0_y <= spi_buf[40:35];
                    poly_a_v1_y <= spi_buf[46:41];
                    poly_a_v2_y <= spi_buf[52:47];
                    poly_en[0] <= 1'b1;
                end
                `SPI_CMD_CLEAR_POLY_A: begin
                    poly_a_color <= 0;
                    poly_a_v0_x <= 0;
                    poly_a_v1_x <= 0;
                    poly_a_v2_x <= 0;
                    poly_a_v0_y <= 0;
                    poly_a_v1_y <= 0;
                    poly_a_v2_y <= 0;
                    poly_en[0] <= 1'b0;
                end
                `SPI_CMD_WRITE_POLY_B: begin
                    // Polygon B data comes as a packed struct
                    poly_b_color <= spi_buf[13:8];
                    poly_b_v0_x <= spi_buf[20:14];
                    poly_b_v1_x <= spi_buf[27:21];
                    poly_b_v2_x <= spi_buf[34:28];
                    poly_b_v0_y <= spi_buf[40:35];
                    poly_b_v1_y <= spi_buf[46:41];
                    poly_b_v2_y <= spi_buf[52:47];
                    poly_en[1] <= 1'b1;
                end
                `SPI_CMD_CLEAR_POLY_B: begin
                    poly_b_color <= 0;
                    poly_b_v0_x <= 0;
                    poly_b_v1_x <= 0;
                    poly_b_v2_x <= 0;
                    poly_b_v0_y <= 0;
                    poly_b_v1_y <= 0;
                    poly_b_v2_y <= 0;
                    poly_en[1] <= 1'b0;
                end
                `SPI_CMD_SET_BG_COLOR: begin
                    bg_color <= spi_buf[13:8];
                end
            endcase
        end
    end


    // Output assignment
    assign bg_color_out = bg_color;
    assign poly_color_out = {poly_b_color, poly_a_color};
    assign v0_x_out = {poly_b_v0_x, poly_a_v0_x};
    assign v0_y_out = {poly_b_v0_y, poly_a_v0_y};
    assign v1_x_out = {poly_b_v1_x, poly_a_v1_x};
    assign v1_y_out = {poly_b_v1_y, poly_a_v1_y};
    assign v2_x_out = {poly_b_v2_x, poly_a_v2_x};
    assign v2_y_out = {poly_b_v2_y, poly_a_v2_y};
    assign poly_enable_out = poly_en;

endmodule