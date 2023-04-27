#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 29 10:32:07 2023

@author: danakoeppe
"""
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import csv

### regions
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion
from regions import PointPixelRegion, RegionVisual
from regions import Regions

### astrometry
import twirl
from astropy.wcs.utils import fit_wcs_from_points
import astropy.wcs as wcs
from astroquery.gaia import Gaia
from astropy import units as u
from astropy.io import fits, ascii
from astropy.stats import sigma_clipped_stats, SigmaClip
from SCORPIO_skymapper_interrogate import skymapper_interrogate

### ginga/tk
from ginga.util import iqcalc
from ginga.AstroImage import AstroImage
from ginga.util import ap_region
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga import colors
from ginga.util.loader import load_data
from ginga.misc import log
from ginga.canvas import CompoundMixin as CM
from ginga.canvas.CanvasObject import get_canvas_types
from ginga.tkw.ImageViewTk import CanvasView
from tkinter import ttk
from tkinter import filedialog
import tkinter as tk


from ginga.AstroImage import AstroImage
from PIL import Image
from astropy.io import fits
from astroquery.hips2fits import hips2fits

img = AstroImage()
iq = iqcalc.IQCalc()

cwd = os.getcwd()
print(cwd)

SCORP_SlitWidths = [4.32, 2.16, 1.44, 1.08, 0.72, 0.54, 0.36] #arcseconds
SCORP_SlitColors = ['#377eb8', '#ff7f00', '#4daf4a',
                  '#f781bf', '#a65628', '#984ea3',
                  '#999999']


CCD_size_y = 2750
CCD_size_x = 2220

SCORP_Scale = 90/CCD_size_y #arcsec/pixel
# as per SCORPIO slit viewing camera final design report

# define the local directory, absolute so it is not messed up when this is called

path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)
sys.path.append(parent_dir)

class MainPage(tk.Tk):
    """ to be written """
    
    def __init__(self):
        super().__init__()

        # Setting up Initial Things
        self.title("SCORPIO Dither Slit")
        self.geometry("1700x1100")
        self.resizable(True, True)
        """ to be written """
        
        logger = log.get_logger("example2", options=None)
        self.logger = logger

        #label = tk.Label(self, text="SCORPIO", font=('Times', '20'))
        #label.pack(pady=10,padx=0)

        # ADD CODE HERE TO DESIGN THIS PAGE

        # keep track of the entry number for header keys that need to be added
        # will be used to write "OtherParameters.txt"
        self.extra_header_params = 0
        self.header_entry_string = '' #keep string of entries to write to a file after acquisition.
        self.wcs = None
        self.canvas_types = get_canvas_types()
        self.drawcolors = colors.get_colors()
        
        
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         
#  #    FITS manager
#         
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.frame_FITSmanager = tk.Frame(self,background="pink")#, width=400, height=800)
        self.frame_FITSmanager.place(x=4, y=720, anchor="nw", width=400, height=210)

        labelframe_FITSmanager =  tk.LabelFrame(self.frame_FITSmanager, text="FITS manager", font=("Arial", 24))
        labelframe_FITSmanager.pack(fill="both", expand="yes")

 
        button_FITS_Load =  tk.Button(labelframe_FITSmanager, text="Open file", bd=3, 
                                           command=self.open_file)
        button_FITS_Load.place(x=0,y=0)
        
        
        
        
# =============================================================================
#      QUERY SIMBAD
# 
# =============================================================================
        labelframe_Query_Simbad =  tk.LabelFrame(labelframe_FITSmanager, text="Query Simbad", 
                                                     width=180,height=110,
                                                     font=("Arial", 24))
        labelframe_Query_Simbad.place(x=0, y=40)

        button_Query_Simbad =  tk.Button(labelframe_Query_Simbad, text="Query Simbad", bd=3, 
                                         command=self.Query_Simbad)
        #button_Query_Simbad =  tk.Button(labelframe_Query_Simbad, text="Query Simbad", bd=3, 
        #                                 command=self.run_queries_in_parallel)
        button_Query_Simbad.place(x=5, y=35)




        self.label_SelectSurvey = tk.Label(labelframe_Query_Simbad, text="Survey")
        self.label_SelectSurvey.place(x=5, y=5)
#        # Dropdown menu options
        Survey_options = [
             "DSS2/red",
             "AKARI/FIS/N160",
             "PanSTARRS/DR1/z",
             "2MASS/J",
             "GALEX",
             "AllWISE/W3",
             "skymapper-I"]
#        # datatype of menu text
        self.Survey_selected = tk.StringVar()
#        # initial menu text
        self.Survey_selected.set(Survey_options[0])
#        # Create Dropdown menu
        self.menu_Survey = tk.OptionMenu(labelframe_Query_Simbad, self.Survey_selected ,  *Survey_options)
        self.menu_Survey.place(x=65, y=5)
        self.menu_Survey.config(foreground="black")
        
        readout_frame = tk.Frame(self, background='pink')
        #readout_frame.pack(side=tk.TOP, fill=tk.X, expand=1)
        readout_frame.place(x=600, y=680)
        self.readout_Simbad = tk.Label(readout_frame, text='') 
        self.readout_Simbad.pack()
        #self.readout_Simbad.place(x=0, y=0)
    
        """ RA Entry box""" 
        self.string_RA = tk.StringVar()
#        self.string_RA.set("189.99763")  #Sombrero
        self.string_RA.set("150.17110")  #NGC 3105
        label_RA = tk.Label(labelframe_FITSmanager, text='RA:',  bd =3)
        self.entry_RA = tk.Entry(labelframe_FITSmanager, width=11,  bd =3, textvariable = self.string_RA)
        label_RA.place(x=190,y=5)
        self.entry_RA.place(x=230,y=5)
        
        """ DEC Entry box""" 
        self.string_DEC = tk.StringVar()
#        self.string_DEC.set("-11.62305")#Sombrero
        self.string_DEC.set("-54.79004") #NGC 3105
        label_DEC = tk.Label(labelframe_FITSmanager, text='Dec:',  bd =3)
        self.entry_DEC = tk.Entry(labelframe_FITSmanager, width=11,  bd =3, textvariable = self.string_DEC)
        label_DEC.place(x=290,y=30)
        self.entry_DEC.place(x=230,y=30)
        
        """ Filter Entry box""" 
        self.string_Filter = tk.StringVar()
        self.string_Filter.set("i")
        label_Filter = tk.Label(labelframe_FITSmanager, text='Filter:',  bd =3)
        entry_Filter = tk.Entry(labelframe_FITSmanager, width=3,  bd =3,textvariable = self.string_Filter)
        label_Filter.place(x=190,y=55)
        entry_Filter.place(x=230,y=55)

        """ Nr. of Stars Entry box""" 
        label_nrofstars =  tk.Label(labelframe_FITSmanager, text="Nr. of stars")
        label_nrofstars.place(x=280,y=55)
        self.nrofstars=tk.IntVar()
        entry_nrofstars = tk.Entry(labelframe_FITSmanager, width=3,  bd =3, textvariable=self.nrofstars)
        entry_nrofstars.place(x=350, y=55)
        self.nrofstars.set('25')

        """ SkyMapper Query """ 
        button_skymapper_query =  tk.Button(labelframe_FITSmanager, text="SkyMapper Query", bd=3, 
                                           command=self.SkyMapper_query)
        #button_skymapper_query.place(x=190,y=80)
               
        
        """ Twirl Astrometry """
        button_twirl_Astrometry =  tk.Button(labelframe_FITSmanager, text="twirl_Astrometry", bd=3, 
                                            command=self.twirl_Astrometry)
        button_twirl_Astrometry.place(x=190,y=105)
        
        # threshold for source detection in twirl
        label_detect_thresh =  tk.Label(labelframe_FITSmanager, text="Detection Threshhold")
        label_detect_thresh.place(x=190,y=140)
        self.detect_thresh=tk.StringVar()
        entry_detect_thresh = tk.Entry(labelframe_FITSmanager, width=3,  bd =3, textvariable=self.detect_thresh)
        entry_detect_thresh.place(x=330, y=138)
        self.detect_thresh.set('2')
        
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# DITHER TELESCOPE
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        
        
        self.dither_frame = tk.LabelFrame(self,text="Calculate Offset",
                                          font=("Ariel, 25"),width=380, height=210)
        self.dither_frame.place(x=430, y=720)
        
        label_slit_select =  tk.Label(self.dither_frame, text="Slit Select")
        label_slit_select.place(x=220,y=-5)
        self.selected_slit = tk.StringVar()
        self.slit_widths_dropdown = ttk.Combobox(self.dither_frame, width = 10, 
                                            textvariable=self.selected_slit,
                                            values=SCORP_SlitWidths, foreground="black")
        
        self.slit_widths_dropdown.place(x=200, y=15)
        self.slit_widths_dropdown.bind("<<ComboboxSelected>>", self.draw_slit_reg)
        self.slit_widths_dropdown.config(foreground="black")
        
        self.curr_des_var = tk.StringVar()
        self.curr_des_var.set("current")
        btn_curr = tk.Radiobutton(self.dither_frame, text="select current slit location",
                                  value="current", variable=self.curr_des_var,
                                  state=tk.DISABLED)
        btn_curr.place(x=4, y=2)
        self.btn_curr = btn_curr
        
        btn_des = tk.Radiobutton(self.dither_frame, text="select desired slit location",
                                 value="desired", variable=self.curr_des_var,
                                 state=tk.DISABLED)
        btn_des.place(x=4, y=25)
        self.btn_des = btn_des
        
        self.use_centroid_var = tk.IntVar()
        self.use_centroid_for_desired = tk.Checkbutton(self.dither_frame, variable=self.use_centroid_var, onvalue=1, offvalue=0, 
                                                       text="Place Desired from Centroid")
        self.use_centroid_for_desired.place(x=4, y=50)
        
        x_entry_label = tk.Label(self.dither_frame, text="x")
        x_entry_label.place(x=158, y=70)
        y_entry_label = tk.Label(self.dither_frame, text="y")
        y_entry_label.place(x=208,y=70)
        ### current values ######
        
        current_pix_vals_label = tk.Label(self.dither_frame, 
                                          text="Current Pixel Values:")
        current_pix_vals_label.place(x=4, y=90)
        self.x_current = tk.IntVar()
        current_pix_val_x = tk.Entry(self.dither_frame, width=4, 
                                     textvariable=self.x_current)
        current_pix_val_x.place(x=140, y=90)
        self.current_pix_val_x = current_pix_val_x
        
        self.y_current = tk.IntVar()
        current_pix_val_y = tk.Entry(self.dither_frame, width=4,
                                     textvariable=self.y_current)
        
        current_pix_val_y.place(x=190, y=90)
        self.current_pix_val_y = current_pix_val_y
        
        ### desired values ######
        desired_pix_vals_label = tk.Label(self.dither_frame, 
                                          text="Desired Pixel Values:")
        desired_pix_vals_label.place(x=4, y=115)
        self.x_desired = tk.IntVar()
        desired_pix_val_x = tk.Entry(self.dither_frame, width=4,
                                     textvariable=self.x_desired)
        desired_pix_val_x.place(x=140, y=115)
        self.desired_pix_val_x = desired_pix_val_x
        
        self.y_desired = tk.IntVar()
        desired_pix_val_y = tk.Entry(self.dither_frame, width=4,
                                     textvariable=self.y_desired)
        desired_pix_val_y.place(x=190, y=115)
        self.desired_pix_val_y = desired_pix_val_y
        
        calc_offset_btn = tk.Button(self.dither_frame, command=self.calc_req_offset,
                                    text="Calculate Required Offset")
        calc_offset_btn.place(x=90,y=150)
        
        
        #### display offset result ###
        #self.dither_result_frame = tk.LabelFrame(self,text="Result", 
        #                                         font=("Ariel", 25), width=150, height=190)
        #self.dither_result_frame.place(x=250, y=300)
        

        
        self.result_east_label_frame = tk.LabelFrame(self.dither_frame,background="pink",
                                                     borderwidth=0,highlightthickness=0, width=60, 
                                                     height=18, foreground="black")
        self.result_east_label_frame.place(x=250, y=95)
        self.result_east_label_frame.config(text="0",labelanchor="wn")
        east_label = tk.Label(self.dither_frame, text="'' East")
        east_label.place(x=300,y=95)
        
        self.result_north_label_frame = tk.LabelFrame(self.dither_frame,background="pink",
                                                borderwidth=0,highlightthickness=0, width=60, 
                                                height=18, foreground="black")
        self.result_north_label_frame.place(x=250, y=120)
        self.result_north_label_frame.config(text="0",labelanchor="wn")

        north_label = tk.Label(self.dither_frame, text="'' North")
        north_label.place(x=300,y=120)

      
        
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# GINGA DISPLAY for SVC
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        vbox = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
#        vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        vbox.pack(side=tk.TOP)
        vbox.place(x=570, y=20, anchor="nw")#, width=500, height=800)
        # self.vb = vbox
        
        label = tk.Label(text="Slit Viewing Camera", font=("Arial", 20))
        label.place(x=750, y=0)
        #self.bind("<Button 1>", self.getorigin)


#        canvas = tk.Canvas(vbox, bg="grey", height=514, width=20)
        self.canvas_yoffset = 420
        self.canvas_xoffset = 10
        canvas = tk.Canvas(vbox, bg="grey", height=650, width=550)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)



        fi = CanvasView(logger) #=> ImageViewTk -- a backend for Ginga using a Tk canvas widget
        fi.set_widget(canvas)  #=> Call this method with the Tkinter canvas that will be used for the display.
        # fi.set_redraw_lag(0.0)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        fi.enable_autozoom('on')
        # fi.enable_draw(False)
        # tk seems to not take focus with a click
        fi.set_enter_focus(True)
        fi.set_callback('cursor-changed', self.cursor_cb)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        fi.show_pan_mark(True)
        # add little mode indicator that shows keyboard modal states
        fi.show_mode_indicator(True, corner = 'ur')
        self.fitsimage = fi
        


        bd = fi.get_bindings()
        bd.enable_all(True)

        # canvas that we will draw on
#        DrawingCanvas = fi.getDrawClasses('drawingcanvas')
        canvas = self.canvas_types.DrawingCanvas()
        canvas.enable_draw(True)
        canvas.enable_edit(True)
        canvas.set_drawtype('box', color='red')
        canvas.register_for_cursor_drawing(fi)
        canvas.add_callback('draw-event', self.draw_cb)
        canvas.set_draw_mode('draw')
        


        # without this call, you can only draw with the right mouse button
        # using the default user interface bindings
        # canvas.register_for_cursor_drawing(fi)

        canvas.set_surface(fi)
        canvas.ui_set_active(True)
        self.canvas = canvas



#        # add canvas to viewers default canvas
        fi.get_canvas().add(canvas)

        self.drawtypes = canvas.get_drawtypes()
        self.drawtypes.sort()

#        fi.configure(516, 528) #height, width
        #fi.set_window_size(514,522)
        #fi.set_window_size(514,20)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# GINGA DISPLAY for IR (2MASS image)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        
        
        vbox = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
        vbox.place(x=4,y=20)
        self.IR_canvas_yoffset = 420
        self.IR_canvas_xoffset = 10
        IR_canvas = tk.Canvas(vbox, bg="grey", height=650, width=550)
        IR_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        IR_label = tk.Label(text="IR HiPS", font=("Arial", 20))
        IR_label.place(x=250,y=0)
        
        IR_fi = CanvasView(logger)
        IR_fi.set_widget(IR_canvas)
        IR_fi.enable_autocuts("on")
        IR_fi.set_autocut_params("zscale")
        IR_fi.enable_autozoom("on")
        IR_fi.set_enter_focus(True)
        
        IR_fi.set_callback('cursor-changed', self.IR_cursor_cb)
        IR_fi.set_bg(0.2, 0.2, 0.2)
        IR_fi.ui_set_active(True)
        IR_fi.show_pan_mark(True)
        
        IR_fi.show_mode_indicator(True, corner = 'ur')
        self.IR_fitsimage = IR_fi
        
        bd = IR_fi.get_bindings()
        bd.enable_all(True)

        # canvas that we will draw on
#        DrawingCanvas = fi.getDrawClasses('drawingcanvas')
        IR_canvas = self.canvas_types.DrawingCanvas()
        IR_canvas.enable_draw(True)
        IR_canvas.enable_edit(True)
        IR_canvas.set_drawtype('box', color='red')
        IR_canvas.register_for_cursor_drawing(IR_fi)
        IR_canvas.add_callback('draw-event', self.IR_draw_cb)
        IR_canvas.set_draw_mode('draw')
        
        IR_canvas.set_surface(IR_fi)
        IR_canvas.ui_set_active(True)
        self.IR_canvas = IR_canvas
        
        IR_fi.get_canvas().add(IR_canvas)
        IR_readout_frame = tk.Frame(self, background='pink')
        #readout_frame.pack(side=tk.TOP, fill=tk.X, expand=1)
        IR_readout_frame.place(x=50, y=680)
        self.IR_readout_Simbad = tk.Label(IR_readout_frame, text='') 
        self.IR_readout_Simbad.pack()
        
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# GINGA DISPLAY for VIS (DSS/SkyMapper... image)
# search for image catalog that contains FOV
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        
        
        vbox = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
        vbox.place(x=1135,y=20)
        self.VIS_canvas_yoffset = 420
        self.VIS_canvas_xoffset = 10
        VIS_canvas = tk.Canvas(vbox, bg="grey", height=650, width=550)
        VIS_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        VIS_label = tk.Label(text="VIS HiPS", font=("Arial", 20))
        VIS_label.place(x=1360,y=0)
        
        VIS_fi = CanvasView(logger)
        VIS_fi.set_widget(VIS_canvas)
        VIS_fi.enable_autocuts("on")
        VIS_fi.set_autocut_params("zscale")
        VIS_fi.enable_autozoom("on")
        VIS_fi.set_enter_focus(True)
        
        VIS_fi.set_callback('cursor-changed', self.cursor_cb)
        VIS_fi.set_bg(0.2, 0.2, 0.2)
        VIS_fi.ui_set_active(True)
        VIS_fi.show_pan_mark(True)
        
        VIS_fi.show_mode_indicator(True, corner = 'ur')
        self.VIS_fitsimage = VIS_fi
        
        bd = VIS_fi.get_bindings()
        bd.enable_all(True)

        # canvas that we will draw on
#        DrawingCanvas = fi.getDrawClasses('drawingcanvas')
        VIS_canvas = self.canvas_types.DrawingCanvas()
        VIS_canvas.enable_draw(True)
        VIS_canvas.enable_edit(True)
        VIS_canvas.set_drawtype('box', color='red')
        VIS_canvas.register_for_cursor_drawing(VIS_fi)
        VIS_canvas.add_callback('draw-event', self.VIS_draw_cb) #TODO make VIS_draw_cb
        VIS_canvas.set_draw_mode('draw')
        
        VIS_canvas.set_surface(VIS_fi)
        VIS_canvas.ui_set_active(True)
        self.VIS_canvas = VIS_canvas
        
        VIS_fi.get_canvas().add(VIS_canvas)
        
        """
        HORIZONTAL BOX AT THE BOTTOM WITH ORIGINAL GINGA TOOLS
        """

        hbox = tk.Frame(self)
        hbox.pack(side=tk.BOTTOM, fill=tk.X, expand=0)

        
        self.drawtypes = canvas.get_drawtypes()
        # wdrawtype = ttk.Combobox(self, values=self.drawtypes,
        # command=self.set_drawparams)
        # index = self.drawtypes.index('ruler')
        # wdrawtype.current(index)
        wdrawtype = tk.Entry(hbox, width=12)
        wdrawtype.insert(0, 'box')
        wdrawtype.bind("<Return>", self.set_drawparams)
        self.wdrawtype = wdrawtype

        wdrawcolor = ttk.Combobox(hbox, values=self.drawcolors)#,
        #                           command=self.set_drawparams)
        index = self.drawcolors.index('red')
        wdrawcolor.current(index)
        wdrawcolor.bind("<<ComboboxSelected>>", self.set_drawparams)
        # wdrawcolor = tk.Entry(hbox, width=12)
        # wdrawcolor.insert(0, 'blue')
        # wdrawcolor.bind("<Return>", self.set_drawparams)
        self.wdrawcolor = wdrawcolor

        self.vfill = tk.IntVar()
        wfill = tk.Checkbutton(hbox, text="Fill", variable=self.vfill)
        self.wfill = wfill

        walpha = tk.Entry(hbox, width=12)
        walpha.insert(0, '1.0')
        walpha.bind("<Return>", self.set_drawparams)
        self.walpha = walpha

        
        wclear = tk.Button(self, text="Clear Canvases",
                                command=self.clear_canvas)
        wclear.place(x=810,y=730)
        #wclear.pack()
        
        
        wopen = tk.Button(hbox, text="Open File",
                               command=self.open_file)
                # pressing quit button freezes application and forces kernel restart.
        wquit = tk.Button(hbox, text="Quit",
                               command=lambda: self.quit(self))

        
        for w in (wquit, wclear, walpha, tk.Label(hbox, text='Alpha:'),
#                  wfill, wdrawcolor, wslit, wdrawtype, wopen):
                  wfill, wdrawcolor, wdrawtype):
            pass
            #w.pack(side=tk.RIGHT)
        
    
    def read_dir_user(self):
         dict_from_csv = {}

         with open(local_dir+"/dirlist_user.csv", mode='r') as inp:
             reader = csv.reader(inp)
             dict_from_csv = {rows[0]:rows[1] for rows in reader}

         return dict_from_csv  
     

         
    def load_last_file(self):
        """ to be written """
        FITSfiledir = local_dir+"/fits_image/"
        self.fullpath_FITSfilename = FITSfiledir + (os.listdir(FITSfiledir))[0] 
            # './fits_image/newimage_ff.fits'
        self.AstroImage = load_data(self.fullpath_FITSfilename, logger=self.logger)
        # AstroImage object of ginga.AstroImage module
        
        # passes the image to the viewer through the set_image() method
        self.fitsimage.set_image(self.AstroImage)
#        self.root.title(self.fullpath_FITSfilename)
    
    def test_multi_1(self):
        for i in range(500):
            pass
        print("func1 done")
        
    def test_multi_2(self):
        for i in range(500):
            pass
        print("func2 done")
        
    def run_queries_in_parallel(self):
        from multiprocessing import Process
        
        fns = [self.test_multi_1, self.test_multi_2]#[self.Query_Simbad, self.IR_Simbad_Query]
        proc = []
        for fn in fns:
          p = Process(target=fn)
          p.start()
          proc.append(p)
        for p in proc:
          p.join()
        
    def Query_Simbad(self):
        """ to be written """
        
        
        from astroquery.simbad import Simbad                                                            
        from astropy.coordinates import SkyCoord
        from astropy import units as u
        print(self.Survey_selected.get())
        coord = SkyCoord(self.string_RA.get()+'  '+self.string_DEC.get(),unit=(u.deg, u.deg), frame='fk5') 
#        coord = SkyCoord('16 14 20.30000000 -19 06 48.1000000', unit=(u.hourangle, u.deg), frame='fk5') 
        query_results = Simbad.query_region(coord)                                                      
        print(query_results)
        self.check_for_IR_VIS_reference_images(coord.ra.value, coord.dec.value)
    # =============================================================================
    # Download an image centered on the coordinates passed by the main window
    # 
    # =============================================================================
        from urllib.parse import urlencode
        from astropy.io import fits
        from astroquery.hips2fits import hips2fits
        #object_main_id = query_results[0]['MAIN_ID']#.decode('ascii')
        object_coords = SkyCoord(ra=query_results['RA'], dec=query_results['DEC'], 
                                 unit=(u.hourangle, u.deg), frame='icrs')
        c = SkyCoord(self.string_RA.get(),self.string_DEC.get(), unit=(u.deg, u.deg))
        self.query_c = c

        scale_factor = 2
        #scale = 180/CCD_size_y
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
                        "CRVAL1": c.ra.value,
                        "CRVAL2": c.dec.value}
        
        query_wcs = wcs.WCS(query_params)
        hips = "CDS/P/"+self.Survey_selected.get()
        print(hips)
        hdul = hips2fits.query_with_wcs(hips = hips,
                                        wcs=query_wcs,
                                        get_query_payload=False,
                                        format='fits', min_cut=0.5, max_cut=99.5)
        hdul.info()
                                                                                            
        #Filename: /path/to/.astropy/cache/download/py3/ef660443b43c65e573ab96af03510e19
        #No.    Name      Ver    Type      Cards   Dimensions   Format
        #  0  PRIMARY       1 PrimaryHDU      22   (500, 500)   int16   
        print(hdul[0].header)                                                                                  
          
        self.image = hdul                                    
        #hdul.writeto('./IR_newtable.fits',overwrite=True)
        
        self.wcs = wcs.WCS(hdul[0].header)
        
        from ginga.AstroImage import AstroImage
        from PIL import Image
        img = AstroImage()
        from astropy.io import fits
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt= self.string_Filter.get()
        data = hdul[0].data#[:,::-1]
        # PIL Image indexing is like FITS (x, y)
        image_data = Image.fromarray(data)
        img_res = image_data
        img_res = image_data.resize(size=(CCD_size_x,CCD_size_y))
        self.hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
        ra = Posx
        dec = Posy
        self.hdu_res.header['RA'] = ra
        self.hdu_res.header['DEC'] = dec

#            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
 #           hdu.writeto(rebinned_filename,overwrite=True)

        img.load_hdu(self.hdu_res)       
        print('\n',self.hdu_res.header)     
        self.fitsimage.set_image(img)
        self.AstroImage = img
#        self.fullpath_FITSfilename = filepath.name
        hdul.close()
        work_dir = os.getcwd()
        self.fits_image_ff = "{}/fits_image/newimage_ff.fits".format(work_dir)
        fits.writeto(self.fits_image_ff,self.hdu_res.data,header=self.hdu_res.header,overwrite=True) 
 
        # self.root.title(filepath)
        self.block_light()
        #self.IR_Simbad_Query()
        #self.VIS_Simbad_query()
        
    
    def check_for_IR_VIS_reference_images(self, RA, DEC):
        
        VIS_fpath = "fits_image/VIS_reference_images/"
        IR_fpath = "fits_image/IR_reference_images/"
        radec_str = "{}_{}".format(RA,DEC)
        
        for f in os.listdir(VIS_fpath):
            if radec_str in f:
                fname = VIS_fpath+f
                break
            
        try:
            VIS_hdul = fits.open(fname)
            VIS_data = Image.fromarray(VIS_hdul[0].data)
            img.load_hdu(VIS_hdul[0])
            self.VIS_fitsimage.set_image(img)
        except UnboundLocalError:
            self.VIS_Simbad_query()
        
        ##########
        
        for f in os.listdir(IR_fpath):
            if radec_str in f:
                fname = IR_fpath+f
                break
            
        try:
            IR_hdul = fits.open(fname)
            IR_data = Image.fromarray(IR_hdul[0].data)
            img.load_hdu(IR_hdul[0])
            self.IR_fitsimage.set_image(img)
        except UnboundLocalError:
            self.IR_Simbad_Query()

    def IR_Simbad_Query(self):
        

        
        scale_factor = 2
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
                        "CRVAL1": self.query_c.ra.value,
                        "CRVAL2": self.query_c.dec.value}
                                                   
        IR_query_wcs = wcs.WCS(query_params)
        hips = "2MASS/J" #self.Survey_selected.get()
        
        hdul = hips2fits.query_with_wcs(hips = hips, 
                                        wcs=IR_query_wcs,
                                        get_query_payload=False,
                                        format='fits', min_cut=0.5, max_cut=99.5)
        img = AstroImage()
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt= self.string_Filter.get()
        data = hdul[0].data#[:,::-1]
        # PIL Image indexing is like FITS (x, y)
        image_data = Image.fromarray(data)
        img_res = image_data
        img_res = image_data.resize(size=(CCD_size_x,CCD_size_y))
        self.IR_hdu_res = fits.PrimaryHDU(data=img_res, header=hdul[0].header)
            # ra, dec in degrees
        ra = Posx
        dec = Posy
        self.IR_hdu_res.header['RA'] = ra
        self.IR_hdu_res.header['DEC'] = dec
        self.IR_wcs = hdul[0].header

#            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
 #           hdu.writeto(rebinned_filename,overwrite=True)

        img.load_hdu(self.hdu_res)       
        print('\n',self.hdu_res.header)     
        self.IR_fitsimage.set_image(img)
        self.IR_AstroImage = img

    def VIS_Simbad_query(self):
        
        scale_factor = 2
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
                        "CRVAL1": self.query_c.ra.value,
                        "CRVAL2": self.query_c.dec.value}
                                                   
        VIS_query_wcs = wcs.WCS(query_params)
        hips_list = "CDS/P/DSS2/red" #, "CDS/P/skymapper-I"] #self.Survey_selected.get()
        
        hdul = hips2fits.query_with_wcs(hips = hips_list, 
                                        wcs=VIS_query_wcs,
                                        get_query_payload=False,
                                        format='fits', min_cut=0.5, max_cut=99.5)
        img = AstroImage()
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt= self.string_Filter.get()
        data = hdul[0].data#[:,::-1]
        # PIL Image indexing is like FITS (x, y)
        image_data = Image.fromarray(data)
        img_res = image_data
        img_res = image_data.resize(size=(CCD_size_x,CCD_size_y))
        self.IR_hdu_res = fits.PrimaryHDU(data=img_res, header=hdul[0].header)
            # ra, dec in degrees
        ra = Posx
        dec = Posy
        self.VIS_hdu_res.header['RA'] = ra
        self.VIS_hdu_res.header['DEC'] = dec
        self.VIS_wcs = hdul[0].header

#            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
 #           hdu.writeto(rebinned_filename,overwrite=True)

        img.load_hdu(self.hdu_res)       
        print('\n',self.hdu_res.header)     
        self.VIS_fitsimage.set_image(img)
        self.VIS_AstroImage = img
        
        
        
    """ 
    Inject image from SkyMapper to create a WCS solution using twirl
    """
    def SkyMapper_query(self):
        """ to be written """
        from ginga.AstroImage import AstroImage
        from PIL import Image
        img = AstroImage()
        from astropy.io import fits
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt= self.string_Filter.get()
        filepath = skymapper_interrogate(Posx, Posy, filt)       
        with fits.open(filepath.name) as hdu_in:
#            img.load_hdu(hdu_in[0])
            data = hdu_in[0].data
            image_data = Image.fromarray(data)
            img_res = image_data.resize(size=(CCD_size_x,CCD_size_y))
            self.hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
            ra = Posx
            dec = Posy
            self.hdu_res.header['RA'] = ra
            self.hdu_res.header['DEC'] = dec

#            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
 #           hdu.writeto(rebinned_filename,overwrite=True)

            img.load_hdu(self.hdu_res)       

            self.fitsimage.set_image(img)
            self.AstroImage = img
            self.fullpath_FITSfilename = filepath.name
        hdu_in.close()
        work_dir = os.getcwd()
        self.fits_image_ff = "{}/fits_image/newimage_ff.fits".format(work_dir)
        fits.writeto(self.fits_image_ff,self.hdu_res.data,header=self.hdu_res.header,overwrite=True) 
 
        self.block_light()
        

    def twirl_Astrometry(self):
        
        from astropy.io import fits
        import numpy as np
        from astropy import units as u
        from astropy.coordinates import SkyCoord
        from matplotlib import pyplot as plt
        import twirl
        
        try:
            image = self.fits_image_ff
            self.Display(self.fits_image_ff)
        except AttributeError:
            image = self.fullpath_FITSfilename
            self.Display(self.fullpath_FITSfilename)
        # self.load_file()   #for ging
        
        hdu=fits.open(image)[0]  #for this function to work
        
        header = hdu.header 
        data = hdu.data
        
        ra, dec = header["RA"], header["DEC"]
        center = SkyCoord(ra, dec, unit=["deg", "deg"])
        center = [center.ra.value, center.dec.value]
        
        # image shape and pixel size in "
        shape = data.shape
        
        pixel = SCORP_Scale * u.arcsec
        fov = np.max(shape)*pixel.to(u.deg).value
        
        # Let's find some stars and display the image
        
        self.canvas.delete_all_objects(redraw=True)
        
        # need to change threshold for star detection 
        #otherwise the twirl solver doesn't have enought to get a solution.
        thresh = float(self.detect_thresh.get())
        stars = twirl.find_peaks(data, threshold=thresh)[0:self.nrofstars.get()]
        
#        plt.figure(figsize=(8,8))
        med = np.median(data)
#        plt.imshow(data, cmap="Greys_r", vmax=np.std(data)*5 + med, vmin=med)
#        plt.plot(*stars.T, "o", fillstyle="none", c="w", ms=12)

        from regions import PixCoord, CirclePixelRegion
#        xs=stars[0,0]
#        ys=stars[0,1]
#        center_pix = PixCoord(x=xs, y=ys)
        radius_pix = 42
#        region = CirclePixelRegion(center_pix, radius_pix)
        
        regions = [CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix)
                for x, y in stars]  #[(1, 2), (3, 4)]]
        regs = Regions(regions)
        for reg in regs:
            obj = r2g(reg)
        # add_region(self.canvas, obj, tag="twirlstars", draw=True)
            self.canvas.add(obj)
        #done with finding the brightest stars in the field.
        # we can now look at the GAIA stars to compute the WCS
        gaias = twirl.gaia_radecs(center, fov, limit=self.nrofstars.get())
        
        self.wcs = twirl._compute_wcs(stars, gaias)
        
        
        # Lets check the WCS solution 
        
#        plt.figure(figsize=(8,8))
        radius_pix = 25
        gaia_pixel = np.array(SkyCoord(gaias, unit="deg").to_pixel(self.wcs)).T
        regions_gaia = [CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix)
                for x, y in gaia_pixel]  #[(1, 2), (3, 4)]]
        regs_gaia = Regions(regions_gaia)
        for reg in regs_gaia:
            obj = r2g(reg)
            obj.color="red"
        # add_region(self.canvas, obj, tag="twirlstars", redraw=True)
            self.canvas.add(obj)
        
        print(self.wcs)
        hdu_wcs = self.wcs.to_fits()
        
        #if self.loaded_regfile is not None:
        #    hdu_wcs[0].header.set("dmdmap", os.path.split(self.loaded_regfile)[1])
            
        hdu_wcs[0].data = data # add data to fits file
        self.wcs_filename = "./fits_image/" + "WCS_"+ra+"_"+dec+".fits"
        hdu_wcs[0].writeto(self.wcs_filename,overwrite=True)
        
        self.Display(self.wcs_filename)
        
        self.btn_curr.config(state = tk.ACTIVE)
        self.btn_des.config(state = tk.ACTIVE)
        self.block_light()
        #
        # > to read:
        # hdu = fits_open(self.wcs_filename)
        # hdr = hdu[0].header
        # import astropy.wcs as apwcs
        # wcs = apwcs.WCS(hdu[('sci',1)].header)
        # hdu.close()
        
 
        
        

        
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#     def start_the_loop(self):
#         while self.stop_it == 0:
#             threading.Timer(1.0, self.load_manager_last_file).start() 
# 
#     def load_manager_last_file(self):
#         FITSfiledir = './fits_image/'
#         self.fullpath_FITSfilename = FITSfiledir + (os.listdir(FITSfiledir))[0]
#         print(self.fullpath_FITSfilename)        
# 
#     def stop_the_loop(self):
#         self.stop_it == 1
# 
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         image = load_data(self.fullpath_FITSfilename, logger=self.logger)
#         self.fitsimage.set_image(image)
#         self.root.title(self.fullpath_FITSfilename)
# 
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    
        
    def block_light(self):
        
        x_center_pix = CCD_size_x/2
        scale_fov_x = SCORP_Scale #180/2220
        light_left_right_pix = 8/scale_fov_x # half of 16'' width of allowed light
        
       
        
        blocked_light_left = x_center_pix-light_left_right_pix # 0 to center-8
        blocked_light_right = x_center_pix+light_left_right_pix # center+8 to ccd_size_x
        
        
        
        
        blocked_light_left_reg = RectanglePixelRegion(
            center=PixCoord(blocked_light_left/2,CCD_size_y/2), 
                                         width=blocked_light_left, height=CCD_size_y)
        
        blocked_light_left_obj = r2g(blocked_light_left_reg)
        
        blocked_light_left_obj.fill = True
        blocked_light_left_obj.fillalpha = 1
        blocked_light_left_obj.color = "black"
        blocked_light_left_obj.fillcolor = "black"
        self.canvas.add(blocked_light_left_obj)
        
        blocked_light_right_width = (CCD_size_x-blocked_light_right)
        
        #right_center_x = x_center_pix + (blocked_light_right_width/2) + light_left_right_pix
        right_center_x = blocked_light_right + blocked_light_right_width/2
        blocked_light_right_reg = RectanglePixelRegion(
            center=PixCoord(right_center_x,CCD_size_y/2), 
            width=blocked_light_right_width, height=CCD_size_y)
        
        blocked_light_right_obj = r2g(blocked_light_right_reg)
        blocked_light_right_obj.fill = True
        blocked_light_right_obj.fillalpha = 1
        blocked_light_right_obj.color = "black"
        blocked_light_right_obj.fillcolor = "black"
        self.canvas.add(blocked_light_right_obj)
        

            
        
    def draw_slit_reg(self, event):
        
        SlitWidth = self.slit_widths_dropdown.get()
        slit_num = self.slit_widths_dropdown.current()
        slit_color = SCORP_SlitColors[slit_num]
        width = float(SlitWidth)/SCORP_Scale
        height = 90/SCORP_Scale # arcsec full height of image
        
        try:
            CM.CompoundMixin.delete_object(self.canvas, self.current_slit_draw_obj)
            
        except:
            print("no slit to remove")
        
        fake_slit_reg = RectanglePixelRegion(center=PixCoord(CCD_size_x/2,CCD_size_y/2), 
                                         width=width, height=height)
        obj = r2g(fake_slit_reg)
        obj.fill = True
        obj.fillcolor = slit_color
        obj.color = slit_color
        self.canvas.add(obj)
        
        self.current_slit_draw_obj = obj
        

        
    def calc_req_offset(self):
        from astropy.coordinates import SkyOffsetFrame, ICRS
        
        current_x = float(self.current_pix_val_x.get())
        current_y = float(self.current_pix_val_y.get())
        
        desired_x = float(self.desired_pix_val_x.get())
        desired_y = float(self.desired_pix_val_y.get())
        
        current_scoords = self.wcs.all_pix2world(np.array([[current_x, current_y]]), 1)
        current = ICRS(current_scoords[0][0]*u.deg, 
                       current_scoords[0][1]*u.deg)
        
        
        desired_scoords = self.wcs.all_pix2world(np.array([[desired_x, desired_y]]), 1)
        desired = ICRS(desired_scoords[0][0]*u.deg, 
                       desired_scoords[0][1]*u.deg)
        desired_delta = desired.transform_to(SkyOffsetFrame(origin=current))
        desired_delta_lon = np.round(desired_delta.lon.to(u.arcsecond).value,2)
        desired_delta_lat = np.round(desired_delta.lat.to(u.arcsecond).value,2)
        print(desired_delta_lon)
        print(desired_delta_lat)
        self.result_east_label_frame.config(text=desired_delta_lon)
        self.result_north_label_frame.config(text=desired_delta_lat)
        
        
        
    def open_file(self):
        """ to be written """
        filename = filedialog.askopenfilename(filetypes=[("allfiles", "*"),
                                              ("fitsfiles", "*.fits")])
        self.fullpath_FITSfilename = filename
        # self.load_file()
        self.AstroImage = load_data(filename, logger=self.logger)
        self.fitsimage.set_image(self.AstroImage)
        hdu = fits.open(filename)
        hdr = hdu[0].header
        
        ra = hdr["CRVAL1"]
        dec = hdr["CRVAL2"]
        self.string_DEC.set(dec)
        self.string_RA.set(ra)
        
        if self.AstroImage.wcs.wcs.has_celestial:
            self.wcs = self.AstroImage.wcs.wcs

        
            self.btn_curr.config(state = tk.ACTIVE)
            self.btn_des.config(state = tk.ACTIVE)
            print("should be activated")
            
        self.block_light()
        
    def IR_draw_cb(self, canvas, tag):
        obj = canvas.get_object_by_tag(tag)
        print("drawing on IR canvas.")
        obj.add_callback('edited', self.edit_cb)
        # obj.add_callback('pick-key',self.delete_obj_cb, 'key')
        x_c, y_c = obj.get_center_pt()
        
        #p = PointPixelRegion(center=PixCoord(x_c, y_c), 
        #                     visual=RegionVisual(point='+', 
        #                                         fontsize=10, color='red'))
        p = CirclePixelRegion(center=PixCoord(x_c, y_c), radius=50)
        canvas.add(r2g(p))
        #self.IR_canvas.add(r2g(p))
        self.VIS_canvas.add(r2g(p))
        self.canvas.add(r2g(p))
        canvas.delete_object(obj)
            
    def VIS_draw_cb(self, canvas, tag):
        obj = canvas.get_object_by_tag(tag)
        
        obj.add_callback('edited', self.edit_cb)
        # obj.add_callback('pick-key',self.delete_obj_cb, 'key')
        x_c, y_c = obj.get_center_pt()
        #p = PointPixelRegion(center=PixCoord(x_c, y_c), 
        #                     visual=RegionVisual(point='+', 
        #                                         fontsize=10, color='red'))
        p = CirclePixelRegion(center=PixCoord(x_c, y_c), radius=50)
        
        canvas.add(r2g(p))
        self.canvas.add(r2g(p))
        self.IR_canvas.add(r2g(p))
            
    def draw_cb(self, canvas, tag):
        """ to be written """
        obj = canvas.get_object_by_tag(tag)
        #obj.add_callback('pick-down', self.pick_cb, 'down')
        #obj.add_callback('pick-up', self.pick_cb, 'up')
        #obj.add_callback('pick-move', self.pick_cb, 'move')
        #obj.add_callback('pick-hover', self.pick_cb, 'hover')
        # obj.add_callback('pick-enter', self.pick_cb, 'enter')
        # obj.add_callback('pick-leave', self.pick_cb, 'leave')
        #obj.add_callback('pick-key', self.pick_cb, 'key')
        #obj.pickable = True
        obj.add_callback('edited', self.edit_cb)
        # obj.add_callback('pick-key',self.delete_obj_cb, 'key')
        x_c, y_c = obj.get_center_pt()
        
        # check whether radio button is set to current or desired
        type_draw = self.curr_des_var.get()
        if type_draw=="current":
            
            self.x_current.set(x_c)
            self.y_current.set(y_c)
            
        elif type_draw=="desired":
            
            if self.use_centroid_var.get()==1:
                img_data = self.AstroImage.get_data()
                
                r = RectanglePixelRegion(center=PixCoord(x=x_c, y=y_c),
                                                width=300, height=300,
                                                angle = 0*u.deg)
                r = g2r(obj)
                
                robj = r2g(r)
                print(x_c, y_c)
                self.canvas.add(robj)
                data_box = self.AstroImage.cutout_shape(robj)
                # we can now remove the "pointer" object
                #CM.CompoundMixin.delete_object(self.canvas,robj)
                peaks = iq.find_bright_peaks(data_box)
                print(peaks[:20])  # subarea coordinates
                x1=robj.x-robj.xradius
                y1=robj.y-robj.yradius
                px,py=round(peaks[0][0]+x1),round(peaks[0][1]+y1)
                print('peak found at: ', px,py)   #image coordinates
                print('with counts: ',img_data[py,px]) #actual counts
                # evaluate peaks to get FWHM, center of each peak, etc.
                objs = iq.evaluate_peaks(peaks, data_box) 
                print('full evaluation: ',objs)
                print('fitted centroid: ', objs[0].objx,objs[0].objy) 
                print('FWHM: ', objs[0].fwhm) 
                print('peak value: ',objs[0].brightness)
                print('sky level: ',objs[0].skylevel)
                print('median of area: ',objs[0].background)
                x1, y1, x2, y2 = robj.get_llur()
                print("the four vertex of the rectangle are, in pixel coord (x1, y1, x2, y2): {} {} {} {}".format(x1, y1, x2, y2))
                print("cx + x1, cy + y1", objs[0].objx+x1, objs[0].objy+y1)
                centroid_x, centroid_y = objs[0].objx+x1, objs[0].objy+y1
                print("the RADEC of the fitted centroid are, in decimal degrees:")
                print(self.AstroImage.pixtoradec(objs[0].objx,objs[0].objy))
                print(self.AstroImage.pixtoradec(centroid_x, centroid_y))
                #CM.CompoundMixin.delete_object(self.canvas,robj)
                robj.x = centroid_x
                robj.y = centroid_y
                robj.yradius = 100
                robj.xradius = 10
                
                p = PointPixelRegion(center=PixCoord(centroid_x, centroid_y), 
                                     visual=RegionVisual(point='+', 
                                                         fontsize=10, color='red'))
                
                
                
                self.x_desired.set(centroid_x)
                self.y_desired.set(centroid_y)
            else:
                
                r = RectanglePixelRegion(center=PixCoord(x=x_c, y=y_c),
                                                width=10, height=100,
                                                angle = 0*u.deg)
                
                robj = r2g(r)
                robj.yradius = 100
                robj.xradius = 10
                p = PointPixelRegion(center=PixCoord(x_c, y_c), 
                                     visual=RegionVisual(point='+', 
                                                         fontsize=10, color='red'))
                
                
                
                self.x_desired.set(x_c)
                self.y_desired.set(y_c)
                
            canvas.add(r2g(p))
            canvas.add(robj)
            self.IR_canvas.add(r2g(p))
            self.VIS_canvas.add(r2g(p))
            
        CM.CompoundMixin.delete_object(self.canvas,obj)
        
        

        
        
    def edit_cb(self, obj):
        """ to be written """
        self.logger.info("object %s has been edited" % (obj.kind))

        return True
    
    def set_mode_cb(self):
        """ to be written """
        mode = self.setChecked.get()
#        self.logger.info("canvas mode changed (%s) %s" % (mode))
        self.logger.info("canvas mode changed (%s)" % (mode))
        try:
            for obj in self.canvas.objects:
                obj.color='red'
        except:
            pass
        
        self.canvas.set_draw_mode(mode)
        self.IR_canvas.set_draw_mode(mode)
        self.VIS_canvas.set_draw_mode(mode)
        
    def set_drawparams(self, evt):
         """ to be written """
         kind = self.wdrawtype.get()
         color = self.wdrawcolor.get()
         alpha = float(self.walpha.get())
         fill = self.vfill.get() != 0

         params = {'color': color,
                   'alpha': alpha,
                   # 'cap': 'ball',
                   }
         if kind in ('circle', 'rectangle', 'polygon', 'triangle',
                     'righttriangle', 'ellipse', 'square', 'box'):
             params['fill'] = fill
             params['fillalpha'] = alpha

         self.canvas.set_drawtype(kind, **params)
         self.IR_canvas.set_drawtype(kind, **params)
         self.VIS_canvas.set_drawtype(kind, **params)
    
    def IR_cursor_cb(self, viewer, button, data_x, data_y):
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = viewer.get_data(int(data_x + viewer.data_off),
                                    int(data_y + viewer.data_off))
            
            value = np.round(value, 2)

        except Exception:
            value = None

        fits_x, fits_y = data_x + 1, data_y + 1

        # Calculate WCS RA
        try:
            # NOTE: image function operates on DATA space coords
            image = viewer.get_image()
            if image is None:
                # No image loaded
                return
            ra_txt, dec_txt = image.pixtoradec(fits_x, fits_y,
                                               format='str', coords='fits')
        except Exception as e:
            self.logger.warning("Bad coordinate conversion: %s" % (
                str(e)))
            ra_txt = 'BAD WCS'
            dec_txt = 'BAD WCS'

        text = "RA: %s  DEC: %s  X: %.2f  Y: %.2f  Value: %s" % (
            ra_txt, dec_txt, fits_x, fits_y, value)
#        text = "RA: %s  DEC: %s  X: %.2f  Y: %.2f  Value: %s Button %s" % (
#            ra_txt, dec_txt, fits_x, fits_y, value, button) 
        self.IR_readout_Simbad.config(text=text)
    
    def cursor_cb(self, viewer, button, data_x, data_y):
        """This gets called when the data position relative to the cursor
        changes.
        """
        # Get the value under the data coordinates
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = viewer.get_data(int(data_x + viewer.data_off),
                                    int(data_y + viewer.data_off))
            
            value = np.round(value, 2)

        except Exception:
            value = None

        fits_x, fits_y = data_x + 1, data_y + 1

        # Calculate WCS RA
        try:
            # NOTE: image function operates on DATA space coords
            image = viewer.get_image()
            if image is None:
                # No image loaded
                return
            ra_txt, dec_txt = image.pixtoradec(fits_x, fits_y,
                                               format='str', coords='fits')
        except Exception as e:
            self.logger.warning("Bad coordinate conversion: %s" % (
                str(e)))
            ra_txt = 'BAD WCS'
            dec_txt = 'BAD WCS'

        text = "RA: %s  DEC: %s  X: %.2f  Y: %.2f  Value: %s" % (
            ra_txt, dec_txt, fits_x, fits_y, value)
#        text = "RA: %s  DEC: %s  X: %.2f  Y: %.2f  Value: %s Button %s" % (
#            ra_txt, dec_txt, fits_x, fits_y, value, button) 
        self.readout_Simbad.config(text=text)

    def Display(self,imagefile): 
        """ to be written """
#        image = load_data(fits_image_converted, logger=self.logger)

        # AstroImage object of ginga.AstroImage module
        self.AstroImage = load_data(imagefile, logger=self.logger)
      
        # passes the image to the viewer through the set_image() method
        self.fitsimage.set_image(self.AstroImage)

    
    def clear_canvas(self):
        """ to be written """
        obj_tags = list(self.canvas.tags.keys())
        print(obj_tags)
        
                    
        self.canvas.delete_all_objects(redraw=True)
        self.IR_canvas.delete_all_objects(redraw=True)
        self.VIS_canvas.delete_all_objects(redraw=True)
        self.block_light()
        
        
    def quit(self,root):
        root.destroy()
        return True
        

if __name__ == "__main__":
    app = MainPage()
    app.mainloop()