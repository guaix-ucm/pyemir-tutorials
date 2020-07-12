Data reduction
==============

Data organization
-----------------

MEGARA DRP uses its own data organization to work. We need a directory named 
MEGARA, in our example this directoryis under data_reduction/::

(megara) bash-3.2$ pwd/Users/acm/Desktop/data_reduction/MEGARA

Under the MEGARA/directory we need to have the calibration tree with the 
specific name ca3558e3-e50d-4bbc-86bd-da50a0998a48/, which is the string that 
uniquely identifies the instrument configuration (a different name was, for 
example, used during laboratory integration at LICA-UCM). Under the MEGARA/
directory we can also have the requirements file named control.yaml needed 
to run the pipeline (see section 5.3; note that the tree command 
shown below might not be available in certain unix distributions; 
use “ls” instead).

::

    (megara) bash-3.2$ tree -L 2
    .
    └── MEGARA
        ├── M15
        ├── M71
        ├── ca3558e3-e50d-4bbc-86bd-da50a0998a48
        └── control.yaml

The requirements file control.yaml contains the path for your MEGARA/
directory:

rootdir: /Users/acm/Desktop/data_reduction

and useful information for performing the wavelength calibration of each VPH, 
including the number of emission lines, wavelength ranges and degree of 
polynomial fit to be used by the wavelength calibration recipe.
In this file you can also specify the name for the extinction curve file used
for the flux calibration recipe. This is simply an ASCII file with two 
space-separated columns, one with the wavelength in Angstroms and another with 
the magnitudes of extinction per unit airmass at the corresponding wavelength, 
i.e. the same format used for extinction curves within IRAF. 
We strongly recommend to use the standard extinction curve of 
the Roque de los Muchachos Observatory.  

(megara) bash-3.2$ more control.yaml version: 1rootdir: /Users/acm/Desktop/REDUCTION_MEGARA/reduction_GTC_comproducts:MEGARA:-{id: 2, type: 'ReferenceExtinctionTable', tags: {}, content: 'extinction_LP.txt'}requirements:MEGARA:default:MegaraArcCalibration:-{name: nlines, tags: {vph: LR-U, speclamp: ThAr, insmode: LCB}, content: [25,25]}-{name: nlines, tags: {vph: LR-U, speclamp: ThAr, insmode: MOS}, content: [25,25]}-{name: nlines, tags: {vph: LR-B, speclamp: ThAr, insmode: LCB}, content: [10,10,15,5]}-{name: nlines, tags: {vph: LR-B, speclamp: ThAr, insmode: MOS}, content: [10,10,15,5]}-{name: nlines, tags: {vph: LR-V, speclamp: ThAr, insmode: LCB}, content: [15,5,10,7]}-{name: nlines, tags: {vph: LR-V, speclamp: ThAr, insmode: MOS}, content: [15,5,10,7]}-{name: nlines, tags: {vph: LR-R, speclamp: ThAr, insmode: LCB}, content: [14,7]}-{name: nlines, tags: {vph: LR-R, speclamp: ThAr, insmode: MOS}, content: [14,7]}-{name: nlines, tags: {vph: LR-I, speclamp: ThAr, insmode: LCB}, content: [14]}-{name: nlines, tags: {vph: LR-I, speclamp: ThAr, insmode: MOS}, content: [14]}-{name: nlines, tags: {vph: LR-Z, speclamp: ThNe, insmode: LCB}, content: [14,9]}-{name: nlines, tags: {vph: LR-Z, speclamp: ThNe, insmode: MOS}, content: [14,9]}-{name: nlines, tags: {vph: MR-U, speclamp: ThAr, insmode: LCB}, content: [8,10]}-{name: nlines, tags: {vph: MR-U, speclamp: ThAr, insmode: MOS}, content: [8,10]}-{name: nlines, tags: {vph: MR-UB, speclamp: ThAr, insmode: LCB}, content: [20]}-{name: nlines, tags: {vph: MR-UB, speclamp: ThAr, insmode: MOS}, content: [20]}-{name: nlines, tags: {vph: MR-B, speclamp: ThAr, insmode: LCB}, content:[11]}-{name: nlines, tags: {vph: MR-B, speclamp: ThAr, insmode: MOS}, content: [11]}-{name: nlines, tags: {vph: MR-G, speclamp: ThAr, insmode: LCB}, content: [10,10,8]}-{name: nlines, tags: {vph: MR-G, speclamp: ThAr, insmode: MOS}, content: [10,10,8]}-{name: nlines, tags: {vph: MR-V, speclamp: ThAr, insmode: LCB}, content: [13,8]}-{name: nlines, tags: {vph: MR-V, speclamp: ThAr, insmode: MOS}, content: [13,8]}-{name: nlines, tags: {vph: MR-VR, speclamp: ThNe, insmode: LCB}, content: [14]}-{name: nlines, tags: {vph: MR-VR, speclamp: ThNe, insmode: MOS}, content: [14]}-{name: nlines, tags: {vph: MR-R, speclamp: ThNe, insmode: LCB}, content: [9]}-{name: nlines, tags: {vph: MR-R, speclamp: ThNe, insmode: MOS}, content: [9]}-{name: nlines, tags: {vph: MR-RI, speclamp: ThNe, insmode: LCB}, content: [7]}-{name: nlines, tags: {vph: MR-RI, speclamp: ThNe, insmode: MOS}, content: [7]}-{name: nlines, tags: {vph: MR-I, speclamp: ThNe, insmode: LCB}, content: [5,5,5]}-{name: nlines, tags: {vph: MR-I, speclamp: ThNe, insmode: MOS}, content: [5,5,5]}-{name: nlines, tags: {vph: MR-Z, speclamp: ThNe, insmode: LCB}, content: [4,5,3]}-{name: nlines, tags: {vph: MR-Z, speclamp: ThNe, insmode: MOS}, content: [4,5,3]}
-{name: nlines, tags: {vph: HR-R, speclamp: ThNe, insmode: LCB}, content: [5]}-{name: nlines, tags: {vph: HR-R, speclamp: ThNe, insmode: MOS}, content: [5]}-{name: nlines, tags: {vph: HR-I, speclamp: ThNe, insmode: LCB}, content: [10]}-{name: nlines, tags: {vph:HR-I, speclamp: ThNe, insmode: MOS}, content: [10]}-{name: polynomial_degree, tags: {vph: LR-U, speclamp: ThAr}, content: [3,5]}-{name: polynomial_degree, tags: {vph: LR-B, speclamp: ThAr}, content: [5,5]}-{name: polynomial_degree,tags: {vph: LR-V, speclamp: ThAr}, content: [5,5]}-{name: polynomial_degree, tags: {vph: LR-R, speclamp: ThAr}, content: [3,5]}-{name: polynomial_degree, tags: {vph: LR-I, speclamp: ThAr}, content: [3,5]}-{name: polynomial_degree, tags: {vph: LR-Z, speclamp: ThNe}, content: [3,5]}-{name: polynomial_degree, tags: {vph: MR-U, speclamp: ThAr}, content: [3,5]}-{name: polynomial_degree, tags: {vph: MR-UB, speclamp: ThAr}, content: [3,5]}-{name: polynomial_degree, tags: {vph: MR-B, speclamp: ThAr}, content: [3,5]}-{name: polynomial_degree, tags: {vph: MR-G, speclamp: ThAr}, content: [3,5]}-{name: polynomial_degree, tags: {vph: MR-V, speclamp: ThAr}, content: [3,5]}-{name: polynomial_degree, tags: {vph: MR-VR, speclamp: ThNe}, content: [3,5]}-{name: polynomial_degree, tags: {vph: MR-R, speclamp: ThNe}, content: [3,3]}-{name: polynomial_degree, tags: {vph: MR-RI, speclamp: ThNe}, content: [3,3]}-{name: polynomial_degree, tags: {vph: MR-I, speclamp: ThNe}, content: [3,5]}-{name: polynomial_degree, tags: {vph: MR-Z, speclamp: ThNe}, content: [3,3]}-{name: polynomial_degree, tags: {vph: HR-R, speclamp: ThNe}, content: [3,5]}-{name: polynomial_degree, tags: {vph: HR-I, speclamp: ThNe}, content: [3,5]}


