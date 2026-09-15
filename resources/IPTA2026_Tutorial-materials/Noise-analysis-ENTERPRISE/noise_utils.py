########################
### Functions definition
########################

import scipy.constants as sc
import numpy as np
import math

# In the notebook
day = 24 * 3600
year = 365.25 * day
AU = sc.astronomical_unit
c = sc.speed_of_light
pc = sc.parsec
AU_light_sec = AU / c
AU_pc = AU / pc

### Dispersion measure noise
def add_dm(psr, A, gamma, idx=-2, components=30, seed=None):
    """Inject dispersion measure (DM) noise into a pulsar.

    DM noise is modelled as a Gaussian process with a power-law PSD,
        P(f) = A^2 / (12 pi^2) (f / f_ref)^-gamma,
    projected onto the residuals via the chromatic Fourier design matrix
        F_DM = F * (nu / nu_ref)^idx,
    where nu is the radio frequency of each TOA.

    For ordinary cold-plasma dispersion, idx = -2.

    See Lentati et al. 2014, Appendix C.

    Parameters
    ----------
    psr : libstempo pulsar object
    A : float
        Amplitude of the power-law PSD.
    gamma : float
        Spectral index of the power-law PSD.
    idx : float, optional
        Chromaticity index (default -2 for DM).
    components : int, optional
        Number of Fourier modes to use (default 30).
    seed : int, optional
        PRNG seed for reproducibility.
    """
    if seed is not None:
        np.random.seed(seed)

    t = psr.toas()
    fref = 1400
    v = (psr.freqs / fref)**idx

    minx, maxx = np.min(t), np.max(t)
    x = (t - minx) / (maxx - minx)
    T = (day / year) * (maxx - minx)

    size = 2 * components
    F = np.zeros((psr.nobs, size), "d")
    f = np.zeros(size, "d")

    for i in range(components):
        F[:, 2 * i] = np.cos(2 * math.pi * (i + 1) * x)
        F[:, 2 * i + 1] = np.sin(2 * math.pi * (i + 1) * x)
        f[2 * i] = f[2 * i + 1] = (i + 1) / T

    norm = A**2 * year**2 / (12 * math.pi**2 * T)
    prior = norm * f ** (-gamma)

    y = np.sqrt(prior) * np.random.randn(size)
    psr.stoas[:] += (1.0 / day) * v * np.dot(F, y)


### Generic chromatic noise
def add_ch(psr, A, gamma, idx=-4, components=30, seed=None):
    """Inject generic chromatic noise into a pulsar.

    Identical to `add_dm` but with an arbitrary chromaticity index `idx`.
    Useful for modelling chromatic processes other than dispersion measure,
    such as interstellar scattering (typically idx ~ -4) or band/system-
    dependent noise.

    See Lentati et al. 2014, Appendix C.

    Parameters
    ----------
    psr : libstempo pulsar object
    A : float
        Amplitude of the power-law PSD.
    gamma : float
        Spectral index of the power-law PSD.
    idx : float, optional
        Chromaticity index (default -4).
    components : int, optional
        Number of Fourier modes to use (default 30).
    seed : int, optional
        PRNG seed for reproducibility.
    """
    if seed is not None:
        np.random.seed(seed)

    t = psr.toas()
    fref = 1400
    v = (psr.freqs / fref)**idx

    minx, maxx = np.min(t), np.max(t)
    x = (t - minx) / (maxx - minx)
    T = (day / year) * (maxx - minx)

    size = 2 * components
    F = np.zeros((psr.nobs, size), "d")
    f = np.zeros(size, "d")

    for i in range(components):
        F[:, 2 * i] = np.cos(2 * math.pi * (i + 1) * x)
        F[:, 2 * i + 1] = np.sin(2 * math.pi * (i + 1) * x)
        f[2 * i] = f[2 * i + 1] = (i + 1) / T

    norm = A**2 * year**2 / (12 * math.pi**2 * T)
    prior = norm * f ** (-gamma)

    y = np.sqrt(prior) * np.random.randn(size)
    psr.stoas[:] += (1.0 / day) * v * np.dot(F, y)


