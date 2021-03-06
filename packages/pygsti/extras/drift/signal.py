from __future__ import division, print_function, absolute_import, unicode_literals
#*****************************************************************
#    pyGSTi 0.9:  Copyright 2015 Sandia Corporation
#    This Software is released under the GPL license detailed
#    in the file "license.txt" in the top-level pyGSTi directory
#*****************************************************************
"""Functions for Fourier analysis of equally spaced time-series data"""

import numpy as _np
from scipy.fftpack import dct as _dct
from scipy.fftpack import idct as _idct
from scipy import convolve as _convolve

def DCT(x,counts=1,null_hypothesis=None):
    """
    Returns the Type-II discrete cosine transform of y, with an orthogonal normalization, where
    y is an array with elements related to the x array by
    
    y[k] = (x[k] - null_hypothesis[k])/normalizer;
    normalizer = sqrt(counts*null_hypothesis[k]*(1-null_hypothesis[k])).
    
    If null_hypothesis is None, then null_hypothesis[k] is mean(x)/counts, for all k. This is
    with the exception that when mean(x)/counts = 0 or 1 (when the above y[k] is ill-defined),
    in which case the zero vector is returned.
    
    Parameters
    ----------
    x : array
        Data string, on which the normalization and discrete cosine transformation is performed. If
        counts is not specified, this must be a bit string.
        
    null_hypothesis : array, optional
        If not None, an array to use in the normalization before the DCT. If None, it is
        taken to be an array in which every element is the mean of x.
        
    counts : int, optional
        TODO
                
    Returns
    -------
    array
        The DCT modes described above.

    """
    x_mean = _np.mean(x)
    N = len(x)
    
    assert(min(counts*_np.ones(N) - x) >= 0), "The number of counts must be >= to the maximum of the data array!"
    assert(min(x) >= 0), "The elements of the data array must be >= 0"
    
    # If the null hypothesis is not specified, we take our null hypothesis to be a constant bias
    # coin, with the bias given by the mean of the data / number of counts.
    if null_hypothesis is None:    
        null_hypothesis = x_mean/counts
        if null_hypothesis <= 0 or null_hypothesis >= 1:
            return _np.zeros(N)
    else:
        assert(min(null_hypothesis)>0 and max(null_hypothesis)<1), "All element of null_hypothesis must be in (0,1)!"
        assert(len(null_hypothesis) == N), "The null hypothesis array must be the same length as the data array!"
    
    return _dct((x - counts*null_hypothesis)/_np.sqrt(counts*null_hypothesis * (1 - null_hypothesis)),norm='ortho')

def IDCT(modes,null_hypothesis,counts=1):
    """
    Inverts the DCT function.
    
    Parameters
    ----------
    modes : array
        The fourier modes to be transformed to time-domain.
        
    null_hypothesis : array
        The null_hypothesis vector. For the IDCT it is not optional, and all
        elements of this array must be in (0,1).
        
    counts : int, optional
        TODO
        
    Returns
    -------
    array
        Inverse of the DCT function
        
    """
    assert(min(null_hypothesis)>0 and max(null_hypothesis)<1), "All element of null_hypothesis must be in (0,1)!"
    assert(len(null_hypothesis) == len(modes)), "The null hypothesis array must be the same length as the data array!"
    
    return  _idct(modes,norm='ortho')*_np.sqrt(counts*null_hypothesis * (1 - null_hypothesis)) + counts*null_hypothesis


def bartlett_spectrum(x,num_spectra,counts=1,null_hypothesis=None):
    """
    If N/num_spectra is not an integer, then 
    not all of the data points are used.
    
    TODO: docstring
    TODO: Make this work with multicount data.
    """
    
    N = len(x)
    length = int(_np.floor(N/num_spectra))
    
    if null_hypothesis is None:
        null_hypothesis = _np.mean(x)*_np.ones(N)/counts
    
    spectra = _np.zeros((num_spectra,length))
    bartlett_spectrum = _np.zeros(length)
    
    for i in range(0,num_spectra):
        spectra[i,:] = DCT(x[i*length:((i+1)*length)],counts=counts,
                           null_hypothesis=null_hypothesis[i*length:((i+1)*length)])**2
        
    bartlett_spectrum = _np.mean(spectra,axis=0)
                
    return bartlett_spectrum

