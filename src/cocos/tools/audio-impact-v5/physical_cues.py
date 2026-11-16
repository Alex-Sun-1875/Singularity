"""Accepted physical contacts with longer, material-specific audible decays.

Import performs no I/O. The previous physical source is loaded on first use
without bytecode writes; no former source or output is modified. No playback,
downloads, recordings, external samples, AI calls, or generic reverb.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
from pathlib import Path
import types

import numpy as np
from scipy import signal

RATE = 44100
CUE_DURATIONS = {
    'war_swing': .30, 'war_slash': .42, 'war_armor': .52, 'war_finish': .60,
    'bow_draw': .70, 'bow_release': .42, 'bow_pierce': .35, 'bow_heavy': .52,
}
DESCRIPTIONS = {
    'war_swing': 'Accepted short blade movement followed by a softer finite air wake.',
    'war_slash': 'Accepted cutting contact with damped steel motion and a brief blade-air release.',
    'war_armor': 'Accepted plate hit with a longer, subordinate inharmonic steel vibration.',
    'war_finish': 'Accepted firm cut with a slightly fuller steel/body decay and trailing air.',
    'bow_draw': 'Accepted irregular tension/friction with a short quiet extension, cut at release by the arranger.',
    'bow_release': 'Accepted tension snap with lower string/limb recoil and a short arrow-air wake.',
    'bow_pierce': 'Accepted dry puncture with finite shaft vibration, fabric movement and fading air.',
    'bow_heavy': 'Accepted firmer puncture followed by modestly longer shaft/wood recoil, no extra blast.',
}
DESIGN_NOTES = {
    'userPreference': '2026-11-16: single sounds may last slightly longer; add profession-specific material aftersound while keeping the accepted attack.',
    'provenance': 'Original deterministic NumPy/SciPy modelling plus the accepted v3 physical source, which was unchanged in v4. No real recordings, AI, downloads, third-party samples or artistic acceptance claimed.',
    'preserved': 'The accepted source is copied exactly at the start. Contact tails begin at 45-60ms, movement tails at 110ms; the v4 arranger contact gain remains a separate mix choice.',
    'war': 'A finite noise excitation drives differently damped non-harmonic steel modes; a separate turbulent blade wake carries movement. No sinusoidal bass drum, pitch chirp or shared reverb.',
    'bow': 'Low-level residual tension/limb modes and different shaft modes create recoil/wood vibration. Finite air and fibre packets are subordinate, rather than a generic buzz or long musical string note.',
    'balance': 'Tail energy is tied to the accepted active body RMS, with moderate independent variation, never independently peak-normalised. Tail onset is faded and source peaks remain bounded by .64.',
    'arrangement': 'The arranger should still truncate preparation at actual release. Per-contact aftersound is finite and quieter so successive attacks can overlap.',
    'acceptance': 'Late energy and effective duration verify actual tail changes; listening and target-device acceptance remain pending.',
}


@lru_cache(maxsize=1)
def _accepted():
    """Lazy source read/compile, deliberately without __pycache__ writes."""
    path=Path(__file__).resolve().parent.parent/'audio-impact-v3/physical_cues.py'
    module=types.ModuleType('_accepted_physical_v3_for_v5')
    module.__file__=str(path)
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),module.__dict__)
    return module


def _rng(name,variation):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(f'physical-tail-v5:{name}:{variation}'.encode()).digest()[:8],'little'))


def _band(rng,n,rate,low,high):
    high=min(high,rate*.44)
    low=min(max(25.,low),high*.8)
    x=signal.sosfilt(signal.butter(2,[low,high],'bandpass',fs=rate,output='sos'),rng.standard_normal(n))
    return x/max(1e-10,float(np.sqrt(np.mean(x*x))))


def _energy(x,rate,start,end,rms):
    segment=x[round(start*rate):min(len(x),round(end*rate))]
    return x*(rms/max(1e-10,float(np.sqrt(np.mean(segment*segment)))))


def _fade(x,rate,in_seconds=.008,out_seconds=.018):
    a=min(len(x),max(2,round(in_seconds*rate)))
    b=min(len(x),max(2,round(out_seconds*rate)))
    x[:a]*=np.linspace(0.,1.,a)
    x[-b:]*=np.linspace(1.,0.,b)
    return x


def _place(dest,source,at,rate,gain=1.):
    start=round(at*rate)
    count=min(len(dest)-start,len(source))
    if count>0:
        dest[start:start+count]+=source[:count]*gain


def _modes(rng,rate,seconds,frequencies,decay):
    """One finite physical excitation, with several non-identical decay modes."""
    n=max(2,round(seconds*rate))
    excitation=np.zeros(n)
    count=min(n,max(4,round(.002*rate)))
    excitation[:count]=rng.standard_normal(count)*np.sin(np.linspace(0,np.pi,count))
    out=np.zeros(n)
    for i,freq in enumerate(frequencies):
        frequency=freq*rng.uniform(.97,1.03)
        radius=np.exp(-1/(rate*decay*rng.uniform(.85,1.15)/(1+.13*i)))
        mode=signal.lfilter([1.],[1.,-2*radius*np.cos(2*np.pi*frequency/rate),radius*radius],excitation)
        mode=_energy(mode,rate,.008,.090,1.)
        out+=mode*rng.uniform(.75,1.15)/(1+.27*i)
    return _fade(out,rate,.009,.025)


def _air(rng,rate,seconds,low,high,attack,decay):
    t=np.arange(round(seconds*rate))/rate
    envelope=-np.expm1(-t/attack)*np.exp(-t/decay)
    # A finite non-periodic wake, rather than continuous hiss or reverb.
    texture=_band(rng,len(t),rate,low,high)
    return _fade(texture*envelope,rate,.006,.025)


def _rms(x,rate,a,b):
    segment=x[round(a*rate):min(len(x),round(b*rate))]
    return max(.001,float(np.sqrt(np.mean(segment*segment))))


def synth_cue(name: str,variation: int=1,sample_rate: int=RATE) -> np.ndarray:
    """Mono float64 with accepted contact, finite audible tail and peak <= .64."""
    if name not in CUE_DURATIONS:
        raise ValueError(f'Unknown physical cue: {name}')
    if not isinstance(variation,(int,np.integer)) or variation<1:
        raise ValueError('variation must be a positive integer')
    if not isinstance(sample_rate,(int,np.integer)) or sample_rate<22050:
        raise ValueError('sample_rate must be an integer >= 22050')
    accepted=_accepted().synth_cue(name,variation,sample_rate)
    out=np.zeros(round(CUE_DURATIONS[name]*sample_rate),np.float64)
    out[:len(accepted)]=accepted
    rng=_rng(name,variation)
    material=rng.uniform(.94,1.06)
    if name=='war_swing':
        strength=_rms(accepted,sample_rate,.025,.12)
        wake=_air(rng,sample_rate,.19,290,3100,.014,.061)
        wake=_energy(wake,sample_rate,.025,.13,strength*.20*material)
        _place(out,wake,.110,sample_rate)
    elif name.startswith('war_'):
        armor=name=='war_armor'
        heavy=name=='war_finish'
        strength=_rms(accepted,sample_rate,.003,.055)
        at=.060 if armor else .055
        seconds=CUE_DURATIONS[name]-at
        frequencies=([647,1103,1723,2477,3511] if armor else [827,1391,2053,2947,4127])
        decay=.103 if armor else .093 if heavy else .074
        steel=_modes(rng,sample_rate,seconds,np.array(frequencies)*material,decay)
        steel=_energy(steel,sample_rate,.025,.15,strength*(.21 if armor else .18 if heavy else .155))
        _place(out,steel,at,sample_rate)
        if not armor:
            wake=_air(rng,sample_rate,min(seconds,.27),330,2600,.016,.069 if heavy else .055)
            wake=_energy(wake,sample_rate,.025,.14,strength*(.095 if heavy else .075))
            _place(out,wake,at+.027,sample_rate)
    elif name=='bow_draw':
        strength=_rms(accepted,sample_rate,.12,.50)
        # Quiet continued tension/friction; actual release still cuts this off.
        extension=_air(rng,sample_rate,.23,240,1900,.024,.075)
        extension=_energy(extension,sample_rate,.025,.16,strength*.28)
        _place(out,extension,.470,sample_rate)
    else:
        release=name=='bow_release'
        heavy=name=='bow_heavy'
        strength=_rms(accepted,sample_rate,.002,.050)
        at=.050 if release else .045
        seconds=CUE_DURATIONS[name]-at
        if release:
            frequencies=[181,379,593,823,1091]
            decay=.076
            relative=.16
        else:
            frequencies=[347,809,1439,2293]
            decay=.086 if heavy else .062
            relative=.17 if heavy else .14
        recoil=_modes(rng,sample_rate,seconds,np.array(frequencies)*material,decay)
        recoil=_energy(recoil,sample_rate,.020,.14,strength*relative)
        _place(out,recoil,at,sample_rate)
        wake=_air(rng,sample_rate,min(.21,seconds),1250 if release else 650,3900 if release else 2700,.012,.047)
        wake=_energy(wake,sample_rate,.020,.12,strength*(.075 if release else .055))
        _place(out,wake,at+.027,sample_rate)
    if not np.all(np.isfinite(out)):
        raise FloatingPointError('Non-finite physical aftersound')
    # Preserve the copied start exactly; the accepted source already starts at 0.
    fade=min(len(out),max(2,round(.018*sample_rate)))
    out[-fade:]*=np.linspace(1.,0.,fade)
    out*=min(1.,.64/max(1e-12,float(np.max(np.abs(out)))))
    return out