### Solar wind
def add_sw(psr, A, gamma, components=30, seed=None):
    """Inject solar wind variations into a pulsar.

    Solar wind introduces a chromatic delay that depends on the angle
    between the line of sight to the pulsar and the Sun. This function
    computes the geometry from the pulsar's Earth-SSB and Sun-SSB
    positions, then modulates the delay with a power-law Gaussian process
    of amplitude `A` and spectral index `gamma`.

    Assumes an electron density at 1 AU of n_earth = 1.0 cm^-3.

    See You et al. 2007 for the solar wind model.

    Parameters
    ----------
    psr : libstempo pulsar object
    A : float
        Amplitude of the power-law PSD.
    gamma : float
        Spectral index of the power-law PSD.
    components : int, optional
        Number of Fourier modes to use (default 30).
    seed : int, optional
        PRNG seed for reproducibility.
    """
    if seed is not None:
        np.random.seed(seed)

    t = psr.toas()

    theta, R_earth = theta_impact(psr.earth_ssb, psr.sun_ssb, psr.psrPos)
    dt_sol_wind = (4.148808e3 / (psr.freqs**2)) * dm_solar(1.0, theta, R_earth)

    minx, maxx = np.min(t), np.max(t)
    x = (t - minx) / (maxx - minx)
    T = (day / year) * (maxx - minx)

    size = 2 * components
    F = np.zeros((psr.nobs, size), "d")
    f = np.zeros(size, "d")

    for i in range(components):
        F[:, 2 * i] = np.cos(2 * math.pi * (i + 1) * x)
        F[:, 2 * i + 1] = np.sin(2 * math.pi * (i + 1) * x)
        f[2 * i] = f[2 * i + 1] = (i + 1) / T

    norm = A**2 * year**2 / (12 * math.pi**2 * T)
    prior = norm * f ** (-gamma)

    y = np.sqrt(prior) * np.random.randn(size)
    psr.stoas[:] += (1.0 / day) * dt_sol_wind * np.dot(F, y)


### Solar wind geometry helpers
def theta_impact(earthssb, sunssb, pos_t):
    """Compute the solar impact angle and Earth-Sun distance.

    Parameters
    ----------
    earthssb : array
        Earth position relative to the Solar System barycentre.
    sunssb : array
        Sun position relative to the Solar System barycentre.
    pos_t : array
        Pulsar position (unit vector).

    Returns
    -------
    theta : array
        Angle between the Sun and the line of sight to the pulsar (rad).
    R_earth : array
        Earth-Sun distance (light seconds).
    """
    earth = earthssb[:, :3]
    sun = sunssb[:, :3]
    pulsar = pos_t[:, :3]
    earthsun = earth - sun
    R_earth = np.sqrt(np.einsum('ij,ij->i', earthsun, earthsun))
    Re_cos_theta_impact = np.einsum('ij,ij->i', earthsun, pulsar)
    theta = np.arccos(-Re_cos_theta_impact / R_earth)
    return theta, R_earth


def _dm_solar_close(n_earth, r_earth):
    """Solar wind DM contribution at very small solar impact angle."""
    return n_earth * AU_light_sec * AU_pc / r_earth


def _dm_solar(n_earth, theta, r_earth):
    """Solar wind DM contribution for general solar impact angle."""
    return ((np.pi - theta) *
            (n_earth * AU_light_sec * AU_pc
             / (r_earth * np.sin(theta))))


def dm_solar(n_earth, theta, r_earth):
    """Dispersion measure due to a 1/r^2 solar wind density model.

    Parameters
    ----------
    n_earth : float
        Solar wind proton/electron density at Earth (cm^-3).
    theta : array
        Angle between the Sun and the line of sight to the pulsar (rad).
    r_earth : array
        Earth-Sun distance (light seconds).

    Returns
    -------
    dm : array
        Solar wind DM contribution.

    See You et al. 2007 for more details.
    """
    return np.where(np.pi - theta >= 1e-5,
                    _dm_solar(n_earth, theta, r_earth),
                    _dm_solar_close(n_earth, r_earth))