def bartlett_spectrum_averaging(spectrum, num_spectra):
    """
    If N/num_spectra is not an integer, then 
    not all of the data points are used.
    
    TODO: docstring
    TODO: Make this work with multicount data.
    """ 
    length = int(_np.floor(len(spectrum)/num_spectra))  
    spectra = _np.zeros((num_spectra,length))
    for i in range(0,num_spectra):
        spectra[i,:] = spectrum[i*length:((i+1)*length)]
        
    bartlett_spectrum = _np.mean(spectra,axis=0)
                
    return bartlett_spectrum

def frequencies_from_timestep(timestep,T):
     
    return _np.arange(0,T)/(2*timestep*T)

def DCT_basis_function(omega, T, t):
    """
    Todo

    These are the *unnormalized* DCT amplitudes.
    """
    return _np.cos(omega*_np.pi*(t+0.5)/T)

#def create_DCT_basis_function(omega, T):
#
#    def DCT_basis_function(t): return _np.cos(omega*_np.pi*(t+0.5)/T)
#
#    return DCT_basis_function

def probability_from_DCT_amplitudes(alphas, omegas, T, t):
    """
    Todo

    This uses the *unnormalized* DCT amplitudes.
    """
    return _np.sum(_np.array([alphas[i]*DCT_basis_function(omegas[i], T, t) for i in range(len(omegas))]))

# -------------------------------- #
# ---------- Signal tools -------- #
# -------------------------------- #

def hoyer_sparsity_measure(p):
    """
    TODO: docstring
    """
    n = len(p)
    return (_np.sqrt(n) - _np.linalg.norm(p,1)/_np.linalg.norm(p,2))/(_np.sqrt(n)-1)

def renormalizer(p,method='logistic'):
    """
    TODO: docstring
    """
    if method == 'logistic':
    
        mean = _np.mean(p)
        nu = min([1-mean ,mean ]) 
        out = mean - nu + (2*nu)/(1 + _np.exp(-2*(p - mean)/nu))
     
    elif method == 'sharp':
        out = p.copy()
        out[p>1] = 1.
        out[p<0] = 0.
    
    else:
        raise ValueError("method should be 'logistic' or 'sharp'")
        
    return out

def logistic_transform(p, mean):
    """
    Todo
    """
    nu = min([1-mean ,mean ]) 
    out = mean - nu + (2*nu)/(1 + _np.exp(-2*(p - mean)/nu))
    return out

def reduce_DCT_amplitudes_until_probability_is_physical(alphas, omegas, T, epsilon=0.01, step_size=0.005):
    """

    """
    assert(0 in omegas)
    assert(0 == omegas[0]), "This function assume that the 0 mode is first in the list!"
    pt = [probability_from_DCT_amplitudes(alphas, omegas, T, t) for t in range(T)]
    newalphas = alphas.copy()

    if alphas[0] > (1 - epsilon) or alphas[0] < epsilon:
        newalphas[1:] = _np.zeros(len(newalphas)-1)
        print("Constraint can't be satisfied using this function, because the zero-mode contribution is outside the requested bounds!")
        return newalphas

    iteration = 0
    while max(pt) >= 1-epsilon or min(pt) <= epsilon:
        iteration += 1
        print("Interation {} of amplitude reduction.".format(iteration))
        # We don't change the amplitude of the DC component.
        for i in range(1,len(newalphas)):
            if newalphas[i] > 0.:
                newalphas[i] = newalphas[i] - step_size
                # If it changes sign we set it to zero.
                if newalphas[i] < 0.:
                    newalphas[i] = 0
            if newalphas[i] < 0.:
                newalphas[i] = newalphas[i] + step_size
                # If it changes sign we set it to zero.
                if newalphas[i] > 0.:
                    newalphas[i] = 0
        pt = [probability_from_DCT_amplitudes(newalphas, omegas, T, t) for t in range(T)]

    print("Estimate within bounds.")
    return newalphas 

def low_pass_filter(data,max_freq = None):
    """
    TODO: docstring
    """
    n = len(data) 
    
    if max_freq is None:
        max_freq = min(int(np.ceil(n/10)),50)
        
    modes = _dct(data,norm='ortho')
    
    if max_freq < n - 1:
        modes[max_freq + 1:] = _np.zeros(len(data)-max_freq-1)

    return _idct(modes,norm='ortho')

def moving_average(sequence, width=100):
    """
    TODO: docstring
    """
    seq_length = len(sequence)
    base = _convolve(_np.ones(seq_length), _np.ones((int(width),))/float(width), mode='same')
    signal = _convolve(sequence, _np.ones((int(width),))/float(width), mode='same')
    return signal/base 