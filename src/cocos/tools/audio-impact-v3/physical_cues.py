"""Restrained physical weapon studies, algorithmically modelled, not recordings.

Importing performs no I/O. synth_cue returns mono float64 with peak <= .58.
Layers are balanced by energy in their useful time windows. The output only
has a safety peak ceiling; quiet draws and air are never peak-normalised.
"""
from __future__ import annotations

import hashlib
import numpy as np
from scipy import signal

CUE_DURATIONS = {
    'war_swing': .22, 'war_slash': .25, 'war_armor': .30, 'war_finish': .34,
    'bow_draw': .62, 'bow_release': .25, 'bow_pierce': .22, 'bow_heavy': .31,
}
DESCRIPTIONS = {
    'war_swing': 'Short non-tonal blade air, separate from contact; no pitched steel sweep.',
    'war_slash': 'Dry cutting onset, brief damped steel modes, cloth/body compression.',
    'war_armor': 'Noise-excited non-harmonic plate with strong damping, no long bell.',
    'war_finish': 'A slightly thicker physical cut; restrained body and short steel decay.',
    'bow_draw': 'Quiet irregular hand/string friction and wood strain; no musical drone.',
    'bow_release': 'Short string-tension snap, damped bow-limb modes and a little arrow air.',
    'bow_pierce': 'Dry puncture, fabric drag and brief shaft damping; no gun-like boom.',
    'bow_heavy': 'The same puncture identity with slightly firmer wood/body contact.',
}
DESIGN_NOTES = {
    'userPreference': '2026-11-16: more realistic and restrained; shorter physical contact, limited low end, no exaggerated critical/kill accents.',
    'provenance': 'Original deterministic NumPy/SciPy material modelling; no recorded foley, AI audio, external samples, or listening approval claimed.',
    'sourceChange': 'V2 sinusoidal drum/body chirps, pitched steel sweeps, and sustained comb-string sound are replaced by finite noise excitation through damped physical-mode banks and irregular friction grains.',
    'mixing': 'Each layer is calibrated with RMS over a local active window. Layer ratios, microtiming, damping and excitation vary independently; no per-cue full-peak loudness normalisation.',
    'war': 'Air is separate; contact combines 1-15ms cut, 12-45ms cloth/body compression, and strongly damped inharmonic steel. Heavy is modestly thicker, never a bass drum.',
    'bow': 'Draw is quieter than release; string/bow-limb ringing is intentionally brief. Heavy preserves a puncture before its wood/body layer and avoids gunshot-like blast.',
    'acceptance': 'Synthesis and numerical checks only. Aesthetic acceptance requires user audition and device playback.',
}


def _rng(name, variation):
    seed = int.from_bytes(hashlib.sha256(f'physical-v3:{name}:{variation}'.encode()).digest()[:8], 'little')
    return np.random.default_rng(seed)


def _band(rng, n, rate, low, high):
    high = min(high, rate*.44)
    low = max(20., min(low, high*.8))
    filtered = signal.sosfilt(signal.butter(2, [low, high], 'bandpass', fs=rate, output='sos'), rng.standard_normal(n))
    return filtered / max(1e-9, float(np.sqrt(np.mean(filtered*filtered))))


def _env(t, attack, decay):
    return -np.expm1(-t/attack)*np.exp(-t/decay)


def _balance(x, rate, window, rms):
    """Energy calibration for an active local window, independent of peak."""
    a, b = [int(round(s*rate)) for s in window]
    region = x[max(0,a):min(len(x),b)]
    return x * (rms/max(1e-9, float(np.sqrt(np.mean(region*region)))))


def _place(destination, source, at, rate, gain=1.):
    start = max(0, int(round(at*rate)))
    count = min(len(destination)-start, len(source))
    if count > 0:
        destination[start:start+count] += source[:count]*gain


