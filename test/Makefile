# Makefile to run all tests

all:
	make -f Makefile.1
	rm -f -r sim_build/rtl
	make -f Makefile.2
	rm -f -r sim_build/rtl
	make -f Makefile.3

clean:
	rm -f -r sim_build/rtl
	rm -f results.xml
	rm -f results_pixel_core.xml
	rm -f results_raster_core.xml

pixel_core:
	make -f Makefile.2

raster_core:
	make -f Makefile.3