# Makefile to run all tests

# Default make just contains top level for GDS testing
all:
	make -f Makefile.1  SAVE_IMGS=False

clean:
	rm -f -r sim_build/rtl
	rm -f results.xml
	rm -f results_pixel_core.xml
	rm -f results_raster_core.xml
	rm -f results_ray_tracer_core.xml
	rm -f results_inverse.xml
	rm -f results_frontend.xml
	rm -f results_vga.xml

# Test job in CI should build all unit tests
ci:
	make -f Makefile.1  SAVE_IMGS=False
	rm -f -r sim_build/rtl
	make -f Makefile.2  SAVE_IMGS=False
	rm -f -r sim_build/rtl
	make -f Makefile.3  SAVE_IMGS=False
	rm -f -r sim_build/rtl
	make -f Makefile.6
	rm -f -r sim_build/rtl
	make -f Makefile.7

# Unit tests for pixel core
pixel_core:
	rm -f -r sim_build/rtl
	make -f Makefile.2 SAVE_IMGS=True

# Unit tests for raster core
raster_core:
	rm -f -r sim_build/rtl
	make -f Makefile.3 SAVE_IMGS=True

# Unit tests for ray tracing core
ray_trace:
	rm -f -r sim_build/rtl
	make -f Makefile.4

# Unit tests for inverse approximation
inverse:
	rm -f -r sim_build/rtl
	make -f Makefile.5

# Unit tests for frontend
frontend:
	rm -f -r sim_build/rtl
	make -f Makefile.6

# Unit tests for vga
vga:
	rm -f -r sim_build/rtl
	make -f Makefile.7

# Unit tests for top level module
top:
	rm -f -r sim_build/rtl
	make -f Makefile.1 SAVE_IMGS=True

# Gatelevel tests
gatelevel:
	rm -f -r sim_build/rtl
	make -f Makefile.1 SAVE_IMGS=True GATES=yes