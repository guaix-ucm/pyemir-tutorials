#
# Copyright 2011-2012 Universidad Complutense de Madrid
# 
# This file is part of PyEmir
# 
# PyEmir is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PyEmir is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with PyEmir.  If not, see <http://www.gnu.org/licenses/>.
#

'''

Routines shared by image mode recipes

'''
import os
import logging
import shutil
import math
import operator

import numpy
import pyfits
import pywcs
from scipy.spatial import KDTree as KDTree
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib.collections import PatchCollection
from numina import __version__
from numina.recipes import RecipeBase, Parameter, provides, DataFrame
from numina.flow import SerialFlow, Node
from numina.flow.node import IdNode
from numina.flow.processing import BiasCorrector, FlatFieldCorrector
from numina.flow.processing import DarkCorrector, NonLinearityCorrector, BadPixelCorrector
from numina.array import combine_shape
from numina.array import fixpix2
from numina.image import resize_fits, custom_region_to_str
from numina.array import combine_shape, correct_flatfield
from numina.array import subarray_match
from numina.array.combine import flatcombine, median, quantileclip

from numina.util.sextractor import SExtractor
from numina.util.sextractor import open as sopen
import numina.util.sexcatalog as sexcatalog

from emir.dataproducts import SourcesCatalog

_logger = logging.getLogger('emir.recipes')

def name_redimensioned_frames(label, step, ext='.fits'):
    dn = '%s_r%s' % (label, ext)
    mn = '%s_mr%s' % (label, ext)
    return dn, mn

def name_object_mask(label, step, ext='.fits'):
    return '%s_mro_i%01d%s' % (label, step, ext)

def name_skybackground(label, step, ext='.fits'):
    dn = '%s_sky_i%01d%s' % (label, step, ext)
    return dn

def name_skybackgroundmask(label, step, ext='.fits'):
    dn = '%s_skymask_i%01d%s' % (label, step, ext)
    return dn

def name_skysub_proc(label, step, ext='.fits'):
    dn = '%s_rfs_i%01d%s' % (label, step, ext)
    return dn

def name_skyflat(label, step, ext='.fits'):
    dn = 'superflat_%s_i%01d%s' % (label, step, ext)
    return dn

def name_skyflat_proc(label, step, ext='.fits'):
    dn = '%s_rf_i%01d%s' % (label, step, ext)
    return dn

def name_segmask(step, ext='.fits'):
    return "check_i%01d%s" % (step, ext)


def offsets_from_wcs(frames, pixref):
    '''Compute offsets between frames using WCS information.
    
    :parameter frames: sequence of FITS filenames or file descriptors
    :parameter pixref: numpy array used as reference pixel
    
    The sky world coordinates are computed on *pixref* using
    the WCS of the first frame in the sequence. Then, the
    pixel coordinates of the reference sky world-coordinates 
    are computed for the rest of the frames.
    
    The results is a numpy array with the difference between the
    computed pixel value and the reference pixel. The first line
    of the array is [0, 0], being the offset from the first image
    to itself. 
    
    '''
    
    result = numpy.zeros((len(frames), pixref.shape[1]))

    with pyfits.open(frames[0]) as hdulist:
        wcs = pywcs.WCS(hdulist[0].header)
        skyref = wcs.wcs_pix2sky(pixref, 1)

    for idx, frame in enumerate(frames[1:]):
        with pyfits.open(frame) as hdulist:
            wcs = pywcs.WCS(hdulist[0].header)
            pixval = wcs.wcs_sky2pix(skyref, 1)
            result[idx + 1] = pixval[0] - pixref[0]

    return result

def intersection(a, b, scale=1):
    '''Intersection between two segments.'''
    a1, a2 = a
    try:
        b1, b2 = b
    except TypeError:
        b1 = b.start
        b2 = b.stop
        

    if a2 <= b1:
        return None
    if a1 >= b2:
        return None

    # a2 > b1 and a1 < b2

    if a2 <= b2:
        if a1 <= b1:
            return slice(b1 * scale, a2 * scale)
        else:
            return slice(a1 * scale, a2 * scale)
    else:
        if a1 <= b1:
            return slice(b1 * scale, b2 * scale)
        else:
            return slice(a1 * scale, b2 * scale)

def clip_slices(r, region, scale=1):
    '''Intersect slices with a region.''' 
    t = []
    for ch in r:
        a1 = intersection(ch[0], region[0], scale=scale)
        if a1 is None:
            continue
        a2 = intersection(ch[1], region[1], scale=scale)
        if a2 is None:
            continue

        t.append((a1, a2))

    return t

