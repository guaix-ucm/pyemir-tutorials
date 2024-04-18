=======================
Preliminary combination
=======================

.. warning::

   Before continuing, make sure that you have already initialize the file tree
   structure by following the instructions provided in the
   :ref:`initial_file_tree` section of this documentation.


Assume you want to combine the following raw images obtained using a dithered
pattern of 7 positions iterated twice (i.e., you have gathered a total of 14
images):

::

   0001877553-20181217-EMIR-STARE_IMAGE.fits
   0001877559-20181217-EMIR-STARE_IMAGE.fits
   0001877565-20181217-EMIR-STARE_IMAGE.fits
   0001877571-20181217-EMIR-STARE_IMAGE.fits
   0001877577-20181217-EMIR-STARE_IMAGE.fits
   0001877583-20181217-EMIR-STARE_IMAGE.fits
   0001877589-20181217-EMIR-STARE_IMAGE.fits
   0001877595-20181217-EMIR-STARE_IMAGE.fits
   0001877601-20181217-EMIR-STARE_IMAGE.fits
   0001877607-20181217-EMIR-STARE_IMAGE.fits
   0001877613-20181217-EMIR-STARE_IMAGE.fits
   0001877619-20181217-EMIR-STARE_IMAGE.fits
   0001877625-20181217-EMIR-STARE_IMAGE.fits
   0001877631-20181217-EMIR-STARE_IMAGE.fits   

Those files (together with some additional files that you will need to follow
this imaging example) are available as a compressed tgz file:
`pyemir_imaging_tutorial_v4.tgz
<https://guaix.fis.ucm.es/data/pyemir/pyemir_imaging_tutorial_v4.tgz>`_.

The preliminary combination of these 14 images will be carried out in two
steps:

- **Step 1:** basic reduction of each individual image: bad-pixel masking,
  flatfielding and reprojection (the latter only since PyEmir version 0.17.0)

- **Step 2:** actual combination of the images


Step 1: basic reduction of individual exposures
-----------------------------------------------

Move to the directory where you have deployed the initial file tree structure
containing the basic PyEmir calibration files (see  :ref:`initial_file_tree`).


Decompress there the previously mentioned tgz file:

::

   (emir) $ tar zxvf pyemir_imaging_tutorial_v4.tgz
   ...
   ...
   (emir) $ rm pyemir_imaging_tutorial_v4.tgz

This action should have populated the file tree with the 
14 scientific raw FITS (placed wihtin the ``data``
subdirectory) and some additional auxiliary files:

::

   (emir) $ tree
   .
   ├── control.yaml
   ├── data
   │   ├── 0001877553-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877559-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877565-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877571-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877577-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877583-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877589-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877595-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877601-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877607-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877613-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877619-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877625-20181217-EMIR-STARE_IMAGE.fits
   │   ├── 0001877631-20181217-EMIR-STARE_IMAGE.fits
   │   ├── master_bpm.fits
   │   ├── master_dark_zeros.fits
   │   ├── master_flat_ones.fits
   │   ├── master_flat_spec.fits
   │   ├── rect_wpoly_MOSlibrary_grism_H_filter_H.json
   │   ├── rect_wpoly_MOSlibrary_grism_J_filter_J.json
   │   ├── rect_wpoly_MOSlibrary_grism_K_filter_Ksp.json
   │   ├── rect_wpoly_MOSlibrary_grism_LR_filter_HK.json
   │   ├── rect_wpoly_MOSlibrary_grism_LR_filter_YJ.json
   │   └── user_offsets.txt
   ├── dithered_ini.yaml
   ├── dithered_v0.yaml
   ├── dithered_v1.yaml
   ├── dithered_v2.yaml
   ├── dithered_v3.yaml
   ├── dithered_v4.yaml
   └── dithered_v5.yaml

You can easily examine the header of the scientific FITS images using the
astropy utility ``fitsheader``:

