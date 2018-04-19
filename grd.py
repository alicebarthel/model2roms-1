"""
This class creates an object based on the input file structure. Currently the class takes
two types of structures as input: SODA or ROMS
"""

from datetime import datetime
from netCDF4 import Dataset
import numpy as np

import IOverticalGrid

try:
    import ESMF
except ImportError:
    print("Could not find module ESMF")
    pass

__author__ = 'Trond Kristiansen'
__email__ = 'me@trondkristiansen.com'
__created__ = datetime(2008, 12, 9)
__modified__ = datetime(2017, 1, 3)
__version__ = "1.5"
__status__ = "Development"


class Grd:

    def __init__(self, type, name, useESMF, realm, outgrid):
        """
        The object is initialised and created through the __init__ method
        As an example of how to use, these lines return a grid object called grdTEST:
        => import grd
        => grdTEST = grd.grdClass("grdfilename","ROMS")
        """
        self.type = type
        self.grdName = outgrid
        self.useESMF = useESMF
        self.realm = realm
        print("Creating init for grid object", outgrid)
        print('---> Initialized GRD object for grid type %s' % (self.type))

    def openNetCDF(self, grdfilename):
        self.grdfilename = grdfilename
        print(grdfilename)
        """Open the netCDF file and store the contents in arrays associated with variable names"""
        try:
            self.cdf = Dataset(self.grdfilename, "r")
            print('GRD file : openNetCDF opened file %s' % (self.grdfilename))

        except IOError:
            print('Could not open file %s' % (self.grdfilename))
            print('Exception caught in: openNetCDF(grdfilename)')

    def createObject(self):
        """
        This method creates a new object by reading the grd input file. All
        dimensions (eta, xi, lon, lat etc.) are defined here and used througout these scripts.
        Also, the depth matrix is calculated in this function by calling IOverticalGrid.py (ROMS grid only). For
        input model depths, the depth array is a one dimensional. If input data has 2 or 3 dimensions, this
        has to be accounted for througout the soda2roms package as one dimension is currently only supported.

        Object types currently supported: HYCOM,SODA,SODAMONTHLY,STATION,ROMS,SODA3,NORESM

        Trond Kristiansen, 18.11.2009, edited 03.01.2017
        """
        if self.type == 'FORCINGDATA':
            print('---> Assuming %s grid type for %s' % (self.grdType, self.type))
            print("---> Using dimension names %s and %s and %s" % (self.lonName, self.latName, self.depthName))

            self.lon = self.cdf.variables[str(self.lonName)][:]
            self.lat = self.cdf.variables[str(self.latName)][:]
            self.h = self.cdf.variables[str(self.depthName)][:]
            self.Nlevels = len(self.h)
            self.fill_value = -9.99e+33

            if np.rank(self.lon) == 1:
                self.lon, self.lat = np.meshgrid(self.lon, self.lat)

            IOverticalGrid.get_z_levels(self)

            # Create grid for ESMF interpolation
            if (self.useESMF):
                print("self.grdfilename", self.grdfilename)
                self.esmfgrid = ESMF.Grid(filename=self.grdfilename, filetype=ESMF.FileFormat.GRIDSPEC,
                                          is_sphere=True, coord_names=[str(self.lonName), str(self.latName)],
                                          add_mask=False)
                print("ESMF FORCING GRID", self.grdfilename, self.lonName, self.latName)
                print("=>", self.esmfgrid.coords)
                print("=>", self.esmfgrid.coord_sys)
                print("=>", self.esmfgrid.lower_bounds)
                print("=>", self.esmfgrid.upper_bounds)

        if self.type == 'WOAMONTHLY': self.fill_value = 9.96921e+36
        if self.type == 'SODA': self.fill_value = -9.99e+33
        if self.type == 'SODA3': self.fill_value = -1.e+20
        if self.type == 'SODA3MONTHLY': self.fill_value = -1.e+20
        if self.type == 'SODAMONTHLY': self.fill_value = -9.99e+33
        if self.type == 'GLORYS': self.fill_value = 9.96921e+36
        if self.type == 'NS8KMZ': self.fill_value = 9.96921e+36

        if self.type == 'NORESM':
            # self.h = self.cdf.variables["depth"][:]
            self.h = np.asarray([0, 5, 10, 15, 20, 25, 30, 40, 50, 62.5, 75, 87.5, 100, 112.5, 125,
                                 137.5, 150, 175, 200, 225, 250, 275, 300, 350, 400, 450, 500, 550, 600,
                                 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250,
                                 1300, 1350, 1400, 1450, 1500, 1625, 1750, 1875, 2000, 2250, 2500, 2750,
                                 3000, 3250, 3500, 3750, 4000, 4250, 4500, 4750, 5000, 5250, 5500, 5750,
                                 6000, 6250, 6500, 6750])

        if self.type == 'STATION':
            self.lon = self.cdf.variables[self.lonName][:]
            self.lat = self.cdf.variables[self.latName][:]
            self.h = self.cdf.variables[self.depthName][:]
            self.time = self.cdf.variables[self.timeName][:]

            self.Lp = 1
            self.Mp = 1
            self.fill_value = -9.99e+33

        if self.type in ['ROMS']:

            self.write_clim = True
            self.write_bry = True
            self.write_init = True
            self.write_stations = False

            self.lonName = 'lon_rho'
            self.latName = 'lat_rho'

            """Set initTime to 1 if you dont want the first timestep to be
            the initial field (no ubar and vbar if time=0)"""

            self.initTime = 0
            self.ocean_time = 0
            self.NT = 2
            self.tracer = self.NT

            self.message = None  # Used to store the date for printing to screen (IOwrite.py)
            self.time = 0
            self.reftime = 0
            self.grdType = 'regular'
            self.mask_rho = self.cdf.variables["mask_rho"][:, :]
            self.lon_rho = self.cdf.variables["lon_rho"][:, :]
            self.lat_rho = self.cdf.variables["lat_rho"][:, :]
            self.h = self.cdf.variables["h"][:, :]
            self.hmin = self.h[self.h > 0].min()
            if self.vtransform == 1:
                self.hc = min(self.hmin, self.Tcline)
                self.hc = self.Tcline
                if (self.Tcline > self.hmin):
                    print('Vertical transformation parameters are not defined correctly in either gridid.txt or in the history files: \n Tc\
line = %d and hmin = %d. \n You need to make sure that Tcline <= hmin when using transformation 1.' % (
                    self.Tcline, self.hmin))
            else:
                self.hc = self.Tcline

            zeta = None
            if zeta is None:
                self.zeta = np.zeros(self.h.shape)
            else:
                self.zeta = zeta

            # for findvar in self.cdf.variables:
            #    if findvar=="hraw":
            #        self.hraw     = self.cdf.variables["hraw"][:,:,:]

            self.lon_u = self.cdf.variables["lon_u"][:, :]
            self.lat_u = self.cdf.variables["lat_u"][:, :]
            self.mask_u = self.cdf.variables["mask_u"][:, :]
            for findvar in self.cdf.variables:
                if findvar == "lon_vert":
                    self.lon_vert = self.cdf.variables["lon_vert"][:, :]
                    self.lat_vert = self.cdf.variables["lat_vert"][:, :]

            for findvar in self.cdf.variables:
                if findvar == "x_rho":
                    self.x_rho = self.cdf.variables["x_rho"][:, :]
                    self.y_rho = self.cdf.variables["y_rho"][:, :]

            for findvar in self.cdf.variables:
                if findvar == "x_u":
                    self.x_u = self.cdf.variables["x_u"][:, :]
                    self.y_u = self.cdf.variables["y_u"][:, :]

            for findvar in self.cdf.variables:
                if findvar == "x_v":
                    self.x_v = self.cdf.variables["x_v"][:, :]
                    self.y_v = self.cdf.variables["y_v"][:, :]

            for findvar in self.cdf.variables:
                if findvar == "x_psi":
                    self.x_psi = self.cdf.variables["x_psi"][:, :]
                    self.y_psi = self.cdf.variables["y_psi"][:, :]

            for findvar in self.cdf.variables:
                if findvar == "x_vert":
                    self.x_vert = self.cdf.variables["x_vert"][:, :]
                    self.y_vert = self.cdf.variables["y_vert"][:, :]

            for findvar in self.cdf.variables:
                if findvar == "xl":
                    self.xl = self.cdf.variables["xl"][:]
                    self.el = self.cdf.variables["el"][:]

            for findvar in self.cdf.variables:
                if findvar == "dmde":
                    self.dmde = self.cdf.variables["dmde"][:, :]
                    self.dndx = self.cdf.variables["dndx"][:, :]

            self.lon_v = self.cdf.variables["lon_v"][:, :]
            self.lat_v = self.cdf.variables["lat_v"][:, :]
            self.mask_v = self.cdf.variables["mask_v"][:, :]

            self.spherical = self.cdf.variables["spherical"][:]

            self.lon_psi = self.lon_u[:-1, :]
            self.lat_psi = self.lat_v[:, :-1]
            self.mask_psi = self.mask_v[:, :-1]

            self.f = self.cdf.variables["f"][:, :]
            self.angle = self.cdf.variables["angle"][:, :]

            self.pm = self.cdf.variables["pm"][:, :]
            self.invpm = 1.0 / np.asarray(self.cdf.variables["pm"][:, :])
            self.pn = self.cdf.variables["pn"][:, :]
            self.invpn = 1.0 / np.asarray(self.cdf.variables["pn"][:, :])

            self.Lp = len(self.lat_rho[1, :])
            self.Mp = len(self.lat_rho[:, 1])

            self.fill_value = -9.99e+33

            self.eta_rho = self.Mp
            self.eta_u = self.Mp
            self.eta_v = self.Mp - 1
            self.eta_psi = self.Mp - 1
            self.xi_rho = self.Lp
            self.xi_u = self.Lp - 1
            self.xi_v = self.Lp
            self.xi_psi = self.Lp - 1

            """Boolean to check if we need to initialize the CLIM file before writing"""
            self.ioClimInitialized = False
            self.ioInitInitialized = False

            if np.rank(self.lon_rho) == 1:
                self.lon_rho, self.lat_rho = np.meshgrid(self.lon_rho, self.lat_rho)
                self.lon_u, self.lat_u = np.meshgrid(self.lon_u, self.lat_u)
                self.lon_v, self.lat_v = np.meshgrid(self.lon_v, self.lat_v)

            """Setup the vertical coordinate system"""
            IOverticalGrid.calculateVgrid(self)
            print("PLING")
            if (self.useESMF):
                self.esmfgrid_u = ESMF.Grid(filename=self.grdfilename, filetype=ESMF.FileFormat.GRIDSPEC,
                                            coord_names=['lon_u', 'lat_u'], add_mask=False)
                self.esmfgrid_v = ESMF.Grid(filename=self.grdfilename, filetype=ESMF.FileFormat.GRIDSPEC,
                                            is_sphere=True, coord_names=['lon_v', 'lat_v'], add_mask=False)
                self.esmfgrid = ESMF.Grid(filename=self.grdfilename, filetype=ESMF.FileFormat.GRIDSPEC,
                                          is_sphere=True, coord_names=[self.lonName, self.latName], add_mask=False)

    def getDims(self):
        if self.type in ["ROMS"]:
            self.Lp = len(self.lat_rho[1, :])
            self.Mp = len(self.lat_rho[:, 1])

        if self.type in ['FORCINGDATA']:
            self.Lp = len(self.lat[1, :])
            self.Mp = len(self.lat[:, 1])

        self.M = self.Mp - 1
        self.L = self.Lp - 1