Another fundamental function of the calibration 
tree (ca3558e3-e50d-4bbc-86bd-da50a0998a48/) is to host the calibration 
products that will be used by the corresponding recipes, such as the 
MasterBias, MasterFiberFlat, MasterSensitivity, etc. 
Thus, once the files for these calibrations are generated, they should be 
copied under this calibration tree according structure below. 
Since the DRP would read the first file in alphabetical order inside the 
corresponding folder, we recommend to place only one file in each folder.   

::

    (megara) bash-3.2$ tree ca3558e3-e50d-4bbc-86bd-da50a0998a48/ -L 2
    ca3558e3-e50d-4bbc-86bd-da50a0998a48/
    ├── LinesCatalog
    │   ├── ThAr
    │   └── ThNe
    ├── MasterBPM
    │   └── master_bpm.fits
    ├── MasterBias
    │   └── master_bias.fits
    ├── MasterFiberFlat
    │   ├── LCB
    │   └── MOS
    ├── MasterSensitivity
    │   ├── LCB
    │   └── MOS
    ├──MasterSlitFlat
    │  
    ├── MasterTwilightFlat
    │   ├── LCB
    │   ├── ModelMap
    │   ├── LCB
    │   └── MOS
    ├── TraceMap
    │   ├── LCB
    │   └── MOS
    └── WavelengthCalibration
        ├── LCB
        └── MOS


The  content  for  the LinesCatalog/ is specific for  each VPH 
(line  lists  for  all  VPHs  can  be  found  at 
`https://zenodo.org/record/2270518#.XRx9HKZS9E4`). 
In the following example the calibration files for the HR-R 
(LCB observing mode) and LR-R (MOS observing mode) VPHs are shown.
When other VPHs are used, the user just needs to create the corresponding 
folders. It is recommended to have only one file in each calibration directory.
For example,for the same VPH you can have several `master_traces.json` 
files with the information to trace the fibers light through the detector 
at thesame day but at different ambient temperatures.

Different files can be stored atthe same directory, but the DRP is going to 
use the first file it encounters in alphabetical order. The user can name 
the desired file with prefix 00 (e.g. `00_master_traces.json`) to be sure 
this is the file to be used by the DRP. Note that the sorting of files 
named `00_` and `000_` might be different for the operative system and 
for the MEGARA DRP, so avoid making abusive use of these prefixes.

Furthermore,the user’s MEGARA/ directory can contain data for your targets 
under different directories (in this example our targets are the M15 and M71 
globular clusters). Your raw data should always be included in a 
subdirectory named data/ within each working target directory (M15, M71, etc.).
Images can be stored gzipped but then the observation-result files 
should list the images with the .gz extension. 
The different observation-result files (`*.yaml`) used during the data 
reduction process should be also located within each target directory 
as they will be different for each target. 
In this example, the observation-resultfiles in YAML format are named 
with a first number related with the order they are run.

.. toctree::
   :maxdepth: 2
   
   bias