def _modes(rng, t, rate, frequencies, base_decay, excitation_ms=1.2):
    """Finite noise striking a bank of damped resonators, not free sine tones."""
    n = len(t)
    count = max(3, int(round(excitation_ms*.001*rate)))
    excitation = np.zeros(n)
    excitation[:count] = rng.standard_normal(count)*np.sin(np.linspace(0, np.pi, count))
    excitation = signal.sosfilt(signal.butter(1, min(7800,rate*.40), 'lowpass', fs=rate, output='sos'), excitation)
    out = np.zeros(n)
    for i, original in enumerate(frequencies):
        frequency = original*rng.uniform(.965,1.035)
        if frequency >= rate*.44:
            continue
        decay = base_decay*rng.uniform(.80,1.12)/(1+.12*i)
        radius = np.exp(-1/(rate*decay))
        mode = signal.lfilter([1.], [1., -2*radius*np.cos(2*np.pi*frequency/rate), radius*radius], excitation)
        # Each mode has finite excitation and a different damping/phase history.
        local = mode[:min(n,int(.055*rate))]
        mode /= max(1e-9,float(np.sqrt(np.mean(local*local))))
        out += mode*rng.uniform(.75,1.2)/(1+.18*i)
    return out


def _friction(rng, t, rate, low=450, high=3000, start=.003, end=.07, count=7):
    out = np.zeros_like(t)
    for at in np.sort(rng.uniform(start, end, count)):
        grain = _band(rng,len(t),rate,low*rng.uniform(.8,1.15),high)*_env(t,rng.uniform(.0004,.0015),rng.uniform(.002,.007))
        _place(out,grain,at,rate,rng.uniform(.45,1.0))
    return out


def _body(rng,t,rate,heavy=False):
    # Broad, damped pressure/fabric energy: no pitched kick or sub-bass tail.
    body = _band(rng,len(t),rate,110 if heavy else 160,1050)*_env(t,.0018,.027 if heavy else .018)
    cloth = _friction(rng,t,rate,350,2400,end=.045,count=5)
    return .76*body+.24*cloth