::

   (emir) $ fitsheader data/0001877* \
     -k nobsblck -k obsblock -k nimgobbl -k imgobbl \
     -k nexp -k exp -k object -k exptime -k readmode \
     -k filter -k grism -k date-obs -k ra -k dec -f > fitsheader_out.txt

The previous command generates a file ``fitsheader_out.txt`` with the contents
of some relevant FITS keywords extracted from the header of the images.

.. literalinclude:: fitsheader_out.txt

Note that:

- the keyword ``OBSBLOCK`` gives the observing block number.

- the keyword ``NIMGOBBL`` provides the total number of images in each
  dithering pattern (7 in this case).

- ``IMGOBBL`` indicates the sequential number within each pattern. This number
  runs from 1 to ``NIMGOBBL``.

- the keyword ``NEXP`` gives the number of exposures taken at each position in
  the dithering pattern before moving to the next one. In this simple example
  this number is 1.

- the keyword ``EXP`` provides de sequential number at each position in the
  dithering pattern. This number runs from 1 to ``NEXP``.

The first steps in the reduction process will be the bad-pixel mask,
flatfielding, and image reprojection.

.. note::

   Remember that the ``numina`` script is the interface with GTC pipelines. 
   In order to execute PyEmir recipes you should type something like:

   ::
   
      (emir) $ numina run <observation_result_file.yaml> -r <requirements_file.yaml>

   where ``<observation_result_file.yaml>`` is an observation result file in 
   YAML format, and ``<requirements_files.yaml>`` is a requirements file, also 
   in YAML format.

   YAML is a human-readable data serialization language (for details see 
   `YAML Syntax
   <https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html>`_)


The deployed file tree already contains the files required
to execute the initial reduction recipe needed in this case: the observation
result file ``dithered_ini.yaml`` and the requirements file ``control.yaml``.
Let's have a look to each of them separately.

**The observation result file:** ``dithered_ini.yaml``

This is what we call an observation result file, which basically contains the
reduction recipes to be applied and the images involved. Note that this
particular file contains 14 blocks, one for each individual image. 

Each block is separated by a line containing just three dashes (``---``):

- Do not forget the separation line ``---`` between blocks (otherwise the 
  pipeline will not recognize where one block ends and the next one begins).

- This separation line must not appear after the last block.


The contents of this file is displayed below,
highlighting the first block (first eight lines):

.. literalinclude:: dithered_ini.yaml
   :lines: 1-125
   :emphasize-lines: 1-8
   :linenos:
   :lineno-start: 1

- The ``id`` value is an arbitrary label that is employed to generate the name
  of two auxiliary subdirectories. In this example the reduction of the first
  block will generate two subdirectories named ``obsid_0001877553_work`` and
  ``obsid_0001877553_results``, where the intermediate results and the final
  results are going to be stored, respectively. Note that we have arbitrarily
  chosen the 10 digits of the unique running number assigned to each image
  obtained with the GTC to build the label.
 
- Not surprisingly, the key ``instrument`` is set to EMIR (do not forget that
  Numina is at present also employed to reduce MEGARA data, and hopefully,
  future GTC instruments).
   
- The key ``mode`` indicates the identification of the reduction recipe
  (``STARE_IMAGE`` in this example). 
     
- The key ``frames`` lists the images to be combined prior to the execution of
  the reduction recipe. In this case a single image has been obtained at each
  point of the dithering pattern before moving to the next location within the
  pattern. For that reason a single image appears in each block. 

