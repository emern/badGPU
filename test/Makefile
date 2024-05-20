# Makefile to run all tests

all:
	make -f Makefile.1

clean:
	rm -f -r sim_build/rtl
	rm -f results.xml
	rm -f results_pixel_core.xml
	rm -f results_raster_core.xml
	rm -f results_ray_tracer_core.xml

# Unit tests for pixel core
pixel_core:
	make -f Makefile.2

# Unit tests for raster core
raster_core:
	make -f Makefile.3

ray_trace:
	make -f Makefile.4