EMIR tutorials
==============

Welcome. This is page shows tutorials of the data reduction pipelines (DRP) 
of the instrument EMIR_ at GTC_.

EMIR is a **wide-field, near-infrared, multi-object spectrograph** 
installed at the Nasmyth focus of GTC. Its MOS mode allows observers to obtain
**tens of intermediate-resolution spectra simultaneously** in the nIR bands *Y,
J, H* and *K*. EMIR is designed to address the science goals of the proposing
team and of the Spanish community at large.

Documentation maintainers: Nicolás Cardiel (cardiel@ucm.es) and Sergio Pascual
(sergiopr@fis.ucm.es).

These tutorials have benefited from the work of Cristina Cabello
(criscabe@ucm.es), who has
tested the code in detail on data reduction related to the `GOYA
<http://research.iac.es/proyecto/goya/>`_ project.

.. warning::

   If you are reducing EMIR data obtained with read-out mode RAMP, please,
   have a look to the instructions provided at `Checking the RAMPs
   <http://research.iac.es/proyecto/emir/pages/observing-with-emir/observing-utilities/checking-ramp-raw-data.php>`_.

   It is very easy to check the employed read-out mode using the auxiliary
   script ``fitsheader`` (provided in the astropy package). For example:

   ``$ fitsheader *.fits -k readmode -f``


.. only:: html

   Document index:

.. toctree::
   :maxdepth: 1

   preliminaries/preliminaries
   tutorial_imaging/index
   tutorial_mos/index
   tutorial_flat/index
   
.. _GTC: http://www.gtc.iac.es
.. _EMIR: http://www.gtc.iac.es/instruments/emir
