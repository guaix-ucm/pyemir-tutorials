
.. _IMAGING_tutorial:

########################################################
Imaging mode tutorial: combination of dithered exposures
########################################################

.. warning::

   All the commands are assumed to be executed in a terminal running the **bash
   shell** (or a compatible one).

   Don't forget to activate the same Python environment employed to install
   PyEmir.  In this document, the prompt ``(emir) $`` will indicate that this
   is the case.

This tutorial provides an easy introduction to the use of PyEmir (via Numina),
focusing on the combination of dithered exposures.

For detailed documentation concerning the installation of PyEmir, see `PyEmir
Installation
<https://pyemir.readthedocs.io/en/latest/installation/index.html>`_.

We strongly recommend to follow the different sections of this tutorial in the
provided order, starting with the simplest combination method, before
attempting to refine the combination procedure.

.. note::

   - Since PyEmir version 0.17.0 image distortions are corrected by
     reprojecting each individual pointing into a WCS with a constant pixel
     scale in X and Y. For this task we are using the package `reproject
     <https://reproject.readthedocs.io/en/stable/>`_.

     **Important**: the absolute astrometric calibration of the reduced images
     is not guaranteed to be better than a few pixels. This means that the same
     field observed (and reduced) in different times may not overlap perfectly.
     An absolute astrometric calibration will require the comparison of the
     derived astrometry with accurate coordinates of objects in the field of
     view.
     
   - Only integer offsets between (reprojected) images are considered: this is
     not especially important considering that the PSF is well oversampled. The
     benefit of using integer offsets is that we avoid reprojecting the images
     a second time (and we do not increase the reduction time).

.. only:: html

   **Tutorial index:**
   
.. toctree::
   :maxdepth: 2
   
   preliminary_combination
   refined_combination
   
