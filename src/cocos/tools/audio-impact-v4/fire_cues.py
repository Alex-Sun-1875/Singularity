"""Punchier combustion studies retaining v3's irregular natural flame texture.

Pure import-safe synthesis API. No files, playback, downloads, AI, or recordings.
The stronger ignition/body/roll are source changes, not a gain-only revision.
"""
from __future__ import annotations

import hashlib
import numpy as np
from scipy import signal

RATE = 44100
CUE_DURATIONS = {'fir_charge': .64, 'fir_burst': .82, 'fir_wall': 2.60}
DESCRIPTIONS = {
    'fir_charge': 'Irregular gathering flame with a modest compression; quieter than the impact.',
    'fir_burst': 'Defined ignition contact, short low-mid pressure volume, rolling combustion and sparse embers.',
    'fir_wall': 'One small ignition followed by sparse natural flame tongues; no repeating explosions.',
}
DESIGN_NOTES = {
    'userPreference': '2026-11-16: v3 is broadly acceptable; make fire/lightning more explosive while retaining natural material identity.',
    'provenance': 'Original deterministic NumPy/SciPy synthesis; no recordings, AI calls, external samples or downloads.',
    'sourceChanges': {
        'ignition': 'Several brief, differently damped micro-fronts establish a 5-25ms contact instead of simply raising the old flame bed.',
        'body': 'Finite noise excites damped 146/229/347/493Hz pressure-volume modes, reinforced by a short 120-450Hz turbulent packet. No sub-bass sine/kick oscillator.',
        'expansion': 'Independent irregular packets expand over 70-250ms with changing bandwidth and non-repeating timing; the low-mid roll is separate from the ignition transient.',
        'tail': 'Sparse embers only, progressively weaker; no long constant white-noise wall or periodic flutter modulation.',
        'chargeAndWall': 'Gathering is modestly denser and still below impact. Wall uses a small one-off ignition and intermittent flame tongues, not a sequence of full explosions.',
    },
    'mix': 'Local active-window energy controls ignition/body balance; final gain is only a safety cap at .64. Three variants independently change excitation, microtiming, modes and packet shapes.',
    'comparison': 'Assess v3/v4 at equal peak or matched loudness. Greater onset/body contrast is separate from overall playback loudness.',
    'acceptance': 'Numerical envelope/energy verification is not artistic or device listening acceptance.',
}


def _rng(name, variation):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(f'fire-impact-v4:{name}:{variation}'.encode()).digest()[:8], 'little'))


def _time(seconds, rate):
    return np.arange(max(2,round(seconds*rate)),dtype=np.float64)/rate


def _noise(rng, n, rate, low, high):
    high = min(high,rate*.44)
    low = min(max(20.,low),high*.8)
    x = signal.sosfilt(signal.butter(2,[low,high],'bandpass',fs=rate,output='sos'),rng.standard_normal(n))
    return x/max(1e-9,float(np.sqrt(np.mean(x*x))))


def _place(dest, source, at, rate, gain=1.):
    begin=round(at*rate)
    skip=max(0,-begin)
    begin=max(0,begin)
    count=min(len(dest)-begin,len(source)-skip)
    if count>0:
        dest[begin:begin+count]+=source[skip:skip+count]*gain


def _packet(rng,rate,seconds,low,high,attack,decay):
    t=_time(seconds,rate)
    envelope=-np.expm1(-t/attack)*np.exp(-t/decay)
    # Every tongue ends; overlapping finite breaths do not become a noise bed.
    fade=np.minimum(1.,(seconds-t)/min(.018,seconds*.24))
    return _noise(rng,len(t),rate,low,high)*envelope*np.sin(fade*np.pi/2)**2


def _energy(x,rate,start,end,rms):
    segment=x[round(start*rate):min(len(x),round(end*rate))]
    return x*(rms/max(1e-9,float(np.sqrt(np.mean(segment*segment)))))


def _ember(rng,rate):
    return _packet(rng,rate,.034,rng.uniform(950,1450),rng.uniform(3400,5200),.00045,rng.uniform(.0026,.0043))


def _pressure(rng,rate):
    """Finite compression front plus noise-excited volume, not a sine drum."""
    t=_time(.105,rate)
    width=rng.uniform(.00085,.00115)
    phase=(t-.0044)/width
    shock=-phase*np.exp(-.5*phase*phase)
    shock*=.17
    count=max(4,round(.0016*rate))
    excitation=np.zeros(len(t))
    excitation[:count]=rng.standard_normal(count)*np.sin(np.linspace(0,np.pi,count))
    body=np.zeros(len(t))
    for freq,gain,decay in ((146,.74,.026),(229,1.,.025),(347,.70,.019),(493,.32,.013)):
        frequency=freq*rng.uniform(.96,1.04)
        radius=np.exp(-1/(rate*decay*rng.uniform(.88,1.14)))
        mode=signal.lfilter([1.],[1.,-2*radius*np.cos(2*np.pi*frequency/rate),radius*radius],excitation)
        mode=_energy(mode,rate,0,.055,1.)
        body+=mode*gain
    body=_energy(body,rate,.002,.060,.092)
    body*=np.clip((.105-t)/.018,0,1)
    return shock+body


