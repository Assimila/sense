"""
implements the I2EM model (see Ulaby (2014), Chapter 10
backscattering model for single scale random surfaces


The code originates from ideas obtained from the supplement
of Ulaby et al (2014)
"""
from . scatter import SurfaceScatter
import numpy as np

from .. util import f2lam
from .. core import Reflectivity
import math

class I2EM(SurfaceScatter):
    def __init__(self, f, eps, sig, l, theta, acf_type='gauss'):
        """

        BACKSCATTERING MODEL

        Parameters
        ----------
        f : float
            frequency [GHz]
        eps : complex
            relative dielectric permitivity
        sig : float
            vertical surface roughness  [m]
        l : float
            autocorrelation length [m]
        theta : float
            incidence angle [rad]
        acf_type : str
            type of autocorrelation function
            'gauss' : gaussian type ACF
        """

        self.freq = f
        lam = f2lam(self.freq)
        k = 2.*np.pi/lam
        self.k = k
        self.sig = sig
        self.l = l
        self.acf_type = acf_type
        super(I2EM, self).__init__(eps, k*sig, theta, kl=k*l)
        
        # assume backscatter geometry
        self.phi = 0.
        self.thetas = self.theta*1.
        self.phis = np.deg2rad(180.)

        # do initializations for backscatter calculations
        self._init_hlp()
        self.init_model()

        # calculate the actual backscattering coefficients
        self._calc_sigma_backscatter()

    def init_model(self):
        """
        initialize model for calculations
        """
        self.niter = self._estimate_itterations()

    def _estimate_itterations(self):
        """
        estimate the number of necessary itterations for 
        the integral calculations
        """

        err = 1.E8
        Ts = 1
        while err > 1.0e-8:
            Ts += 1
            err = ((self._ks2 *(self._cs + self._css)**2 )**Ts) / math.factorial(Ts)
        return Ts


    def _init_hlp(self):
        """ initiate help variables """
        self._ks2 = self.ks**2.
        self._cs = np.cos(self.theta)
        self._s = np.sin(self.theta)
        self._sf = np.sin(self.phi)
        self._cf = np.cos(self.phi)
        self._ss = np.sin(self.thetas)
        self._css = np.cos(self.thetas)
        self._cfs = np.cos(self.phis)
        self._sfs = np.sin(self.phis)
        self._s2 = self._s**2.
        self._kx = self.k*self._s*self._cf
        self._ky = self.k*self._s*self._sf
        self._kz = self.k*self._cs

        self._ksx = self.k * self._ss *self._cfs
        self._ksy = self.k * self._ss *self._sfs
        self._ksz = self.k * self._css

    def _calc_sigma_backscatter(self):
        assert isinstance(self.theta, float), 'Currently array processing not supported yet!'
        # calculate backscattering coefficients
        self.vv, self.hh = self._i2em_bistatic()
        self.hv = self._i2em_cross()

    def _i2em_bistatic(self):
        """
        calculate sigma for the co-pol case
        backscatter geometr
        calculate sigma for the co-pol case
        backscatter geometry

        module 10.1
        """
        Ivv, Ihh = self._calc_Ipp()
        Ivv_abs = np.abs(Ivv)
        Ihh_abs = np.abs(Ihh)
        wn = self.calc_roughness_spectrum(acf_type=self.acf_type) 

        # calculate shadowing effects
        ShdwS = self._calc_shadowing()

        # calculate the integral
        idx = np.arange(self.niter)+1
        fac = map(math.factorial, idx)
        a0 = wn / fac * (self.s**(2.*idx))

        # final backscatter calculation
        hlp = ShdwS*0.5*self.k**2*np.exp(-self.s**2*(self._kz**2.+self._ksz**2.))
        sigvv = np.sum(a0 * Ivv_abs**2.) * hlp
        sighh = np.sum(a0 * Ihh_abs**2.) * hlp
        return  sigvv, sighh

    def _i2em_cross(self):
        assert False
        return None

    def _calc_shadowing(self):
        assert False
        print('TODO: shadowing')
        return 1.  ## todo

    def calc_roughness_spectrum(self, acf_type=None):
        """
        calculate roughness spectrum
        Return wn as an array
        """
        assert 'Validate with code again'
        if acf_type == 'gauss':
            # gaussian autocorrelation function
            S = GaussianSpectrum(niter=self.niter, l=self.l, theta=self.theta, thetas=self.thetas, phi=self.phi,phis=self.phis, freq=self.freq)
        elif acf_type == 'exp15':
            # 1.5 power exponential function
            S = ExponentialSpectrum(niter=self.niter, l=self.l, theta=self.theta, thetas=self.thetas, phi=self.phi,phis=self.phis, freq=self.freq)
        else:
            assert False, 'Invalid surface roughness spectrum: ' + str(acf_type)
        return S.wn()  # returns wn as an array with length NITER

    def _calc_Ipp(self):
        n = np.arange(self.niter)+1.
        qi = self.k*self._cs
        qs = self.k*self._css

        h1= np.exp(-self.sig**2. * self._kz * self._ksz)*(self._kz + self._ksz)**n

        # Calculate the Fppup(dn) i(s) coefficient
        R = Reflectivity(self.eps, self.theta)
        Rvi = R.rho_v
        Rhi = R.rho_h
        
        Fvvupi, Fhhupi = self.Fppupdn( 1,1,Rvi,Rhi)
        Fvvups, Fhhups = self.Fppupdn( 1,2,Rvi,Rhi)
        Fvvdni, Fhhdni = self.Fppupdn(-1,1,Rvi,Rhi)
        Fvvdns, Fhhdns = self.Fppupdn(-1,2,Rvi,Rhi)

        # fpp calculations
        fvv, fhh = self.calc_fpp()

        # Ipp
        Ivv = fvv*h1
        Ivv += 0.25*(Fvvupi *(self._ksz-qi)**(n-1) *np.exp(-self.sig**2. *(qi**2. - qi*(self._ksz-self._kz))))
        Ivv += 0.25*(Fvvdni *(self._ksz+qi)**(n-1) *np.exp(-self.sig**2. *(qi**2. + qi*(self._ksz-self._kz))))
        Ivv += 0.25*(Fvvups *(self._kz +qs)**(n-1) *np.exp(-self.sig**2. *(qs**2. - qs*(self._ksz-self._kz))))
        Ivv += 0.25*(Fvvdns *(self._kz -qs)**(n-1) *np.exp(-self.sig**2. *(qs**2. + qs*(self._ksz-self._kz))))

        Ihh = fhh*h1
        Ihh += 0.25*(Fhhupi *(self._ksz-qi)**(n-1) *np.exp(-self.s**2. *(qi**2. - qi*(self._ksz-self._kz))))
        Ihh += 0.25*(Fhhdni *(self._ksz+qi)**(n-1) *np.exp(-self.s**2. *(qi**2. + qi*(self._ksz-self._kz))))
        Ihh += 0.25*(Fhhups *(self._kz +qs)**(n-1) *np.exp(-self.s**2. *(qs**2. - qs*(self._ksz-self._kz))))
        Ihh += 0.25*(Fhhdns *(self._kz -qs)**(n-1) *np.exp(-self.s**2. *(qs**2. + qs*(self._ksz-self._kz))))

        return Ivv, Ihh

    def calc_fpp(self):

        Rvt, Rht = self.calc_reflection_coefficients()

        fvv =  2. * Rvt *(self._s * self._ss - (1. + self._cs * self._css) * self._cfs)/(self._cs + self._css)
        fhh = -2. * Rht *(self._s * self._ss - (1. + self._cs * self._css) * self._cfs)/(self._cs + self._css)
        return fvv, fhh


    def Fppupdn(self, u_d, i_s, Rvi, Rhi):
        print('TODO: Fpp')
        assert i_s in [1,2]
        assert u_d in [-1,1]

        # set coefficients
        if i_s == 1:
            Gqi = u_d * self._kz
            Gqti = u_d * self.k *np.sqrt(self.eps-self._s**2.);
            qi = u_d * self._kz
            c11 = self.k * self._cfs *(self._ksz - qi)
            c21 = self._cs *(self._cfs *(self.k**2 *self._s*self._cf*(self._ss *self._cfs - self._s * self._cf) + Gqi*(self.k * self._css - qi))+ self.k**2. *self._cf * self._s *self._ss *self._sfs**2.)

            c31 = self.k*self._s*(self._s*self._cf*self._cfs*(self.k*self._css-qi) - Gqi*(self._cfs*(self._ss*self._cfs -self._s*self._cf)+ self._ss *self._sfs**2.))
            c41 = self.k *self._cs*(self._cfs*self._css*(self.k*self._css - qi) + self.k *self._ss*(self._ss*self._cfs-self._s*self._cf))
            c51 = Gqi*(self._cfs *self._css*(qi-self.k*self._css) - self.k *self._ss*(self._ss*self._cfs-self._s*self._cf))
            c12 = self.k * self._cfs *(self._ksz - qi)

            c22 = self._cs *(self._cfs *(self.k**2. *self._s*self._cf*(self._ss *self._cfs - self._s * self._cf) + Gqti*(self.k * self._css - qi)) + self.k**2. *self._cf * self._s *self._ss *self._sfs**2.)
            c32 = self.k*self._s*(self._s*self._cf*self._cfs*(self.k*self._css-qi) - Gqti*(self._cfs*(self._ss*self._cfs -self._s*self._cf)- self._ss *self._sfs**2.))

            c42 = self.k *self._cs*(self._cfs*self._css*(self.k*self._css - qi) + self.k *self._ss*(self._ss*self._cfs-self._s*self._cf))

            c52 = Gqti*(self._cfs *self._css*(qi-self.k*self._css) - self.k *self._ss*(self._ss*self._cfs-self._s*self._cf))  

        else:
            print('Still need to implement')
            assert False

        q = self._kz
        qt = self.k * np.sqrt(self.eps - self._s**2.)

        vv =  (1.+Rvi) *( -(1-Rvi) *c11 /q + (1.+Rvi)       *c12 / qt) 
        vv += (1.-Rvi) *(  (1-Rvi) *c21 /q - (1.+Rvi)       *c22 / qt) 
        vv += (1.+Rvi) *(  (1-Rvi) *c31 /q - (1.+Rvi)       *c32 /self.eps /qt) 
        vv += (1.-Rvi) *(  (1+Rvi) *c41 /q - self.eps*(1. - Rvi)  *c42 / qt) 
        vv += (1.+Rvi) *(  (1+Rvi) *c51 /q - (1.-Rvi)       *c52 / qt)


        hh =  (1.+Rhi) *( (1.-Rhi) * c11 /q - self.eps *(1.+Rhi) *c12 / qt)
        hh -= (1.-Rhi) *( (1.-Rhi) * c21 /q - (1.+Rhi)    *c22 / qt)
        hh -= (1.+Rhi) *( (1.-Rhi) * c31 /q - (1.+Rhi)    *c32 / qt)
        hh -= (1.-Rhi) *( (1.+Rhi) * c41 /q - (1.-Rhi)    *c42 / qt)
        hh -= (1.+Rhi) *( (1.+Rhi) * c51 /q - (1.-Rhi)    *c52 / qt)



        return vv, hh

    def calc_reflection_coefficients(self):
        assert False, 'Still needs implementation'
        return 1., 1.





