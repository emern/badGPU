/*
 * Copyright (c) 2024 Emery Nagy
 * SPDX-License-Identifier: Apache-2.0
 */

// Drive 640x480 VGA display @ 60 hz
// X: 640 + 16 + 96 + 48 = 800
// Y: 480 + 10 + 2 + 33 = 525
//http://www.tinyvga.com/vga-timing/640x480@60Hz

module tt_um_emern_vga(
	input clk,
	input rst_n,
	output h_sync,
    output v_sync,
	output [9:0] row_counter,
	output [9:0] col_counter,
	output screen_inactive,
    output cmd_en
	);

	reg [9:0] x_count;
    reg [9:0] y_count;

    // Horizontal line is in visible portion when x < 640 or when x < 1010000000
    // Total range is 0-800 so we also need to check x < 1100100000
    wire invisible_x = ((&x_count[9:8]) | (&{x_count[9], x_count[7]}));

    // Vertical line is in visible portion when x < 480 or when x < 0111100000
    // Total range is 0-525 so we also need to check x < 1000001101
    wire invisible_y = ((&y_count[9]) | (&y_count[8:5]));

    // Check if x counter is at the boundary (799)
    // 799 = 11???11111, we only can about the exact value
    // Try and do this without full comparitors
    wire x_max = &{x_count[9:8], x_count[4:0]};

    // Check if y counter is at the boundary (524)
    // 524 = 1?????11??, we only can about the exact value
    wire y_max = &{y_count[9], y_count[3:2]};

	assign screen_inactive = (invisible_x | invisible_y);
    assign cmd_en = invisible_y;
	assign h_sync = ~ ((x_count > 10'd655) & (x_count < 10'd752));
    // Sync pulse on y=490 and y=491 only
    // Slight optimization: Do this bitwise
    // 490/491 = x11110101x since the range of y_count is up to 525
	assign v_sync = ~ (y_count[8:1] == 8'b11110101);

    assign row_counter = y_count;
    assign col_counter = x_count;
	
	always @(posedge clk) begin
		if (rst_n == 1'b0) begin
            x_count <= 0;
            y_count <= 0;
		end
		else begin
            if (x_max) begin
                // x counter saturated
                x_count <= 0;
                if (y_max) begin
                    // y counter saturated
                    y_count <= 0;
                end
                else begin
                    y_count <= y_count + 1'b1;
                end
            end
            else begin
                x_count <= x_count + 1'b1;
            end
        end
	end
	
endmodule