def synth_cue(name: str, variation: int = 1, sample_rate: int = 44100) -> np.ndarray:
    """Return one deterministic material cue; no files, playback, or cache writes."""
    if name not in CUE_DURATIONS:
        raise ValueError(f'Unknown physical cue: {name}')
    if not isinstance(variation,(int,np.integer)) or variation<1:
        raise ValueError('variation must be a positive integer')
    if not isinstance(sample_rate,(int,np.integer)) or sample_rate<22050:
        raise ValueError('sample_rate must be an integer >= 22050')
    rng = _rng(name,variation)
    t = np.arange(round(CUE_DURATIONS[name]*sample_rate))/sample_rate
    n = len(t)
    material = rng.uniform(.94,1.06)
    if name == 'war_swing':
        # A short turbulent displacement; two imperfect lobes, no pitched edge.
        centre = rng.uniform(.063,.077)
        air = _band(rng,n,sample_rate,280,3600)
        core = np.exp(-.5*((t-centre)/.028)**2)
        wake = np.exp(-.5*((t-centre-.030)/.026)**2)
        texture = _band(rng,n,sample_rate,1200,5600)
        x = _balance(air*core,sample_rate,(.025,.12),.077*material)
        x += _balance(texture*wake,sample_rate,(.04,.14),.018)
    elif name in ('war_slash','war_finish'):
        heavy = name=='war_finish'
        cut = _band(rng,n,sample_rate,550,6900)*_env(t,.00045,.010 if not heavy else .012)
        # Contact slides briefly rather than ringing as a pitched sword effect.
        scrape = _friction(rng,t,sample_rate,850,4800,end=.027,count=5)
        steel = _modes(rng,t,sample_rate,np.array([690,1117,1643,2359,3167,4231,5573])*material,.027 if not heavy else .033)
        body = _body(rng,t,sample_rate,heavy)
        x = _balance(cut,sample_rate,(0,.024),(.108 if heavy else .098)*material)
        x += _balance(scrape,sample_rate,(.004,.045),.027 if heavy else .023)
        x += _balance(steel,sample_rate,(.003,.060),.033 if heavy else .028)
        x += _balance(body,sample_rate,(.003,.055),.069 if heavy else .053)
    elif name=='war_armor':
        plate = _modes(rng,t,sample_rate,np.array([623,997,1483,2137,2849,3593,4583,5869])*material,.039)
        touch = _band(rng,n,sample_rate,650,6800)*_env(t,.00045,.008)
        cloth = _body(rng,t,sample_rate)
        x = _balance(plate,sample_rate,(.003,.075),.067)
        x += _balance(touch,sample_rate,(0,.021),.087*material)
        x += _balance(cloth,sample_rate,(.003,.05),.028)
    elif name=='bow_draw':
        # A quiet, irregular stretch: random friction/creak events, no oscillator.
        texture = _band(rng,n,sample_rate,190,2100)
        modulation = signal.sosfilt(signal.butter(2,32,'lowpass',fs=sample_rate,output='sos'),rng.standard_normal(n))
        modulation /= max(1e-9,float(np.std(modulation)))
        swell = np.maximum(0,np.sin(np.pi*t/t[-1]))**.8
        x = _balance(texture*swell*np.clip(.65+.20*modulation,.1,1.2),sample_rate,(.10,.50),.021)
        creak = np.zeros(n)
        for at in (.10,.26,.43):
            grain = _modes(rng,t,sample_rate,np.array([230,517,901])*material,.010,2.3)
            _place(creak,grain,at+rng.uniform(-.025,.025),sample_rate,rng.uniform(.6,1.))
        x += _balance(creak,sample_rate,(.08,.50),.010)
    elif name=='bow_release':
        # Strongly damped tension modes replace the old long Karplus/comb buzz.
        string = _modes(rng,t,sample_rate,np.array([183,373,571,784,1019,1287,1591,1973])*material,.018,.65)
        wood = _modes(rng,t,sample_rate,np.array([253,607,1139,1867])*material,.023,1.7)
        snap = _band(rng,n,sample_rate,750,6200)*_env(t,.0005,.0065)
        air = _band(rng,n,sample_rate,1100,4100)*np.exp(-.5*((t-.044)/.023)**2)
        x = _balance(snap,sample_rate,(0,.019),.073*material)
        x += _balance(string,sample_rate,(.001,.043),.044)
        x += _balance(wood,sample_rate,(.002,.052),.046)
        x += _balance(air,sample_rate,(.020,.095),.028)
    elif name in ('bow_pierce','bow_heavy'):
        heavy = name=='bow_heavy'
        puncture = _band(rng,n,sample_rate,1000,7200)*_env(t,.00035,.0058)
        drag = _friction(rng,t,sample_rate,530,3300,start=.003,end=.026,count=5)
        shaft = _modes(rng,t,sample_rate,np.array([332,749,1373,2281])*material,.018 if not heavy else .024,1.1)
        body = _body(rng,t,sample_rate,False)
        x = _balance(puncture,sample_rate,(0,.016),(.100 if heavy else .089)*material)
        x += _balance(drag,sample_rate,(.003,.040),.034)
        x += _balance(shaft,sample_rate,(.002,.045),.035 if heavy else .027)
        x += _balance(body,sample_rate,(.003,.050),.054 if heavy else .033)
    else:
        raise AssertionError(name)
    # A conservative common cleanup, not a substitute for the source changes.
    x = signal.sosfilt(signal.butter(2,70,'highpass',fs=sample_rate,output='sos'),x)
    x *= rng.uniform(.95,1.035)
    fade = max(2,round(sample_rate*.0012))
    x[:fade] *= np.linspace(0.,1.,fade)
    x[-fade:] *= np.linspace(1.,0.,fade)
    peak = float(np.max(np.abs(x)))
    x *= min(1.,.58/max(peak,1e-12))
    if not np.all(np.isfinite(x)):
        raise FloatingPointError(f'Non-finite synthesis result: {name}')
    return x.astype(np.float64,copy=False)