- The key ``requirements`` is employed to pass additional parameters to the
  reduction recipe. In this case, we are specifying the reprojection method to
  be employed in order to correct the images from distortions prior to their
  final combination. Since the reprojection is performed using the package
  `reproject <https://reproject.readthedocs.io/en/stable/>`_ we can choose
  between the different resampling algorithms implemented in that package:
  valid values are: ``none`` (no reprojection is performed; this leads to bad
  results when combining dithered images, specially at the final image
  borders), ``interp`` (fastest reprojection method), ``adaptive``, or
  ``exact`` (slowest). Please, have a look to the documentation in the
  `reproject <https://reproject.readthedocs.io/en/stable/>`_ package if you
  need additional information concerning the reprojetion methods. In this 
  example we are using ``interp``, which provides
  good results. PyEmir users can try to use the slower ``adaptive`` or
  ``exact`` methods and compare the final combined images to check for the
  impact of the adopted method (we do not expect important differences).
   
- The key ``enabled: True`` indicates that this block is going to be reduced.
  As it is going to be shown later, the user can easily
  activate/deactivate the execution of particular reduction recipes (i.e.
  blocks in this file) just by modifying this flag.

.. warning::
   
   Since the generation of the file ``dithered_ini.yaml`` can be cumbersome,
   specially
   when the number of images is large, an auxiliary script has been
   incorporated in PyEmir in order to help in its generation.

   In particular, the file used in this example can be easily created using a
   few simple commands:

   ::

      (emir) $ cd data/
      (emir) $ ls 0001877*fits > list_images.txt
      (emir) $ cd ..
      (emir) $ pyemir-generate_yaml_for_dithered_image \
        data/list_images.txt --step 0 --repeat 1 \
        --reprojection interp \
        --outfile dithered_ini.yaml


   Note that a temporary file ``list_images.txt`` is created with a list of the
   the individual exposures. The script
   ``pyemir-generate_yaml_for_dithered_image`` reads that file and generates 
   the observation result file ``dithered_ini.yaml``.

   The parameter ``--step 0``
   indicates that the reduction recipe to be used here is ``STARE_IMAGE``,
   which corresponds to the preliminary image reduction. 

   The parameter ``--repeat 1`` indicates that there is only a single exposure
   at each telescope pointing within the dithering pattern. In a general case
   this number can be greater than one (check the ``NEXP`` keyword in the FITS
   header of the images; this is one of the keywords included in the file
   ``fitsheader_out.txt`` generated above).

   The reprojection method is also indicated by ``--reprojection interp``,
   where the valid options are ``none``, ``interp``, ``adaptive`` or ``exact``.


**The requirements file:** ``control.yaml``

This is the requirements file, containing the expected name of generic 
calibration files. You do not need to modify anything here.

.. literalinclude:: control.yaml
   :linenos:
   :lineno-start: 1

Starting from March 2024, the format of this file has been updated to include calibrations for both the original EMIR detector and the subsequent replacement, the H2RG detector.

**Numina execution**

You are ready to execute the reduction recipe indicated in the file
``dithered_ini.yaml`` (in this case the reduccion recipe named
``STARE_IMAGE``):

::

   (emir) $ numina run dithered_ini.yaml -r control.yaml
   ...
   ...

After the execution of the previous command line, two subdirectories for each
block should have appeared:

::

   (emir) $ ls
   control.yaml              obsid_0001877565_results/ obsid_0001877601_work/
   data/                     obsid_0001877565_work/    obsid_0001877607_results/
   dithered_ini.yaml         obsid_0001877571_results/ obsid_0001877607_work/
   dithered_v0.yaml          obsid_0001877571_work/    obsid_0001877613_results/
   dithered_v1.yaml          obsid_0001877577_results/ obsid_0001877613_work/
   dithered_v2.yaml          obsid_0001877577_work/    obsid_0001877619_results/
   dithered_v3.yaml          obsid_0001877583_results/ obsid_0001877619_work/
   dithered_v4.yaml          obsid_0001877583_work/    obsid_0001877625_results/
   dithered_v5.yaml          obsid_0001877589_results/ obsid_0001877625_work/
   obsid_0001877553_results/ obsid_0001877589_work/    obsid_0001877631_results/
   obsid_0001877553_work/    obsid_0001877595_results/ obsid_0001877631_work/
   obsid_0001877559_results/ obsid_0001877595_work/
   obsid_0001877559_work/    obsid_0001877601_results/

