import midi
import logging
import os
import settings
import numpy as np
import pandas as pd
from itertools import chain
import pickle

log = logging.getLogger(__name__)


def process_midifile(m, notes=None, tempos=None):
    if notes is None:
        notes = {}

    if tempos is None:
        tempos = {'tick': [], 'mpqn': []}

    instruments = []
    for track in m:
        instrument = None
        for e in track:
            if isinstance(e, midi.events.ProgramChangeEvent):
                instrument = e.data[0]
                instruments.append(instrument)
            if isinstance(e, midi.events.NoteOnEvent) and instrument is not None:
                pitch, velocity = e.data
                tick = e.tick
                if instrument not in notes:
                    notes[instrument] = {'pitch': [], 'velocity': [], 'tick': []}
                notes[instrument]['pitch'].append(pitch)
                notes[instrument]['velocity'].append(velocity)
                notes[instrument]['tick'].append(tick)
            elif isinstance(e, midi.events.SetTempoEvent):
                tick = e.tick
                tick = round(tick / settings.TICK_ROUNDOFF) * settings.TICK_ROUNDOFF
                mpqn = e.mpqn
                tempos['tick'].append(tick)
                tempos['mpqn'].append(mpqn)
        tempos['mpqn'].append(0)
        tempos['tick'].append(0)
    return notes, tempos, instruments


def generate_matrix(seq, offset=1):
    seq = [round(i / settings.VALUE_ROUNDOFF) * settings.VALUE_ROUNDOFF for i in seq]
    unique_seq = list(set(seq))
    unique_seq.sort()
    mat = np.zeros((len(unique_seq), len(unique_seq)))
    for i in xrange(0, len(seq) - offset):
        i_ind = unique_seq.index(seq[i])
        i_1_ind = unique_seq.index(seq[i + offset])
        mat[i_ind, i_1_ind] += 1
    return {'mat': mat, 'inds': unique_seq}


def generate_matrices(notes, tempos, offset=1):
    tm = {}
    nm = {}
    tm['tick'] = generate_matrix(tempos['tick'])
    tm['mpqn'] = generate_matrix(tempos['mpqn'])

    for instrument in notes:
        nm[instrument] = {}
        for sk in notes[instrument]:
            nm[instrument][sk] = generate_matrix(notes[instrument][sk], offset)
    return nm, tm

def generate_transition_matrix(offset=1):
    tempos = {'tick': [], 'mpqn': []}
    notes = {}
    all_instruments = []
    for i, f in enumerate(os.listdir(settings.SOURCE_MIDI_DIR)):
        if not f.endswith(".mid"):
            continue
        try:
            m = midi.read_midifile(os.path.join(settings.SOURCE_MIDI_DIR, f))
        except Exception:
            continue
        try:
            notes, tempos, instruments = process_midifile(m, notes, tempos)
            all_instruments.append(instruments)
        except Exception:
            log.error("Could not get features for file {0}".format(f))
            continue
    note_matrix, tempo_matrix = generate_matrices(notes, tempos, offset)

    data = {'note_matrix': note_matrix, 'tempo_matrix': tempo_matrix,
            'instruments': list(chain.from_iterable(all_instruments))}

    return data

def read_single_midi(f):
    try:
        m = midi.read_midifile(f)
    except Exception:
        return None
    notes, tempos, instruments = process_midifile(m)
    return {
        "notes": notes,
        "tempos": tempos,
        "instruments": instruments
    }

def read_all_midis():
    data = []
    for i, f in enumerate(os.listdir(settings.SOURCE_MIDI_DIR)):
        if f.endswith(".mid"):
            data.append(read_single_midi(os.path.join(settings.SOURCE_MIDI_DIR, f)))
    return data

def generate_transition_matrices(start, end):
    data = []
    for offset in xrange(start, end):
        data.append(generate_transition_matrix(offset))
    return data