class Roughness(object):
    """
    calculate roughness spectrum
    """
    def __init__(self, **kwargs):
        self.niter = kwargs.get('niter', None)
        self.l = kwargs.get('l', None)
        self.theta = kwargs.get('theta', None)
        self.thetas = kwargs.get('thetas', None)
        self.phi = kwargs.get('phi', None)
        self.phis = kwargs.get('phis', None)
        self.freq = kwargs.get('freq', None)
        self.n = np.arange(self.niter)+1
        self._check()
        self._init()

    def wn(self):
        assert False, 'Should be implemented in child class!'

    def _init(self):
        ss = np.sin(self.thetas)
        s = np.sin(self.theta)
        sf = np.sin(self.phi)
        sfs = np.sin(self.phis)
        cfs = np.cos(self.phis)
        cf = np.cos(self.phi)
        lam = f2lam(self.freq)
        self.k = 2.*np.pi / lam
        
        # todo whereis this defined ???
        self.wvnb = self.k * np.sqrt( (ss *cfs - s *cf)**2. + (ss * sfs - s * sf)**2. )

    def _check(self):
        assert self.niter is not None
        assert self.l is not None
        assert self.theta is not None
        assert self.thetas is not None
        assert self.phi is not None
        assert self.phis is not None
        assert self.freq is not None


class GaussianSpectrum(Roughness):
    def __init__(self, **kwargs):
        super(GaussianSpectrum, self).__init__(**kwargs)
    
    def wn(self):
        # Fung (1994), Eq. 2B.4; except for wvnb
        n = self.n
        wn = (self.l**2.)/(2.*n) * np.exp(-(self.wvnb*self.l)**2. / (4.*n))
        return wn

class ExponentialSpectrum(Roughness):
    """
    exponential spectrum
    """
    def __init__(self, **kwargs):
        super(ExponentialSpectrum, self).__init__(**kwargs)

    def wn(self):
        # Fung (1994): eq. 2.B.14
        n = self.n
        wn= self.l**2. / n**2. * (1.+(self.wvnb*self.l/n)**2.)**(-1.5)
        return wn