**The** ``work`` **subdirectories**

All the relevant images (scientific and calibrations) involved in the reduction
of a particular block of the observation result file are copied into the
``work`` subdirectories in order to preserve the original files. 

In particular, for the first block:

::

   (emir) $ tree obsid_0001877553_work/
   obsid_0001877553_work/
   ├── 0001877553-20181217-EMIR-STARE_IMAGE.fits
   ├── index.pkl
   ├── mask_bpm.fits
   ├── master_dark_zeros.fits
   └── master_flatframe.fits

*When disk space is an issue, it is possible to execute numina indicating that
links (instead of actual copies of the original raw files) must be placed in
the* ``work`` *subdirectory.* This behaviour is set using the parameter
``--link-files``:

::

   (emir) $ numina run dithered_ini.yaml --link-files -r control.yaml
   ...
   ...

   (emir) $ tree obsid_0001877553_work/
   obsid_0001877553_work/
   ├── 0001877553-20181217-EMIR-STARE_IMAGE.fits -> /Users/cardiel/w/GTC/emir/work/z_tutorials_201907/x/data/0001877553-20181217-EMIR-STARE_IMAGE.fits
   ├── index.pkl
   ├── master_bpm.fits -> /Users/cardiel/w/GTC/emir/work/z_tutorials_201907/x/data/master_bpm.fits
   ├── master_dark_zeros.fits -> /Users/cardiel/w/GTC/emir/work/z_tutorials_201907/x/data/master_dark_zeros.fits
   └── master_flat_spec.fits -> /Users/cardiel/w/GTC/emir/work/z_tutorials_201907/x/data/master_flat_spec.fits


**The** ``results`` **subdirectories**

These subdirectories store the result of the execution of the reduction
recipes. In particular, for the first block:

:: 

   $ tree obsid_0001877553_results/
   obsid_0001877553_results/
   ├── processing.log
   ├── reduced_image.fits
   ├── result.json
   └── task.json
   
Note that although all the reduced images receive the same name in all these
``results`` subdirectories (for this reduction recipe ``reduced_image.fits``),
there is no confusion because the subdirectory name contains a unique label for
each block in the observation result file.


Step 2: image combination
-------------------------

After the basic reduction performed in step 1, we can proceed with the
combination of the images. For that purpose a different reduction recipe must
be employed: ``FULL_DITHERED_IMAGE``. 

This task is carried out using a new
observation result file: ``dithered_v0.yaml``: the first 125 lines of this new
file are the same as the content of the the previous file
``dithered_ini.yaml``, but setting ``enabled: False`` in each of the 14 blocks.
This flag indicates that the execution of the recipe ``STARE_IMAGE`` is no
longer necessary in any of the 14 blocks. **Note however that these blocks must
explicitly appear in the observation result file, even though they imply no
actual reduction, because they define the location of the previously reduced
images**.

The new observation result file ``dithered_v0.yaml`` contains a new block at
the end (see lines 127-149 below), that is responsible of the execution of the
combination of the previously reduced images:

.. literalinclude:: dithered_v0.yaml
   :lines: 1-149
   :emphasize-lines: 127-149
   :linenos:
   :lineno-start: 1

The new block (lines 127-149) indicates that the reduction recipe
``FULL_DITHERED_IMAGE`` must be executed using as input the results of the
previous blocks. In particular, the ``id's`` of the initial 14 blocks are given
under the ``children:`` keyword (lines 131 to 144).

In addition, a few parameters (which will be modified later) are set to some
default values in this initial combination:

- ``iterations: 0``: this parameter indicates whether an object mask is
  employed or not. A value of ``0`` means that no object mask is computed. Note
  that an object mask allows a better sky background determination since bright
  objects are removed prior to the sky signal estimation. When this parameter
  is greater than zero, an object mask is created by performing a
  SEXtractor-like object search in the resulting image at the end of the
  previous iteration.