def _burst(rng,rate,n):
    out=np.zeros(n)
    # Three short changing combustion fronts, not a louder copy of the old bed.
    ignition=_packet(rng,rate,.038,410,6200,.00035,rng.uniform(.006,.008))
    ignition=_energy(ignition,rate,.001,.023,.106)
    _place(out,ignition,.0010,rate)
    fold=_packet(rng,rate,.027,680,4300,.0005,.0045)
    _place(out,fold,.011+rng.uniform(-.0015,.0015),rate,.17)
    _place(out,_pressure(rng,rate),.005,rate)
    volume=_packet(rng,rate,.125,115,470,.0025,rng.uniform(.025,.035))
    volume=_energy(volume,rate,.006,.060,.070)
    _place(out,volume,.014,rate)
    # The expansion has its own slower attack and evolving low-mid bandwidth.
    for at,seconds,gain,low,high in (
        (.026,.160,.250,170,2200),(.079,.180,.225,130,1700),
        (.139,.175,.155,185,2500),(.218,.155,.088,230,2600),
        (.319,.140,.038,290,2800)):
        at+=rng.uniform(-.006,.006)
        breath=_packet(rng,rate,seconds,low*rng.uniform(.9,1.1),high*rng.uniform(.92,1.08),rng.uniform(.007,.014),rng.uniform(.032,.049))
        _place(out,breath,at,rate,gain)
    for at,gain in ((.255,.034),(.388,.023),(.529,.013),(.668,.006)):
        _place(out,_ember(rng,rate),at+rng.uniform(-.011,.011),rate,gain)
    return out


def _charge(rng,rate,n):
    out=np.zeros(n)
    _place(out,_ember(rng,rate),.025,rate,.038)
    for i,at in enumerate((.055,.138,.232,.323,.411,.495)):
        breath=_packet(rng,rate,rng.uniform(.092,.130),rng.uniform(190,310),rng.uniform(1600,2400),.010,rng.uniform(.030,.044))
        _place(out,breath,at+rng.uniform(-.008,.008),rate,.073+.014*i)
    # A small pressure gathering, not an early full-strength hit.
    _place(out,_pressure(rng,rate),.425,rate,.20)
    return out


def _wall(rng,rate,n):
    out=np.zeros(n)
    _place(out,_ember(rng,rate),.022,rate,.046)
    _place(out,_pressure(rng,rate),.038,rate,.12)
    at=.052
    while at<2.28:
        duration=rng.uniform(.120,.190)
        breath=_packet(rng,rate,duration,rng.uniform(230,370),rng.uniform(1550,2450),rng.uniform(.014,.026),rng.uniform(.037,.056))
        gain=rng.uniform(.060,.112)*min(1.,(at+.06)/.20)*min(1.,(2.42-at)/.48)
        _place(out,breath,at,rate,gain)
        at+=rng.uniform(.110,.168)
    for at in (.183,.526,.893,1.416,1.961,2.271):
        _place(out,_ember(rng,rate),at+rng.uniform(-.022,.022),rate,rng.uniform(.011,.023)*min(1.,(2.5-at)/.5))
    return out


def synth_cue(name: str, variation: int=1, sample_rate: int=RATE) -> np.ndarray:
    """Generate deterministic finite mono float64 samples, peak <= .64."""
    if name not in CUE_DURATIONS:
        raise ValueError(f'Unknown fire cue: {name}')
    if not isinstance(variation,(int,np.integer)) or variation<1:
        raise ValueError('variation must be a positive integer')
    if not isinstance(sample_rate,(int,np.integer)) or sample_rate<22050:
        raise ValueError('sample_rate must be an integer >= 22050')
    rng=_rng(name,variation)
    n=round(CUE_DURATIONS[name]*sample_rate)
    if name=='fir_burst':
        audio=_burst(rng,sample_rate,n)
    elif name=='fir_charge':
        audio=_charge(rng,sample_rate,n)
    else:
        audio=_wall(rng,sample_rate,n)
    audio=signal.sosfilt(signal.butter(2,80 if name=='fir_burst' else 115,'highpass',fs=sample_rate,output='sos'),audio)
    if not np.all(np.isfinite(audio)):
        raise FloatingPointError('Non-finite combustion synthesis')
    fade_in=max(2,round(.0010*sample_rate))
    fade_out=max(2,round(.012*sample_rate))
    audio[:fade_in]*=np.linspace(0,1,fade_in)
    audio[-fade_out:]*=np.linspace(1,0,fade_out)
    audio*=min(1.,.64/max(1e-12,float(np.max(np.abs(audio)))))
    return np.asarray(audio,dtype=np.float64)
