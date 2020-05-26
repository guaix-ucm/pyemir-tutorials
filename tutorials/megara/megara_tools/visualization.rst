Visualization
=============

As part of the MEGARA DRP we also provide a tool to visualize the RSS frames 
generated when processing LCB IFU data. This tool is best suited for 
visualizing `final_rss.fits` RSS images (or, equivalently, `reduced_rss.fits` 
images) obtained after running the `MegaraLcbImage` processing recipe. 
The way to execute this code is to use the following command under the 
corresponding MEGARA environment:

::

    (megara) bash-3.2$ python -m megaradrp.visualization test/final_rss_M32_MR-G.fits --label "flux (Jy)" --wcs-grid

As for the other commands, adding the -h flag would provide the help and 
syntax for using this command. The result is the following:

.. program:: visualization

.. option:: --wcs-grid

    Display WCS grid

.. option:: --wcs-pa-from-header 

   Use PA angle from PC keys

.. option:: --average-region AVERAGE_REGION

    Region of the RSS averaged on display

.. option:: --extname EXTNAME, -e EXTNAME

    Name of the extension used

.. option:: --column COLUMN, -c COLUMN
    
    Column of the RSS on display

.. option:: --continuum-region CONTINUUM_REGION CONTINUUM_REGION
    
    Region of the RSS used for continuum subtraction

.. option:: --coordinate-type {pixel,wcs}

    Types of coordinates used

.. option:: --colormap COLORMAP

    Name of a valid matplotlib colormap

.. option:: --plot-sky
    
    Plot SKY bundles

.. option:: --plot-nominal-config

    Plot nominal configuration, do not use the header

.. option:: --hide-values
    
    Do not show values out of range

.. option:: --title TITLE
    
    Title of the plot

.. option:: --label LABEL
    
    Legend of the colorbar

.. option:: --hex-size HEX_SIZE
    
    Size of the hexagons (default is 0.443)

.. option:: --hex-rel-size HEX_REL_SIZE
    
    Scale the size of hexagons by a factor

.. option:: --min-cut MIN_CUT
    
    Inferior cut level

.. option:: --max-cut MAX_CUT
    
    Superior cut level

.. option:: --percent PERCENT
    
    Compute cuts using percentiles

.. option:: --stretch {linear,sqrt,power,log,asinh}
    
    Name of the strech method used for display

contouring:

.. option:: --contour-pixel-size CONTOUR_PIXEL_SIZE
    
    Pixel size in arc seconds for image reconstruction

.. option:: --contour-levels CONTOUR_LEVELS
    
    Contour levels

.. option:: --contour
    
    Draw contours

.. option:: --contour-image CONTOUR_IMAGE
    
    Image for computing contours

.. option:: --contour-image-column CONTOUR_IMAGE_COLUMN
    
    Column of image used for contouring

.. option:: --contour-image-save CONTOUR_IMAGE_SAVE
    
    Save image used for contouring

.. option:: --contour-image-region CONTOUR_IMAGE_REGION
    
    Region of the image used for contouring

.. option:: --contour-is-density 

   The data is a magnitude that does not require scaling

positional arguments:

.. option:: RSS

    RSS images to process

Note that this visualization tool can be also used to display output 
RSS files from the analyze_rss.py tool described below. As an example, the 
command to display the flux the first of the two gaussians fit to a 
specific emission line analyzed with that code would be:

:: 

    (megara) bash-3.2$ python -m megaradrp.visualization test/analyze_rss_Halpha.fits -c 22 --min-cut 10.0 --max-cut 400.0
