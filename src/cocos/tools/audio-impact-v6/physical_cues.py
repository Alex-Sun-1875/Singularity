"""Heavier physical contacts with a deliberately short bow-air component.

Pure import-safe API; v5's material helpers are lazily reused without bytecode
writes. Sources are rebuilt with a larger damped body and less bright contact,
not globally pitch-shifted or merely low-passed versions of the old sounds.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
from pathlib import Path
import types

import numpy as np
from scipy import signal

RATE=44100
CUE_DURATIONS={
    'war_swing':.26,'war_slash':.40,'war_armor':.48,'war_finish':.56,
    'bow_draw':.62,'bow_release':.30,'bow_pierce':.30,'bow_heavy':.42,
}
DESCRIPTIONS={
    'war_swing':'Dense short blade displacement with a darker finite wake, no bright whistle.',
    'war_slash':'Damped weighted cutting contact with a small steel edge and dark steel aftermotion.',
    'war_armor':'Firm padded plate impact, low-mid material body and subordinate dark steel vibration.',
    'war_finish':'Heavier compressed cut/body, still a blade contact rather than a hammer or drum.',
    'bow_draw':'Low wood/string tension friction with short irregular creaks, no long air sweep.',
    'bow_release':'Firm string latch and bow-limb recoil, with only 65ms of faint arrow air.',
    'bow_pierce':'Weighted fibre puncture and short shaft recoil; only 50ms of subordinate air.',
    'bow_heavy':'Thicker puncture/bow-wood body and dark shaft vibration, no extended swoosh.',
}
AIR_WINDOWS={
    'bow_release':(.018,.083),
    'bow_pierce':(.014,.064),
    'bow_heavy':(.014,.074),
}
DESIGN_NOTES={
    'userPreference':'2026-11-16: all professions should feel heavier and less bright; bow specifically must not have a long wind sound.',
    'provenance':'Original deterministic NumPy/SciPy modelling with reused v5 material helpers; no recordings, AI, downloads, external samples or claimed listening approval.',
    'sourceChanges':{
        'weight':'Rebuilt finite 165-720Hz noise-excited compression and 180-700Hz wood/body layers become the main contact, rather than raising gain or lowering pitch on the old bright transient.',
        'war':'The cutting edge has less energy and less high-frequency bandwidth; lower non-harmonic steel modes are damped behind the contact. No sine kick, hammer boom or chirp.',
        'bow':'A firm string latch, low bow-limb resonance and weighted puncture replace bright snap-first balance. Shaft recoil stays separate from air.',
        'bowAir':'V5 added 210ms wakes beginning 72-77ms after contact. Those wakes and the old longer release-air source are removed. New isolated packets last 50/60/65ms and are finished by 64/74/83ms, not merely hidden with EQ.',
    },
    'bowAirWindowsSeconds':AIR_WINDOWS,
    'tail':'Darker finite material tails remain below contact; bows have no additional late air layer.',
    'mix':'Active-window RMS balances individual material layers. Final .64 cap is protection only, not a uniform peak/loudness target.',
    'arrangement':'Keep the v5 schedule/gain and cut preparation at actual release; these are source-timbre changes.',
    'acceptance':'Frequency/envelope measures describe the changes; human and target-device listening acceptance remain pending.',
}


@lru_cache(maxsize=1)
def _v5():
    path=Path(__file__).resolve().parent.parent/'audio-impact-v5/physical_cues.py'
    module=types.ModuleType('_v5_material_helpers_for_v6')
    module.__file__=str(path)
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),module.__dict__)
    return module


def _rng(name,variation):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(f'weighted-physical-v6:{name}:{variation}'.encode()).digest()[:8],'little'))


def _packet(shared,rng,n,rate,low,high,attack,decay):
    t=np.arange(n)/rate
    return shared._band(rng,n,rate,low,high)*(-np.expm1(-t/attack))*np.exp(-t/decay)


def _scale(shared,x,rate,a,b,rms):
    return shared._energy(x,rate,a,b,rms)


def _dark_tail(shared,rng,rate,seconds,frequencies,decay,rms):
    x=shared._modes(rng,rate,seconds,frequencies,decay)
    return _scale(shared,x,rate,.020,min(.15,seconds),rms)


def synth_cue(name: str,variation: int=1,sample_rate: int=RATE) -> np.ndarray:
    """Generate finite mono float64 material samples with peak <= .64."""
    if name not in CUE_DURATIONS:
        raise ValueError(f'Unknown physical cue: {name}')
    if not isinstance(variation,(int,np.integer)) or variation<1:
        raise ValueError('variation must be a positive integer')
    if not isinstance(sample_rate,(int,np.integer)) or sample_rate<22050:
        raise ValueError('sample_rate must be an integer >= 22050')
    shared=_v5()
    rng=_rng(name,variation)
    n=round(CUE_DURATIONS[name]*sample_rate)
    t=np.arange(n)/sample_rate
    out=np.zeros(n,np.float64)
    material=rng.uniform(.94,1.06)
    if name=='war_swing':
        centre=rng.uniform(.062,.074)
        core=shared._band(rng,n,sample_rate,190,2250)*np.exp(-.5*((t-centre)/.030)**2)
        out+=_scale(shared,core,sample_rate,.025,.12,.068*material)
        wake=shared._air(rng,sample_rate,.15,240,1800,.016,.050)
        wake=_scale(shared,wake,sample_rate,.025,.12,.012)
        shared._place(out,wake,.110,sample_rate)
    elif name.startswith('war_'):
        armor=name=='war_armor'
        heavy=name=='war_finish'
        # Broad damped mass, not a pitched bass hit. The transient edge remains
        # physically distinct and shorter than the body it initiates.
        body=_packet(shared,rng,n,sample_rate,165 if heavy else 180,720,.0018,.029 if heavy else .024)
        body=_scale(shared,body,sample_rate,.003,.060,.102 if heavy else .088 if armor else .084)
        edge=_packet(shared,rng,n,sample_rate,650,3600 if armor else 3200,.0008,.0085)
        edge=_scale(shared,edge,sample_rate,.001,.022,.043 if armor else .047 if heavy else .039)
        fibers=_packet(shared,rng,n,sample_rate,260,1450,.0025,.025)
        fibers=_scale(shared,fibers,sample_rate,.004,.055,.029)
        steel=shared._modes(rng,sample_rate,CUE_DURATIONS[name],np.array([521,883,1427,2273])*material,.029 if armor else .024)
        steel=_scale(shared,steel,sample_rate,.004,.065,.036 if armor else .023)
        out+=body+edge+fibers+steel
        at=.055
        tail=_dark_tail(shared,rng,sample_rate,CUE_DURATIONS[name]-at,
                        np.array([487,797,1279,1993])*material,
                        .098 if armor else .085 if heavy else .069,
                        .017 if armor else .016 if heavy else .012)
        shared._place(out,tail,at,sample_rate)
        if not armor:
            wake=shared._air(rng,sample_rate,.19 if heavy else .16,220,1600,.016,.058)
            wake=_scale(shared,wake,sample_rate,.025,.13,.007)
            shared._place(out,wake,.085,sample_rate)
    elif name=='bow_draw':
        # Tension/friction, not a sustained wind source or a pitched string note.
        friction=shared._band(rng,n,sample_rate,140,1150)
        swell=np.maximum(0,np.sin(np.pi*t/t[-1]))**.8
        out+=_scale(shared,friction*swell,sample_rate,.10,.50,.021)
        for at in (.11,.28,.43):
            creak=shared._modes(rng,sample_rate,.075,np.array([207,397,653])*material,.014)
            creak=_scale(shared,creak,sample_rate,.008,.055,.012)
            shared._place(out,creak,at+rng.uniform(-.018,.018),sample_rate)
    else:
        release=name=='bow_release'
        heavy=name=='bow_heavy'
        body=_packet(shared,rng,n,sample_rate,170 if heavy else 185,700,.0016,.027 if heavy else .022)
        body=_scale(shared,body,sample_rate,.003,.055,.091 if heavy else .078 if release else .074)
        latch=_packet(shared,rng,n,sample_rate,450 if release else 650,2350 if release else 3150,.0009,.0065)
        latch=_scale(shared,latch,sample_rate,.001,.018,.047 if release else .043 if heavy else .038)
        modes=shared._modes(rng,sample_rate,CUE_DURATIONS[name],
                           np.array([191,389,647,1019] if release else [273,541,937,1447])*material,
                           .028 if release else .025)
        modes=_scale(shared,modes,sample_rate,.003,.060,.040 if release else .031)
        out+=body+latch+modes
        at=.048
        recoil=_dark_tail(shared,rng,sample_rate,CUE_DURATIONS[name]-at,
                         np.array([193,391,629,929] if release else [267,517,887,1333])*material,
                         .063 if heavy else .050,
                         .014 if heavy else .011)
        shared._place(out,recoil,at,sample_rate)
        # Actual air support is bounded in time. No late 210ms v5 wake remains.
        begin,end=AIR_WINDOWS[name]
        air=shared._air(rng,sample_rate,end-begin,850 if release else 540,
                        2700 if release else 2100,.004,.016)
        air=_scale(shared,air,sample_rate,.005,end-begin-.010,.009 if release else .0055)
        shared._place(out,air,begin,sample_rate)
    # A small DC cleanup is shared by all new sources; timbre was rebuilt above.
    out=signal.sosfilt(signal.butter(2,70,'highpass',fs=sample_rate,output='sos'),out)
    out*=rng.uniform(.96,1.035)
    fade_in=max(2,round(.0012*sample_rate))
    fade_out=max(2,round(.018*sample_rate))
    out[:fade_in]*=np.linspace(0,1,fade_in)
    out[-fade_out:]*=np.linspace(1,0,fade_out)
    out*=min(1.,.64/max(1e-12,float(np.max(np.abs(out)))))
    if not np.all(np.isfinite(out)):
        raise FloatingPointError('Non-finite weighted physical source')
    return np.asarray(out,dtype=np.float64)
