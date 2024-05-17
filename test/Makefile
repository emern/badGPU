# Makefile to run all tests

all: 
	make -f Makefile.1 results.xml

pixel_core:
	rm -f sim_build/rtl/sim.vvp
	rm -f sim_build/rtl/cmds.f
	make -f Makefile.2

raster_core:
	rm -f sim_build/rtl/sim.vvp
	rm -f sim_build/rtl/cmds.f
	make -f Makefile.3