- ``sky_images: 0``: number of images employed to determine the sky background
  of each pixel. Setting this parameter to ``0`` indicates that the sky
  background is simply computed as the median value in the same image in which
  the pixel background is being estimated. Using a value larger than zero sets
  the number of closest images (in time) where the signal of a particular pixel
  is averaged (for example, a value of ``6`` will tipically mean that the sky
  background will be estimated using 3 images acquired before and 3 images
  acquired after the current one; note that at the beginning and at the end of
  a given observation sequence, the closest nearby images correspond to
  exposures obtained only after or only before the current one, respectively).

- ``refine_offsets: False``: this flag indicates whether the offsets between
  images must be refined using cross-correlation of subimages around the
  brightest objects.

As it will be explained later, the use of these parameters can help to obtain
better results. So far we are only interested in showing a fast way to generate
a combined image.

.. warning::

   The file ``dithered_v0.yaml`` can also be automatically generated using
   the same script previously mentioned in step 1:

   ::

      (emir) $ pyemir-generate_yaml_for_dithered_image \
        data/list_images.txt --step 1 --repeat 1 \
        --reprojection interp \
        --obsid_combined combined_v0 \
        --outfile dithered_v0.yaml

   Note that here we are using ``--step 1`` instead of ``--step 0``. In
   addition, a new parameter ``--obsid_combined combined_v0`` has also been
   employed in order to set the ``id`` of the block responsible for the
   execution of the combination recipe.

   Do not miss the ``--repeat <NEXP>`` parameter (in this example
   ``NEXP=1``).

The combination of the images is finally performed using numina:

::

   (emir) $ numina run dithered_v0.yaml --link-files -r control.yaml

The previous execution also generates two auxiliary subdirectories ``work`` and
``results``. The resulting combined image can be found in
``obsid_combined_v0_result/reduced_image.fits``:

::

   (emir) $ tree obsid_combined_v0_results/
   obsid_combined_v0_results/
   ├── processing.log
   ├── reduced_image.fits
   ├── result.json
   └── task.json

You can display the image using ``ds9``, using ``numina-ximshow`` (the display
tool shipped with numina based on matplotlib), or with any other tool:

::

   (emir) $ numina-ximshow obsid_combined_v0_results/reduced_image.fits


.. generada con --geometry 0,0,850,1200  
.. (--geometry 0,0,567,800 en el MacBook Pro)
.. convert image.png -trim image_trimmed.png
.. image:: combined_v0_trimmed.png
   :width: 100%
   :alt: combined image, version 0

It is clear that this combined image is far from perfect. In particular, there
are inhomogeneities in the background level, which are easier to see at the
image borders. In addition, the objects appear elongated, which indicates that
the offsets between individual exposures, determined from the WCS header
information, are not suficiently precise. The zoomed region shown in the next
image reveals that the problem is not negligible:

.. generada con --geometry 0,0,850,1200 --bbox 1100,1600,800,1300
.. (--geometry 0,0,576,800 en el MacBook Pro)
.. convert image.png -trim image_trimmed.png
.. image:: combined_v0_zoom_trimmed.png
   :width: 100%
   :alt: combined image, version 0

In addition, the superflatfield computed when combining the individual
exposures does exhibit a doughnut-like shape that must be taken account
(something that we have not yet done). In particular, the image
``obsid_combined_v0_work/superflat_comb_i0.fits`` has the following aspect:

.. generada con --geometry 0,0,850,1200  
.. (--geometry 0,0,567,800 en el MacBook Pro)
.. convert image.png -trim image_trimmed.png
.. image:: superflat_v0_trimmed.png
   :width: 100%
   :alt: superflatfield, version 0

In the next section we are showing several alternatives to handle the previous
issues and improve the image combination.