class DirectImageCommon(object):
        
    logger = _logger
    BASIC, PRERED, CHECKRED, FULLRED, COMPLETE = range(5)
    
    def __init__(self, *args, **kwds):
        super(DirectImageCommon, self).__init__()
        
        self._figure = plt.figure(facecolor='white')
        self._figure.canvas.set_window_title('Recipe Plots')
        self._figure.canvas.draw()
    
    def process(self, obresult, baseshape, amplifiers, 
                offsets=None, window=None, 
                subpix=1, store_intermediate=True,
                target_is_sky=True, stop_after=PRERED):
        
        numpy.seterr(divide='raise')
        
        # metadata = self.instrument['metadata']
        # FIXME: hardcoded
        metadata = {
         "juliandate": "MJD-OBS", 
         "airmass": "AIRMASS", 
         "detector.mode": "CCDMODE", 
         "filter0": "FILTER", 
         "imagetype": "IMGTYP", 
         "exposure": "EXPTIME"
        }     
        recipe_result = {'products' : []}

        if window is None:
            window = tuple((0, siz) for siz in baseshape)

        if store_intermediate:
            recipe_result['intermediate'] = []
        
        
        # States
        BASIC, PRERED, CHECKRED, FULLRED, COMPLETE = range(5)
        
        state = BASIC
        step = 0
        
        try:
            niteration = self.parameters['iterations']
        except KeyError:
            niteration = 1
        
        
        while True:
            if state == BASIC:    
                _logger.info('Basic processing')

                # Basic processing
                
                # FIXME: add this
                bpm = pyfits.getdata(self.parameters['master_bpm'])
                
                if self.parameters['master_bias']:
                    mbias = pyfits.getdata(self.parameters['master_bias'])
                    bias_corrector = BiasCorrector(mbias)
                else:
                    bias_corrector = IdNode()
            
                mdark = pyfits.getdata(self.parameters['master_dark'])
                dark_corrector = DarkCorrector(mdark)
                nl_corrector = NonLinearityCorrector(self.parameters['nonlinearity'])

                mflat = pyfits.getdata(self.parameters['master_intensity_ff'])
                ff_corrector = FlatFieldCorrector(mflat)  
                  
                basicflow = SerialFlow([bias_corrector, 
                                        dark_corrector, 
                                        nl_corrector,
                                        ff_corrector
                                        ])

                for frame in obresult.frames:
                    with pyfits.open(frame.label, mode='update') as hdulist:
                            hdulist = basicflow(hdulist)
                  
                if stop_after == state:
                    break
                else:
                    state = PRERED
            elif state == PRERED:                
                # Shape of the window
                windowshape = tuple((i[1] - i[0]) for i in window)
                _logger.debug('Shape of window is %s', windowshape)
                # Shape of the scaled window
                subpixshape = tuple((side * subpix) for side in windowshape)
                    
                # Scaled window region
                scalewindow = tuple(slice(*(subpix * i for i in p)) for p in window)
                # Window region
                window = tuple(slice(*p) for p in window)
                
                scaled_amp = clip_slices(amplifiers, window, scale=subpix)

                # Reference pixel in the center of the frame
                refpix = numpy.divide(numpy.array([baseshape], dtype='int'), 2).astype('float')
        
                # lists of targets and sky frames
                targetframes = []
                skyframes = []
                
                for frame in obresult.frames:
                    
                    # Getting some metadata from FITS header
                    hdr = pyfits.getheader(frame.label)
                    try:
                        frame.exposure = hdr[str(metadata['exposure'])]
                        #frame.baseshape = get_image_shape(hdr)
                        frame.airmass = hdr[str(metadata['airmass'])]
                        frame.mjd = hdr[str(metadata['juliandate'])]
                    except KeyError as e:
                        raise KeyError("%s in frame %s" % (str(e), frame.label))
                    
                    
                    frame.baselabel = os.path.splitext(frame.label)[0]
                    frame.mask = self.parameters['master_bpm']
                    # Insert pixel offsets between frames    
                    frame.objmask_data = None
                    frame.valid_target = False
                    frame.valid_sky = False
                    frame.valid_region = scalewindow
                    if frame.itype == 'TARGET':
                        frame.valid_target = True
                        targetframes.append(frame)
                        if target_is_sky:
                            frame.valid_sky = True
                            skyframes.append(frame)
                    if frame.itype == 'SKY':
                        frame.valid_sky = True
                        skyframes.append(frame)
        
                labels = [frame.label for frame in targetframes]
        
                if offsets is None:
                    _logger.info('Computing offsets from WCS information')
                    
                    list_of_offsets = offsets_from_wcs(labels, refpix)
                else:
                    _logger.info('Using offsets from parameters')
                    list_of_offsets = numpy.asarray(offsets)

                # Insert pixel offsets between frames
                for frame, off in zip(targetframes, list_of_offsets):
                    
                    # Insert pixel offsets between frames
                    frame.pix_offset = off
                    frame.scaled_pix_offset = subpix * off
 
                    _logger.debug('Frame %s, offset=%s, scaled=%s', frame.label, off, subpix * off)

                _logger.info('Computing relative offsets')
                offsets = [(frame.scaled_pix_offset) 
                           for frame in targetframes]
                offsets = numpy.round(offsets).astype('int')        
                finalshape, offsetsp = combine_shape(subpixshape, offsets)
                _logger.info('Shape of resized array is %s', finalshape)
                
                # Resizing target frames        
                self.resize(targetframes, subpixshape, offsetsp, finalshape, 
                            window=window, scale=subpix)
                
                if not target_is_sky:
                    for frame in skyframes:
                        frame.resized_base = frame.label
                        frame.resized_mask = frame.mask    
                
                # superflat
                _logger.info('Step %d, superflat correction (SF)', step)
                # Compute scale factors (median)           
                self.update_scale_factors(obresult.frames)

                # Create superflat
                superflat = self.compute_superflat(obresult.frames, scaled_amp)
            
                # Apply superflat
                self.figure_init(subpixshape)
                self.apply_superflat(obresult.frames, superflat)

                _logger.info('Simple sky correction')
                if target_is_sky:
                    # Each frame is the closest sky frame available
                    
                    for frame in obresult.frames:            
                        self.compute_simple_sky(frame)
                else:
                    self.compute_simple_sky_for_frames(targetframes, skyframes)
                
                # Combining the frames
                _logger.info("Step %d, Combining target frames", step)
                
                sf_data = self.combine_frames(targetframes)
                    
                self.figures_after_combine(sf_data)
                      
                _logger.info('Step %d, finished', step)

                if stop_after == state:
                    break
                else:
                    state = CHECKRED
            elif state == CHECKRED:
                
                seeing_fwhm = None

                #self.check_position(images_info, sf_data, seeing_fwhm)
                recompute = False
                if recompute:
                    _logger.info('Recentering is needed')
                    state = PRERED
                else:
                    _logger.info('Recentering is not needed')
                    _logger.info('Checking photometry')
                    self.check_photometry(targetframes, sf_data, seeing_fwhm)
                    
                    if stop_after == state:
                        break
                    else:
                        state = FULLRED
            elif state == FULLRED:

                # Generating segmentation image
                _logger.info('Step %d, generating segmentation image', step)
                objmask, seeing_fwhm = self.create_mask(sf_data, seeing_fwhm, step=step)
                step +=1
                # Update objects mask
                # For all images    
                # FIXME:
                for frame in obresult.frames:
                    frame.objmask = name_object_mask(frame.baselabel, step)
                    _logger.info('Step %d, create object mask %s', step,  frame.objmask)                 
                    frame.objmask_data = objmask[frame.valid_region]
                    pyfits.writeto(frame.objmask, frame.objmask_data, clobber=True)

                _logger.info('Step %d, superflat correction (SF)', step)
                
                # Compute scale factors (median)           
                self.update_scale_factors(obresult.frames, step)

                # Create superflat
                superflat = self.compute_superflat(obresult.frames, scaled_amp, 
                                                   segmask=objmask, step=step)
                
                # Apply superflat
                self.figure_init(subpixshape)
                
                self.apply_superflat(obresult.frames, superflat, step=step, save=True)

                _logger.info('Step %d, advanced sky correction (SC)', step)
                # FIXME: Only for science          
                for frame in targetframes:
                    self.compute_advanced_sky(frame, objmask, step=step)
            
                # Combining the images
                _logger.info("Step %d, Combining the images", step)
                # FIXME: only for science
                sf_data = self.combine_frames(targetframes, step=step)
                self.figures_after_combine(sf_data)

                if step >= niteration:
                    state = COMPLETE
            else:
                break

        hdu = pyfits.PrimaryHDU(sf_data[0])                
        hdr = hdu.header
        hdr.update('NUMXVER', __version__, 'Numina package version')
        hdr.update('NUMRNAM', self.__class__.__name__, 'Numina recipe name')
        hdr.update('NUMRVER', self.__version__, 'Numina recipe version')
        
        hdr.update('FILENAME', 'result.fits')
        hdr.update('IMGTYP', 'TARGET', 'Image type')
        hdr.update('NUMTYP', 'TARGET', 'Data product type')
        
        varhdu = pyfits.ImageHDU(sf_data[1], name='VARIANCE')
        num = pyfits.ImageHDU(sf_data[2], name='MAP')

        result = pyfits.HDUList([hdu, varhdu, num])        
        
        _logger.info("Final frame created")
        recipe_result['products'] = [DataFrame(result), SourcesCatalog()]
        
        return recipe_result
    
    def compute_simple_sky_for_frames(self, targetframes, skyframes, 
                            maxsep=5, step=0, save=True):
        
        # build kdtree        
        sarray = numpy.array([frame.mjd for frame in skyframes])
        # shape must be (n, 1)
        sarray = numpy.expand_dims(sarray, axis=1)
        
        # query
        tarray = numpy.array([frame.mjd for frame in targetframes])
        # shape must be (n, 1)
        tarray = numpy.expand_dims(tarray, axis=1)
        
        kdtree = KDTree(sarray)
        
        # 1 / minutes in a day 
        MIN_TO_DAY = 0.000694444
        dis, idxs = kdtree.query(tarray, k=1, 
                                 distance_upper_bound=maxsep * MIN_TO_DAY)
        
        nsky = len(sarray)
        
        for tid, idss in enumerate(idxs):
            try:
                tf = targetframes[tid]
                sf = skyframes[idss]
                self.compute_simple_sky_out(tf, sf, step=step, save=save)
            except IndexError:
                _logger.error('No sky image available for frame %s', tf.lastname)
                raise


    def compute_simple_sky_out(self, frame, skyframe, step=0, save=True):
        _logger.info('Correcting sky in frame %s', frame.lastname)
        _logger.info('with sky computed from frame %s', skyframe.lastname)
        
        if hasattr(skyframe, 'median_sky'):
                sky = skyframe.median_sky
        else:
        
            with pyfits.open(skyframe.lastname, mode='readonly') as hdulist:
                data = hdulist['primary'].data
                valid = data[frame.valid_region]


                if skyframe.objmask_data is not None:
                    _logger.debug('object mask defined')
                    msk = frame.objmask_data[valid]
                    sky = numpy.median(valid[msk == 0])
                else:
                    _logger.debug('object mask empty')
                    sky = numpy.median(valid)

            _logger.debug('median sky value is %f', sky)
            skyframe.median_sky = sky
                
        dst = name_skysub_proc(frame.baselabel, step)
        prev = frame.lastname
        
        if save:
            shutil.copyfile(prev, dst)
        else:
            os.rename(prev, dst)
        
        frame.lastname = dst
        
        with pyfits.open(frame.lastname, mode='update') as hdulist:
            data = hdulist['primary'].data
            valid = data[frame.valid_region]
            valid -= sky

    def compute_simple_sky(self, frame, step=0, save=True):
        self.compute_simple_sky_out(frame, skyframe=frame, step=step, save=save)
        
    def compute_advanced_sky(self, frame, objmask, step=0):
        self.compute_simple_sky_out(frame, frame, step=step, save=True)
        return
        
        # FIXME
        # FIXME
        
        
        # Create a copy of the frame
        dst = name_skysub_proc(frame.baselabel, step)
        shutil.copy(frame.lastname, dst)
        frame.lastname = dst
        
        # Fraction of julian day
        max_time_sep = self.parameters['sky_images_sep_time'] / 1440.0
        thistime = frame.mjd
        
        _logger.info('Iter %d, SC: computing advanced sky for %s', self.iter, frame.baselabel)
        desc = []
        data = []
        masks = []
        scales = []

        try:
            idx = 0
            for i in itertools.chain(*frame.sky_related):
                time_sep = abs(thistime - i.mjd)
                if time_sep > max_time_sep:
                    _logger.warn('frame %s is separated from %s more than %dm', 
                                 i.baselabel, frame.baselabel, self.parameters['sky_frames_sep_time'])
                    _logger.warn('frame %s will not be used', i.baselabel)
                    continue
                filename = i.flat_corrected
                hdulist = pyfits.open(filename, mode='readonly')
                data.append(hdulist['primary'].data[i.valid_region])
                scales.append(numpy.median(data[-1]))
                masks.append(objmask[i.valid_region])
                desc.append(hdulist)
                idx += 1

            _logger.debug('computing background with %d frames', len(data))
            sky, _, num = median(data, masks, scales=scales)
            if numpy.any(num == 0):
                # We have pixels without
                # sky background information
                _logger.warn('pixels without sky information in frame %s',
                             i.flat_corrected)
                binmask = num == 0
                # FIXME: during development, this is faster
                sky[binmask] = sky[num != 0].mean()
                # To continue we interpolate over the patches
                #fixpix2(sky, binmask, out=sky, iterations=1)
                name = name_skybackgroundmask(frame.baselabel, self.iter)
                pyfits.writeto(name, binmask.astype('int16'), clobber=True)
                
            hdulist1 = pyfits.open(frame.lastname, mode='update')
            try:
                d = hdulist1['primary'].data[frame.valid_region]
                
                # FIXME
                # sky median is 1.0 ?
                sky = sky / numpy.median(sky) * numpy.median(d)
                # FIXME
                self.figure_image(sky, frame)                 
                d -= sky
                
                name = name_skybackground(frame.baselabel, self.iter)
                pyfits.writeto(name, sky, clobber=True)
                _logger.info('Iter %d, SC: subtracting sky %s to frame %s', 
                             self.iter, name, frame.lastname)                
            
            finally:
                hdulist1.close()
                                                       
        finally:
            for hdl in desc:
                hdl.close()
        
        
        

    def combine_frames(self, frames, out=None, step=0):
        _logger.debug('Step %d, opening sky-subtracted frames', step)

        def fits_open(name):
            '''Open FITS with memmap in readonly mode'''
            return pyfits.open(name, mode='readonly', memmap=True)

        frameslll = [fits_open(frame.lastname) for frame in frames if frame.valid_target]
        _logger.debug('Step %d, opening mask frames', step)
        mskslll = [fits_open(frame.resized_mask) for frame in frames if frame.valid_target]
        _logger.debug('Step %d, combining %d frames', step, len(frameslll))
        try:
            extinc = [pow(10, -0.4 * frame.airmass * self.parameters['extinction']) for frame in frames if frame.valid_target]
            data = [i['primary'].data for i in frameslll]
            masks = [i['primary'].data for i in mskslll]
            
            out = quantileclip(data, masks, scales=extinc, dtype='float32', out=out, fclip=0.1)
            
            # saving the three extensions
            pyfits.writeto('result_i%0d.fits' % step, out[0], clobber=True)
            pyfits.writeto('result_var_i%0d.fits' % step, out[1], clobber=True)
            pyfits.writeto('result_npix_i%0d.fits' % step, out[2], clobber=True)
                
            return out
            
        finally:
            _logger.debug('Step %d, closing sky-subtracted frames', step)
            map(lambda x: x.close(), frameslll)
            _logger.debug('Step %d, closing mask frames', step)
            map(lambda x: x.close(), mskslll)
            
    def apply_superflat(self, frames, flatdata, step=0, save=True):
        _logger.info("Step %d, SF: apply superflat", step)

        # Process all frames with the fitted flat
        # FIXME: not sure
        for frame in frames:
            self.correct_superflat(frame, flatdata, step=step, save=save)
        return frames
            
    def correct_superflat(self, frame, fitted, step=0, save=True):
        
        frame.flat_corrected = name_skyflat_proc(frame.baselabel, step)
        
        if save:
            shutil.copyfile(frame.resized_base, frame.flat_corrected)
        else:
            os.rename(frame.resized_base, frame.flat_corrected)
        
        _logger.info("Step %d, SF: apply superflat to frame %s", step, frame.flat_corrected)
        with pyfits.open(frame.flat_corrected, mode='update') as hdulist:
            data = hdulist['primary'].data
            datar = data[frame.valid_region]
            data[frame.valid_region] = correct_flatfield(datar, fitted)

            frame.lastname = frame.flat_corrected            
            
            # FIXME: plotting
            try:
                self.figure_image(data[frame.valid_region], frame)
            except ValueError:
                _logger.warning('Problem plotting %s', frame.lastname)
                        
    def compute_superflat(self, frames, amplifiers, segmask=None, step=0):
        _logger.info("Step %d, SF: combining the frames without offsets", step)
        try:
            filelist = []
            data = []
            for frame in frames:
                _logger.debug('Step %d, opening resized frame %s', step, frame.resized_base)
                hdulist = pyfits.open(frame.resized_base, memmap=True, mode='readonly')
                filelist.append(hdulist)
                data.append(hdulist['primary'].data[frame.valid_region])

            scales = [frame.median_scale for frame in frames]
            
            # FIXME: plotting
            self.figure_median_background(scales)
            
            masks = None
            if segmask is not None:
                masks = [segmask[frame.valid_region] for frame in frames]
                
            _logger.debug('Step %d, combining %d frames', step, len(data))
            sf_data, _sf_var, sf_num = flatcombine(data, masks, scales=scales, 
                                                    blank=1.0 / scales[0])            
        finally:
            _logger.debug('Step %d, closing resized frames and mask', step)
            for fileh in filelist:               
                fileh.close()            

        # We interpolate holes by channel
        _logger.debug('Step %d, interpolating holes by channel', step)
        for channel in amplifiers:
            mask = (sf_num[channel] == 0)
            if numpy.any(mask):                    
                fixpix2(sf_data[channel], mask, out=sf_data[channel])

        # Normalize, flat has mean = 1
        sf_data /= sf_data.mean()
        
        # Auxiliary data
        sfhdu = pyfits.PrimaryHDU(sf_data)            
        sfhdu.writeto(name_skyflat('comb', step), clobber=True)
        return sf_data
        
    def update_scale_factors(self, frames, step=0):
        _logger.info('Step %d, SF: computing scale factors', step)
        # FIXME: not sure
        for frame in frames:
            region = frame.valid_region
            data = pyfits.getdata(frame.resized_base)[region]
            mask = pyfits.getdata(frame.resized_mask)[region]
            # FIXME: while developing this ::10 is faster, remove later            
            frame.median_scale = numpy.median(data[mask == 0][::10])
            _logger.debug('median value of %s is %f', frame.resized_base, frame.median_scale)
        return frames
        
    def resize(self, frames, shape, offsetsp, finalshape, window=None, scale=1, step=0):
        _logger.info('Resizing frames and masks')
        for frame, rel_offset in zip(frames, offsetsp):
            if frame.valid_target:
                region, _ = subarray_match(finalshape, rel_offset, shape)
                # Valid region
                frame.valid_region = region
                # Relative offset
                frame.rel_offset = rel_offset
                # names of frame and mask
                framen, maskn = name_redimensioned_frames(frame.baselabel, step)
                frame.resized_base = framen
                frame.resized_mask = maskn
                _logger.debug('%s, valid region is %s, relative offset is %s', frame.label, 
                custom_region_to_str(region), rel_offset)
                self.resize_frame_and_mask(frame, finalshape, framen, maskn, window, scale)
                
        return frames

    def resize_frame_and_mask(self, frame, finalshape, framen, maskn, window, scale):
        _logger.info('Resizing frame %s, window=%s, subpix=%i', frame.label, 
                     custom_region_to_str(window), scale)
        resize_fits(frame.label, framen, finalshape, frame.valid_region, 
                    window=window, scale=scale)

        _logger.info('Resizing mask %s, subpix x%i', frame.label, scale)
        # We don't conserve the sum of the values of the frame here, just
        # expand the mask
        resize_fits(frame.mask, maskn, finalshape, frame.valid_region, 
                    fill=1, window=window, scale=scale, conserve=False)
        
    def figure_init(self, shape):
        self._figure.clf()
        ax = self._figure.add_subplot(111)
        cmap = mpl.cm.get_cmap('gray')
        norm = mpl.colors.LogNorm()
        ax.imshow(numpy.ones(shape), cmap=cmap, norm=norm)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        self._figure.canvas.draw()
        
    def figures_after_combine(self, sf_data, step=0):
       
         # FIXME, more plots
        def truncated(array, frac=0.1):
            '''Dirty truncated mean'''
            nf = int(array.size * frac)
            array.sort()
            new = array[nf:-nf]
            lnew = len(new)
            if lnew == 0:
                return 0, 0
            elif lnew == 1:
                return new.mean(), 0.0
            else:
                return new.mean(), new.std()
            
        ndata = sf_data[2].astype('int')                    
        data = sf_data[0]
        
        nimages = ndata.max()

        rnimage = range(1, nimages + 1)
        rmean = rnimage[:]
        rstd = rnimage[:]
            
        for pix in rnimage:
            rmean[pix - 1], rstd[pix - 1] = truncated(data[ndata == pix])                
            
        avg_rms = self.figure_check_combination(rnimage, rmean, rstd, step=step)
                        
        # Fake sky error image
        self.figure_simple_image(ndata, title='Number of frames combined')

        # Create fake error frame
        mask = (ndata <= 0)
        ndata[mask] = 1
        fake = numpy.where(mask, 0.0, numpy.random.normal(avg_rms / numpy.sqrt(ndata)))
        ndata[mask] = 0
        self.figure_simple_image(fake, title='Fake sky error image')
        # store fake image
        pyfits.writeto('fake_sky_rms_i%0d.fits' % step, fake, clobber=True)
        
    def figure_check_combination(self, rnimage, rmean, rstd, step=0):            
        self._figure.clf()
        self._figure.subplots_adjust(hspace=0.001)
        
        ax1 = self._figure.add_subplot(3,1,1)
        pred = [rstd[-1] * math.sqrt(rnimage[-1] / float(npix)) for npix in rnimage]
        ax1.plot(rnimage, rstd, 'g*', rnimage, pred, 'y-')
        ax1.set_title("")
        ax1.set_ylabel('measured sky rms')
        
        ax2 = self._figure.add_subplot(3,1,2, sharex=ax1)
        pred = [val * math.sqrt(npix) for val, npix in zip(rstd, rnimage)]
        avg_rms = sum(pred) / len(pred)
        ax2.plot(rnimage, pred, 'r*', [rnimage[0], rnimage[-1]], [avg_rms,avg_rms])
        ax2.set_ylabel('scaled sky rms')

        ax3 = self._figure.add_subplot(3,1,3, sharex=ax1)
        ax3.plot(rnimage, rmean, 'b*')
        ax3.set_ylabel('mean sky')
        ax3.set_xlabel('number of frames per pixel')

        xticklabels = ax1.get_xticklabels() + ax2.get_xticklabels()
        mpl.artist.setp(xticklabels, visible=False)
        self._figure.canvas.draw()
        self._figure.savefig('figure-check-combination_i%01d.png' % step)
        return avg_rms        
        
    def figure_simple_image(self, data, title=None):
        self._figure.clf()
        ax = self._figure.add_subplot(111)
        cmap = mpl.cm.get_cmap('gray')
        norm = mpl.colors.LogNorm()
        if title is not None:
            ax.set_title(title)
                          
        ax.set_xlabel('X')
        ax.set_ylabel('Y')            
        ax.imshow(data, cmap=cmap, norm=norm)                                
        self._figure.canvas.draw()
  
    def figure_median_background(self, scales, step=0):
        # FIXME: plotting
        self._figure.clf()
        ax = self._figure.add_subplot(1,1,1) 
        ax.plot(scales, 'r*')
        ax.set_title("")
        ax.set_xlabel('Image number')
        ax.set_ylabel('Median')
        self._figure.canvas.draw()
        self._figure.savefig('figure-median-sky-background_i%01d.png' % step)
        
    def figure_image(self, thedata, image):
        # FIXME: remove this dependency
        import numdisplay        
        ax = self._figure.gca()
        image_axes, = ax.get_images()
        image_axes.set_data(thedata)
        z1, z2 = numdisplay.zscale.zscale(thedata)
        image_axes.set_clim(z1, z2)
        clim = image_axes.get_clim()
        ax.set_title('%s, bg=%g fg=%g, linscale' % (image.lastname, clim[0], clim[1]))        
        self._figure.canvas.draw()      

    def check_photometry(self, frames, sf_data, seeing_fwhm, step=0):
        # Check photometry of few objects
        weigthmap = 'weights4rms.fits'
        
        wmap = numpy.zeros_like(sf_data[0])
        
        # Center of the image
        border = 300
        wmap[border:-border, border:-border] = 1                    
        pyfits.writeto(weigthmap, wmap, clobber=True)
        
        basename = 'result_i%0d.fits' % (step)
        sex = SExtractor()
        sex.config['VERBOSE_TYPE'] = 'QUIET'
        sex.config['PIXEL_SCALE'] = 1
        sex.config['BACK_TYPE'] = 'AUTO' 
        if seeing_fwhm is not None:
            sex.config['SEEING_FWHM'] = seeing_fwhm * sex.config['PIXEL_SCALE']
        sex.config['WEIGHT_TYPE'] = 'MAP_WEIGHT'
        sex.config['WEIGHT_IMAGE'] = weigthmap
        
        sex.config['PARAMETERS_LIST'].append('FLUX_BEST')
        sex.config['PARAMETERS_LIST'].append('FLUXERR_BEST')
        sex.config['PARAMETERS_LIST'].append('FWHM_IMAGE')
        sex.config['PARAMETERS_LIST'].append('CLASS_STAR')
        
        sex.config['CATALOG_NAME'] = 'master-catalogue-i%01d.cat' % step
        _logger.info('Runing sextractor in %s', basename)
        sex.run('%s,%s' % (basename, basename))
        
        # Sort catalog by flux
        catalog = sex.catalog()
        catalog = sorted(catalog, key=operator.itemgetter('FLUX_BEST'), reverse=True)
        
        # set of indices of the N first objects
        OBJS_I_KEEP = 3
        indices = set(obj['NUMBER'] for obj in catalog[:OBJS_I_KEEP])
        
        base = numpy.empty((len(frames), OBJS_I_KEEP))
        error = numpy.empty((len(frames), OBJS_I_KEEP))
        
        for idx, frame in enumerate(frames):
            imagename = name_skysub_proc(frame.baselabel, step)

            sex.config['CATALOG_NAME'] = 'catalogue-%s-i%01d.cat' % (frame.baselabel, step)

            # Lauch SExtractor on a FITS file
            # om double image mode
            _logger.info('Runing sextractor in %s', imagename)
            sex.run('%s,%s' % (basename, imagename))
            catalog = sex.catalog()
            
            # Extinction correction
            excor = pow(10, -0.4 * frame.airmass * self.parameters['extinction'])
            excor = 1.0
            base[idx] = [obj['FLUX_BEST'] / excor
                                     for obj in catalog if obj['NUMBER'] in indices]
            error[idx] = [obj['FLUXERR_BEST'] / excor
                                     for obj in catalog if obj['NUMBER'] in indices]
        
        data = base / base[0]
        err = error / base[0] # sigma
        w = 1 / err / err
        # weighted mean of the flux values
        wdata = numpy.average(data, axis=1, weights=w)
        wsigma = 1 / numpy.sqrt(w.sum(axis=1))
        
        # Actions to carry over images when checking the flux
        # of the objects in different images
        def warn_action(img):
            _logger.warn('Image %s has low flux in objects', img.baselabel)
            img.valid_science = True
        
        def reject_action(img):
            img.valid_science = False
            _logger.info('Image %s rejected, has low flux in objects', img.baselabel)            
            pass
        
        def default_action(img):
            _logger.info('Image %s accepted, has correct flux in objects', img.baselabel)      
            img.valid_science = True
        
        # Actions
        dactions = {'warn': warn_action, 'reject': reject_action, 'default': default_action}

        levels = self.parameters['check_photometry_levels']
        actions = self.parameters['check_photometry_actions']
        
        x = range(len(frames))
        vals, (_, sigma) = self.check_photometry_categorize(x, wdata, 
                                                           levels, tags=actions)
        # n sigma level to plt
        n = 3
        self.check_photometry_plot(vals, wsigma, levels, n * sigma)
        
        for x, _, t in vals:
            try:
                action = dactions[t]
            except KeyError:
                _logger.warning('Action named %s not recognized, ignoring', t)
                action = default_action
            for p in x:
                action(frames[p])
                
    def check_photometry_categorize(self, x, y, levels, tags=None):
        '''Put every point in its category.
    
        levels must be sorted.'''   
        x = numpy.asarray(x)
        y = numpy.asarray(y)
        ys = y.copy()
        ys.sort()
        # Mean of the upper half
        m = ys[len(ys) / 2:].mean()
        y /= m
        m = 1.0
        s = ys[len(ys) / 2:].std()
        result = []

        if tags is None:
            tags = range(len(levels) + 1)

        for l, t in zip(levels, tags):
            indc = y < l
            if indc.any():
                x1 = x[indc]
                y1 = y[indc]
                result.append((x1, y1, t))

                x = x[indc == False]
                y = y[indc == False]
        else:
            result.append((x, y, tags[-1]))

        return result, (m, s)
               
    def check_photometry_plot(self, vals, errors, levels, nsigma, step=0):
        x = range(len(errors))
        self._figure.clf()
        ax = self._figure.add_subplot(111)
        ax.set_title('Relative flux of brightest object')
        for v,c in zip(vals, ['b', 'r', 'g', 'y']):
            ax.scatter(v[0], v[1], c=c)
            w = errors[v[0]]
            ax.errorbar(v[0], v[1], yerr=w, fmt=None, c=c)
            

        ax.plot([x[0], x[-1]], [1, 1], 'r--')
        ax.plot([x[0], x[-1]], [1 - nsigma, 1 - nsigma], 'b--')
        for f in levels:
            ax.plot([x[0], x[-1]], [f, f], 'g--')
            
        self._figure.canvas.draw()
        self._figure.savefig('figure-relative-flux_i%01d.png' % step)
        
    def create_mask(self, sf_data, seeing_fwhm, step=0):
        # FIXME more plots
        self.figure_final_before_s(sf_data[0])

        #
        remove_border = True
        
        # sextractor takes care of bad pixels
        sex = SExtractor()
        sex.config['CHECKIMAGE_TYPE'] = "SEGMENTATION"
        sex.config["CHECKIMAGE_NAME"] = name_segmask(step)
        sex.config['VERBOSE_TYPE'] = 'QUIET'
        sex.config['PIXEL_SCALE'] = 1
        sex.config['BACK_TYPE'] = 'AUTO' 

        if seeing_fwhm is not None and seeing_fwhm > 0:
            sex.config['SEEING_FWHM'] = seeing_fwhm * sex.config['PIXEL_SCALE']

        sex.config['PARAMETERS_LIST'].append('FLUX_BEST')
        sex.config['PARAMETERS_LIST'].append('X_IMAGE')
        sex.config['PARAMETERS_LIST'].append('Y_IMAGE')
        sex.config['PARAMETERS_LIST'].append('A_IMAGE')
        sex.config['PARAMETERS_LIST'].append('B_IMAGE')
        sex.config['PARAMETERS_LIST'].append('THETA_IMAGE')
        sex.config['PARAMETERS_LIST'].append('FWHM_IMAGE')
        sex.config['PARAMETERS_LIST'].append('CLASS_STAR')                
        if remove_border:
            weigthmap = 'weights4rms.fits'
            
            # Create weight map, remove n pixs from either side
            # using a Hannig filter
            # npix = 90          
            # w1 = npix
            # w2 = npix
            # wmap = numpy.ones_like(sf_data[0])
            
            # cos_win1 = numpy.hanning(2 * w1)
            # cos_win2 = numpy.hanning(2 * w2)
                                   
            # wmap[:,:w1] *= cos_win1[:w1]                    
            # wmap[:,-w1:] *= cos_win1[-w1:]
            # wmap[:w2,:] *= cos_win2[:w2, numpy.newaxis]
            # wmap[-w2:,:] *= cos_win2[-w2:, numpy.newaxis]                 
            
            # Take the number of combined images from the combined image
            wm = sf_data[2].copy()
            # Dont search objects where nimages < lower
            # FIXME: this is a magic number
            # We ignore objects in regions where we have less
            # than 10% of the images
            lower = sf_data[2].max() / 10
            wm[wm < lower] = 0
            pyfits.writeto(weigthmap, wm, clobber=True)
                                
            sex.config['WEIGHT_TYPE'] = 'MAP_WEIGHT'
            # FIXME: this is a magic number
            # sex.config['WEIGHT_THRESH'] = 50
            sex.config['WEIGHT_IMAGE'] = weigthmap
        
        filename = 'result_i%0d.fits' % (step)
        
        # Lauch SExtractor on a FITS file
        sex.run(filename)
        
        # Plot objects
        # FIXME, plot sextractor objects on top of image
        patches = []
        fwhms = []
        nfirst = 0
        catalog_f = sopen(sex.config['CATALOG_NAME'])
        try:
            star = catalog_f.readline()
            while star:
                flags = star['FLAGS']
                # ignoring those objects with corrupted apertures
                if flags & sexcatalog.CORRUPTED_APER:
                    star = catalog_f.readline()
                    continue
                center = (star['X_IMAGE'], star['Y_IMAGE'])
                wd = 10 * star['A_IMAGE']
                hd = 10 * star['B_IMAGE']
                color = 'red'
                e = Ellipse(center, wd, hd, star['THETA_IMAGE'], color=color)
                patches.append(e)
                fwhms.append(star['FWHM_IMAGE'])
                nfirst += 1
                # FIXME Plot a ellipse
                star = catalog_f.readline()
        finally:
            catalog_f.close()
            
        p = PatchCollection(patches, alpha=0.4)
        ax = self._figure.gca()
        ax.add_collection(p)
        self._figure.canvas.draw()
        self._figure.savefig('figure-segmentation-overlay_%01d.png' % step)

        self.figure_fwhm_histogram(fwhms, step=step)
                    
        # mode with an histogram
        hist, edges = numpy.histogram(fwhms, 50)
        idx = hist.argmax()
        
        seeing_fwhm = 0.5 * (edges[idx] + edges[idx + 1]) 
        if seeing_fwhm <= 0:
            _logger.warning('Seeing FHWM %f pixels is negative, reseting', seeing_fwhm)
            seeing_fwhm = None
        else:
            _logger.info('Seeing FHWM %f pixels (%f arcseconds)', seeing_fwhm, seeing_fwhm * sex.config['PIXEL_SCALE'])
        objmask = pyfits.getdata(name_segmask(step))
        return objmask, seeing_fwhm
    
    def figure_final_before_s(self, data):
        import numdisplay
        self._figure.clf()
        ax = self._figure.add_subplot(111)
        cmap = mpl.cm.get_cmap('gray')
        norm = mpl.colors.LogNorm()
        ax.set_title('Result image')              
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        z1, z2 = numdisplay.zscale.zscale(data)
        ax.imshow(data, cmap=cmap, clim=(z1, z2))                                
        self._figure.canvas.draw()
    
    def figure_fwhm_histogram(self, fwhms, step=0):
        self._figure.clf()
        ax = self._figure.add_subplot(111)
        ax.set_title('FWHM of objects')
        ax.hist(fwhms, 50, normed=1, facecolor='g', alpha=0.75)
        self._figure.canvas.draw()
        self._figure.savefig('figure-fwhm-histogram_i%01d.png' % step)
        
        
    def check_position(self, images_info, sf_data, seeing_fwhm):
        # FIXME: this method has to be updated

        _logger.info('Checking positions')
        # Check position of bright objects
        weigthmap = 'weights4rms.fits'
        
        wmap = numpy.zeros_like(sf_data[0])
        
        # Center of the image
        border = 300
        wmap[border:-border, border:-border] = 1                    
        pyfits.writeto(weigthmap, wmap, clobber=True)
        
        basename = 'result_i%0d.fits' % (step)
        sex = SExtractor()
        sex.config['VERBOSE_TYPE'] = 'QUIET'
        sex.config['PIXEL_SCALE'] = 1
        sex.config['BACK_TYPE'] = 'AUTO'
        if  seeing_fwhm is not None and seeing_fwhm > 0:
            sex.config['SEEING_FWHM'] = seeing_fwhm * sex.config['PIXEL_SCALE']
        sex.config['WEIGHT_TYPE'] = 'MAP_WEIGHT'
        sex.config['WEIGHT_IMAGE'] = weigthmap
        
        sex.config['PARAMETERS_LIST'].append('FLUX_BEST')
        sex.config['PARAMETERS_LIST'].append('FLUXERR_BEST')
        sex.config['PARAMETERS_LIST'].append('FWHM_IMAGE')
        sex.config['PARAMETERS_LIST'].append('CLASS_STAR')
        
        sex.config['CATALOG_NAME'] = 'master-catalogue-i%01d.cat' % step
        
        _logger.info('Runing sextractor in %s', basename)
        sex.run('%s,%s' % (basename, basename))
        
        # Sort catalog by flux
        catalog = sex.catalog()
        catalog = sorted(catalog, key=operator.itemgetter('FLUX_BEST'), reverse=True)
        
        # set of indices of the N first objects
        OBJS_I_KEEP = 10
        
        master = [(obj['X_IMAGE'], obj['Y_IMAGE']) for obj in catalog[:OBJS_I_KEEP]]
        
        for image in images_info:
            imagename = name_skysub_proc(image.baselabel, self.iter)

            sex.config['CATALOG_NAME'] = 'catalogue-self-%s-i%01d.cat' % (image.baselabel, step)

            # Lauch SExtractor on a FITS file
            # on double image mode
            _logger.info('Runing sextractor in %s', imagename)
            sex.run(imagename)
            catalog = sex.catalog()
            
            
            data = [(obj['X_IMAGE'], obj['Y_IMAGE']) for obj in catalog]
            
            tree = KDTree(data)
            
            # Search 2 neighbors
            dists, _ids = tree.query(master, 2, distance_upper_bound=5)
            
            for i in dists[:,0]:
                print i
            
            
            _logger.info('Mean offset correction for image %s is %f', imagename, dists[:,0].mean())
            #raw_input('press any key')

        
        