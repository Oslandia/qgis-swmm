QGIS swmm plugin
==================

Extends processing framework to models storm water management systems.

This plugin lets you model hydraulic network for water and run simulations to get water flow rate informations and more.

Requirements
============

You need :
* A working version of SWMM
* QGIS > 2.0
* The QGIS Processing framework

Installation
============

You need to have swmm as a command line tool for the plugin to work.

Install SWMM for Windows
--------------------------

Download and run http://www2.epa.gov/sites/production/files/2014-06/swmm51006_setup_1.exe

Compile SWMM for linux
------------------------

Download Epanet sources from http://www2.epa.gov/sites/production/files/2014-06/swmm51006_engine_0.zip

For linux:

    mkdir swmm
    cd swmm
    wget http://www2.epa.gov/sites/production/files/2014-06/swmm51006_engine_0.zip
    unzip swmm51006_engine_0.zip
    unzip source5_1_006.zip
    unzip -o makefiles.zip 
    unzip -o GNU-CLE.zip

Open the file swmm5.c, comment out the line

    #define DLL

and uncomment the line

    #define CLE

also comment the line
 
    #include <direct.h>

Open the file Makefile and replace the line (line 12)

    cc -o swmm5 -lm $(objs)

by

    cc -o swmm5 $(objs) -lm 

and remove the misplaced backslash from the last line of the objs definition (line 8)

Then run: 
 
    make

Install the plugin
------------------
 
Simply put this directory in the plugin directory. On linux:

    cd ~/.qgis2/python/plugins
    git clone https://github.com/Oslandia/qgis-swmm.git

You then need to run QGIS, install the processing plugin and configure the path to the swmm executable in QGIS menu Processing -> Options and configuration.


Running the example
===================

A simple example is provided to test the plugin. You need a working postgres/postgis server in order to use the example.

First create a test database, from the installation root directory run:

    createdb swmm_test
    psql swmm_test -f example/example1_test_db.sql

Open QGIS, click on 'Add Postgis Layer', configure a new connection to swmm_test database and connect. Check 'Also list tables with no geometry' and select following layers from the plublic schema (layers with geometry are duplicated in the list, make sure you select the entry with a geometry):

- conduits (geom)
- controls
- curves
- evaporation
- inflows
- junctions (geom
- options
- outfalls (geom)
- pumps (geom)
- report
- storage (geom)
- timeseries
- xsections

Open the processing toobox and double-click on the incon Swmm... -> Simulation -> Simulate...

If you are running a fresh buid from QGIS master, the name of the parameters are already set (recognized from layer names). If you running an older version of QGIS, you must set the following parameter:

- Analysis options -> options
- Output reporting instruction -> report
- Evaporation data -> evaporation
- Junctions node information -> junctions
- Outfall node information -> outfalls
- Storage node information -> storage
- Conduit link information -> conduits
- Pump link information -> pumps
- Conduit, orifice, and weir cross-section geometry -> xsections
- Rules that control pump and regulator operation -> controls
- External hydrograph/pollutograph inflow at nodes -> inflows
- x-y tabular data references in other sections -> curves
- Time series data referenced in other sections -> timeseries

Then click on Run. Three result layers should appear in the project once the simualtion is complete.


Credits
=======

This plugin has been developed by Oslandia ( http://www.oslandia.com ).

Oslandia provides support and assistance for QGIS and associated tools, including this plugin.

This work has been funded by European funds.
Thanks to the GIS Office of Apavil, Valcea County (Romania)

Licence
=======

This work is free software and licenced under the GNU GPL version 2 or any later version.
See LICENCE file.

Known issue
===========

In SwmmAlgorithm.py the first argument of subprocess.Popen should be the list [swmm_cli, filename, outfilename], but for some reason this does not seem to work. On windows, if you can't obtain the results after running the example, try changing this line.


