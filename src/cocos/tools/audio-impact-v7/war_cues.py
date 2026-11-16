"""Weighted sword contacts with a clear, short material-specific steel response.

Pure import-safe synthesis; the v6 body is reused and no old source is changed.
Steel is a finite noisy mechanical excitation through non-harmonic damped modes,
not a bright equalizer boost, extra loudness, pitch chirp, or long bell.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
from pathlib import Path
import types

import numpy as np
from scipy import signal

RATE=44100
CUE_DURATIONS={'war_swing':.26,'war_slash':.40,'war_armor':.48,'war_finish':.56}
DESCRIPTIONS={
    'war_swing':'The weighted v6 blade-air movement is preserved; a swing does not invent a metal collision.',
    'war_slash':'Weighted cutting body with a light, clearly shaped steel contact and a short scrape.',
    'war_armor':'Firm blade-on-plate collision, audible inharmonic steel clank and a quickly damped scrape.',
    'war_finish':'Firm weighted cut with a fuller short steel response, below a prolonged bell or hammer crash.',
}
DESIGN_NOTES={
    'userPreference':'2026-11-16: sword and arrow impacts should have metal-collision identity; retain v6 weight and short bow air, without returning to sharp thin pings.',
    'provenance':'Original deterministic NumPy/SciPy material modelling added to the v6 source. No recordings, downloads, AI calls, external samples or listening acceptance claimed.',
    'body':'The existing thick v6 sword/body waveform is retained as the foundation, at its original gain before the common safety ceiling.',
    'steelStructure':'A 1.3ms irregular mechanical excitation and a small trailing contact fold drive separate non-harmonic modes near 700/1100/1700/2400Hz. Modal decay is 36-64ms with shorter high-mode damping; the result is a contact clank rather than continuous high noise.',
    'materialDifference':'Soft contact uses a light blade resonance and small scrape. Armor has more independent plate motion and a clearer short scrape. Finish sits between them. Swing remains unchanged with no manufactured hit.',
    'spectralBalance':'New energy is concentrated in the 650-2600Hz material band while the accepted 180-700Hz body remains. Modes and exciter are changed, not the overall pitch or a global treble/gain control.',
    'tail':'Steel response is finite, with no room reverb or long ringing bell; v6 dark aftermotion remains subordinate.',
    'mix':'Local active-window RMS assigns contact-layer energy; a final .64 ceiling is protection only. Three variants alter excitation, contact spacing, modal damping and frequency jitter.',
    'comparisonApi':'synth_contact(variation=1,material="soft"|"armor",sample_rate=44100) maps to the same war_slash/war_armor sources used in demonstrations.',
    'acceptance':'Spectrum and decay checks describe the source changes; human and device listening remain pending.',
}


@lru_cache(maxsize=1)
def _v6():
    path=Path(__file__).resolve().parent.parent/'audio-impact-v6/physical_cues.py'
    module=types.ModuleType('_v6_weighted_sword_for_v7')
    module.__file__=str(path)
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),module.__dict__)
    return module


def _rng(name,variation):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(f'steel-contact-v7:{name}:{variation}'.encode()).digest()[:8],'little'))


def _energy(x,rate,a,b,rms):
    local=x[round(a*rate):min(len(x),round(b*rate))]
    return x*(rms/max(1e-12,float(np.sqrt(np.mean(local*local)))))


def _place(dest,source,at,rate,gain=1.):
    start=round(at*rate)
    count=min(len(dest)-start,len(source))
    if count>0:
        dest[start:start+count]+=source[:count]*gain


def _plate(rng,rate,seconds,armor=False,heavy=False):
    n=round(seconds*rate)
    t=np.arange(n)/rate
    excitation=np.zeros(n)
    length=max(4,round(.0013*rate))
    excitation[:length]=rng.standard_normal(length)*np.sin(np.linspace(0,np.pi,length))
    # A quieter second physical contact is a fraction of a millimetre of slip,
    # not a decorative repeated clang or a regular amplitude modulation.
    length2=max(4,round(.0010*rate))
    fold=rng.standard_normal(length2)*np.sin(np.linspace(0,np.pi,length2))
    _place(excitation,fold,rng.uniform(.0045,.0075),rate,.20 if armor else .10)
    excitation=signal.sosfilt(signal.butter(2,[420,min(3400,rate*.43)],'bandpass',fs=rate,output='sos'),excitation)
    frequencies=[701,1117,1693,2381] if armor else [769,1217,1811,2519]
    decay=.064 if armor else .049 if heavy else .036
    gains=[.76,1.,.72,.41] if armor else [.72,1.,.54,.25]
    response=np.zeros(n)
    for i,(freq,gain) in enumerate(zip(frequencies,gains)):
        frequency=freq*rng.uniform(.973,1.027)
        tau=decay*rng.uniform(.88,1.12)/(1+.19*i)
        radius=np.exp(-1/(rate*tau))
        mode=signal.lfilter([1.],[1.,-2*radius*np.cos(2*np.pi*frequency/rate),radius*radius],excitation)
        response+=_energy(mode,rate,.004,.090,1.)*gain
    response*=np.minimum(1.,t/.0010)
    response*=np.clip((seconds-t)/.025,0,1)
    return response


def _scrape(shared,rng,rate,armor):
    seconds=.045 if armor else .034
    t=np.arange(round(seconds*rate))/rate
    texture=shared._band(rng,len(t),rate,650 if armor else 850,2850)
    # A small finite slide after contact, with one uneven pressure break.
    envelope=-np.expm1(-t/.0015)*np.exp(-t/(.0075 if armor else .0055))
    pressure=1-.26*np.exp(-.5*((t-rng.uniform(.008,.012))/.0018)**2)
    result=texture*envelope*pressure
    result[-max(2,round(.008*rate)):]*=np.linspace(1.,0.,max(2,round(.008*rate)))
    return result


def synth_cue(name: str,variation: int=1,sample_rate: int=RATE) -> np.ndarray:
    """Finite mono float64 sword cue, peak <= .64, no I/O or playback writes."""
    if name not in CUE_DURATIONS:
        raise ValueError(f'Unknown sword cue: {name}')
    if not isinstance(variation,(int,np.integer)) or variation<1:
        raise ValueError('variation must be a positive integer')
    if not isinstance(sample_rate,(int,np.integer)) or sample_rate<22050:
        raise ValueError('sample_rate must be an integer >= 22050')
    previous=_v6()
    out=previous.synth_cue(name,variation,sample_rate).copy()
    if name=='war_swing':
        return out
    shared=previous._v5()
    rng=_rng(name,variation)
    armor=name=='war_armor'
    heavy=name=='war_finish'
    steel=_plate(rng,sample_rate,.30 if armor else .25,armor,heavy)
    steel=_energy(steel,sample_rate,.004,.085,.061 if armor else .045 if heavy else .034)
    _place(out,steel,.002,sample_rate)
    scrape=_scrape(shared,rng,sample_rate,armor)
    scrape=_energy(scrape,sample_rate,.003,.025,.024 if armor else .013 if heavy else .010)
    _place(out,scrape,.006,sample_rate)
    if not np.all(np.isfinite(out)):
        raise FloatingPointError('Non-finite steel-contact synthesis')
    fade=max(2,round(.012*sample_rate))
    out[-fade:]*=np.linspace(1,0,fade)
    out*=min(1.,.64/max(1e-12,float(np.max(np.abs(out)))))
    return np.asarray(out,dtype=np.float64)


def synth_contact(variation: int=1,material: str='armor',sample_rate: int=RATE) -> np.ndarray:
    """Direct material comparison using the same sources as the cue bank."""
    if material not in ('armor','soft'):
        raise ValueError('material must be armor or soft')
    return synth_cue('war_armor' if material=='armor' else 'war_slash',variation,sample_rate)
