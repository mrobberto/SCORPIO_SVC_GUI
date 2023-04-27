#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 11:55:59 2023

@author: danakoeppe
"""

import numpy as np
import pandas as pd

from astroquery.hips2fits import hips2fits
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy import wcs

from PIL import Image


CCD_size_x = 2220
CCD_size_y = 2750
SCORP_Scale = 90/CCD_size_y

scale_factor = 2

file_name_fmt = "fits_image/{}/{}_{}_{}.fits"
# fits_image/{IR/VIS}_reference_images/{IR/VIS}_{RA_deg}_{DEC_deg}


def IR_Simbad_Query(RA, DEC, units):
    
    """
    Input:
        - RA, DEC in J2000
        - units for RA and DEC.  Can be (u.deg, u.deg) or (u.hourangle, u.deg)
        
    Returns:
        -HDUL of 2MASS-J with proper SCORPIO size/scaling and WCS
    """
    
    query_coords = SkyCoord(RA, DEC, unit=units)
    
    query_params = {"NAXIS1": int(CCD_size_x/scale_factor),
                    "NAXIS2": int(CCD_size_y/scale_factor),
                    "WCSAXES": 2,
                    "CRPIX1": int(CCD_size_x/(scale_factor*2)),
                    "CRPIX2": int(CCD_size_y/(scale_factor*2)),
                    "CDELT1": SCORP_Scale/3600 * scale_factor  ,
                    "CDELT2": SCORP_Scale/3600 * scale_factor,
                    "CUNIT1": "deg",
                    "CUNIT2": "deg",
                    "CTYPE1": "RA---TAN",
                    "CTYPE2": "DEC--TAN",
                    "CRVAL1": query_coords.ra.value,
                    "CRVAL2": query_coords.dec.value}
    
    IR_query_wcs = wcs.WCS(query_params)
    hips = "CDS/P/2MASS/J" #self.Survey_selected.get()
    
    hdul = hips2fits.query_with_wcs(hips = hips, 
                                    wcs=IR_query_wcs,
                                    get_query_payload=False,
                                    format='fits', min_cut=0.5, max_cut=99.5)
    data = hdul[0].data
    image_data = Image.fromarray(data)

    img_res = image_data.resize(size=(CCD_size_x,CCD_size_y))
    
    hdul[0].data = img_res
    
    cat_name = "IR_"+hips.split("CDS/P/")[1].replace("/","_")#strip("CDS").strip("/P").replace("/","_")
    fname = file_name_fmt.format("IR_reference_images", cat_name, query_coords.ra.value,
                                 query_coords.dec.value)
    
    hdul.writeto(fname)
    
def VIS_Simbad_Query(RA, DEC, units, hips=None):
    
    """
    Input:
        - RA, DEC in J2000
        - units for RA and DEC.  Can be (u.deg, u.deg) or (u.hourangle, u.deg)
        
    Returns:
        -HDUL of 2MASS-J with proper SCORPIO size/scaling and WCS
    """
    
    query_coords = SkyCoord(RA, DEC, unit=units)
    
    query_params = {"NAXIS1": int(CCD_size_x/scale_factor),
                    "NAXIS2": int(CCD_size_y/scale_factor),
                    "WCSAXES": 2,
                    "CRPIX1": int(CCD_size_x/(scale_factor*2)),
                    "CRPIX2": int(CCD_size_y/(scale_factor*2)),
                    "CDELT1": SCORP_Scale/3600 * scale_factor  ,
                    "CDELT2": SCORP_Scale/3600 * scale_factor,
                    "CUNIT1": "deg",
                    "CUNIT2": "deg",
                    "CTYPE1": "RA---TAN",
                    "CTYPE2": "DEC--TAN",
                    "CRVAL1": query_coords.ra.value,
                    "CRVAL2": query_coords.dec.value}
    
    VIS_query_wcs = wcs.WCS(query_params)
    if hips is None:
        hips = "CDS/P/DSS2/red"
    #hips = "CDS/P/PanSTARRS/DR1/i"#, "CDS/P/skymapper-I"
    
    hdul = hips2fits.query_with_wcs(hips = hips, 
                                    wcs=VIS_query_wcs,
                                    get_query_payload=False,
                                    format='fits', min_cut=0.5, max_cut=99.5)
    data = hdul[0].data
    image_data = Image.fromarray(data)

    img_res = image_data.resize(size=(CCD_size_x,CCD_size_y))
    
    hdul[0].data = img_res
    
    cat_name = "VIS_"+hips.split("CDS/P/")[1].replace("/","_")#.strip("CDS").strip("/P").replace("/","_")
    print(cat_name)
    fname = file_name_fmt.format("VIS_reference_images", cat_name, query_coords.ra.value,
                                 query_coords.dec.value)
    print(fname)
    
    hdul.writeto(fname, overwrite=True)    
    
    return fname
    
    