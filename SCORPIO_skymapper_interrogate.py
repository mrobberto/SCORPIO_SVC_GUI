#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 19 22:05:04 2023

@author: robberto
"""
import urllib.request



CCD_size_y = 2750
CCD_size_x = 2220
SCORP_Scale = 90/CCD_size_y # arcsec/pixel

def skymapper_interrogate(POSx=150.041214, POSy=-54.893356, filter='r'):
    POS = str(POSx)+","+str(POSy)   #"189.99763,-11.62305"
    Sizex = 180/3600#SCORP_Scale / 3600 *CCD_size_x
    Sizey = 180/3600#SCORP_Scale / 3600 *CCD_size_y
    SIZE = str(Sizex) + "," + str(Sizey)  #"0.05,0.1"
    NAXIS = str(CCD_size_x) + "," + str(CCD_size_y)
    CDELT = str(SCORP_Scale/3600).replace("e","E")#"[-"+str(SCORP_Scale/3600)+","+str(SCORP_Scale/3600)+"]"
    FILTERS  = filter  #"g"#"g,r,i"
    string0= 'https://api.skymapper.nci.org.au/public/siap/dr2/'
    string = string0 + "query?"
    string += 'POS=' + POS + '&'
    string += 'SIZE=' + SIZE + '&'
    string += 'BAND=' + FILTERS + '&'
    #string += 'NAXIS=' + NAXIS + '&'
    #string += 'CDELT=' + CDELT + '&'
    string += 'FORMAT=image/fits&INTERSECT=covers&MJD_END=56970&RESPONSEFORMAT=CSV'
    print(string)
    with urllib.request.urlopen(string) as response:
       html = response.read()
    print(html)
    
    import pandas as pd
    #v=pd.read_csv(html)
    v=html.decode('UTF-8')
    
    entrypoint  = v.find("\nSkyMapper")
    image_number = v[entrypoint+13:entrypoint+30]
    print("IMAGE NUMBER",image_number)
    
    string = string0 + "get_image?"
    string += 'IMAGE='+image_number + '&'
    string += 'SIZE=' + SIZE + '&'
    string += 'POS=' + POS + '&'
    string += 'BAND=' + FILTERS + '&'
    #string += 'NAXIS=' + NAXIS + '&'
    #string += 'CDELT=' + CDELT + '&'
    string += 'FORMAT=fits'
    
    print(string)
    #https://api.skymapper.nci.org.au/public/siap/dr2/get_image?IMAGE=20140425124821-10&SIZE=0.05,0.1&POS=189.99763,-11.62305&BAND=g&FORMAT=fits
    #https://api.skymapper.nci.org.au/public/siap/dr2/get_image?IMAGE=20140425124821-10&SIZE=0.0833&POS=189.99763,-11.62305&FORMAT=png
    
    """
    #Fetching URLs
    #FROM https://docs.python.org/3/howto/urllib2.html
    """
    import shutil
    import tempfile#import urllib.request
    
    with urllib.request.urlopen(string) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(response, tmp_file)
    
    with open(tmp_file.name) as html:
        pass
    
    return(tmp_file)
#    from astropy.io import fits
#    hdu = fits.open(tmp_file.name)[0]
#    image = hdu.data
#    header = hdu.header
#    return(hdu)