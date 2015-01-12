import random
import numpy as np
import logging
import midi
import math
import os
import settings
from transition_matrix import generate_transition_matrices, read_all_midis
from collections import Counter
from copy import deepcopy

log = logging.getLogger(__name__)


def pick_proba(vec):
    randint = random.uniform(0, np.sum(vec))
    choice = None
    try:
        total = 0.0
        for i in xrange(0, len(vec)):
            total += vec[i]
            if total > randint:
                choice = i
                break
    except Exception:
        return 0
    if choice is None:
        choice = len(vec) - 1
    return choice


def find_closest_element(e, l):
    dists = [abs(i - e) for i in l]
    ind = dists.index(min(dists))
    return l[ind]


def generate_markov_seq(data, length, key="tempo_matrix", tick_key="tick"):
    inds = []
    for i in xrange(0, len(data)):
        inds.append([int(i) for i in data[i][key][tick_key]["inds"]])
    start = inds[0][pick_proba(np.divide(np.sum(data[0][key][tick_key]["mat"], axis=1), 1000000))]
    seq = [start]
    for j in xrange(1, length):
        try:
            val = 0
            multiplier = 1
            divisor = 1
            for i in xrange(0, len(data)):
                try:
                    tick_mat = data[i][key][tick_key]["mat"]
                    ind = inds[i].index(find_closest_element(seq[j - 1], inds[i]))
                    sind = pick_proba(tick_mat[ind, :] / np.sum(tick_mat[ind, :]))
                    val += (inds[i][sind]) * multiplier
                    divisor += multiplier
                    multiplier /= settings.MELODY_DECAY
                except Exception:
                    pass
            val /= divisor
            val = find_closest_element(val, inds[0])
            if val == seq[j - 1] and val == seq[j - 2]:
                val = find_closest_element(val - 40, inds[0])

            seq.append(val)

        except Exception:
            print("Failed markov sequence")
            seq.append(random.choice(inds))
    return seq


def generate_tick_seq(data, length, tick_max=4000, key="tempo_matrix"):
    inds = []
    for i in xrange(0, len(data)):
        inds.append([int(i) for i in data[i][key]["tick"]["inds"]])
    tick_max = int(find_closest_element(tick_max, inds[0]))
    start = inds[0][pick_proba(np.divide(np.sum(data[0][key]["tick"]["mat"], axis=1), 1000000))]
    log.info("Start {0}".format(start))
    if start > tick_max:
        start = tick_max
    seq = []
    seq.append(start)
    sofar = 0
    j = 1
    zeros_count = 0
    while sofar < length:
        t = 0
        multiplier = 1
        divisor = 1
        for i in xrange(0, len(data)):
            tick_mat = data[i][key]["tick"]["mat"]
            ind = inds[i].index(find_closest_element(seq[j - 1], inds[i]))
            sind = pick_proba(tick_mat[ind, :] / np.sum(tick_mat[ind, :]))
            t += (inds[i][sind]) * multiplier
            divisor += multiplier
            multiplier /= settings.MELODY_DECAY
        t /= divisor
        t = find_closest_element(t, inds[0])
        if t > tick_max:
            t = tick_max
        if zeros_count > 5:
            t = int(find_closest_element(100, inds[0]))
            if t == 0:
                t = 20
        if t == 0:
            zeros_count += 1
        else:
            zeros_count = 0
        seq.append(int(t))
        sofar += t
        j += 1

    if sofar > length:
        seq[-1] -= (sofar - length)
    return seq


def generate_audio_track(data, length, all_instruments=None):
    notes = data[0]["note_matrix"]
    if all_instruments is None:
        instrument = random.choice(notes.keys())
    else:
        ai = [a for a in all_instruments if a < 42 and a > 55]
        if len(ai) == 0:
            instrument = random.choice(all_instruments)
        else:
            instrument = random.choice(ai)
    note_mats = [{"note_matrix": d["note_matrix"][instrument]} for d in data]
    tick = generate_tick_seq(note_mats, length, tick_max=160, key="note_matrix")
    tick_length = len(tick)
    pitch = generate_markov_seq(note_mats, tick_length, key="note_matrix", tick_key="pitch")
    velocity = generate_markov_seq(note_mats, tick_length, key="note_matrix", tick_key="velocity")
    for i in xrange(0, len(velocity)):
        if velocity[i] > 100:
            velocity[i] = 100

    track = midi.Track()
    track.append(midi.TrackNameEvent())
    prog = midi.ProgramChangeEvent()
    prog.set_value(instrument)
    track.append(prog)
    notes = []
    for i in xrange(0, min(tick_length, settings.BASE_HARMONY_LENGTH)):
        on = midi.NoteOnEvent(channel=0)
        on.set_pitch(pitch[i])
        on.set_velocity(velocity[i])
        on.tick = tick[i]
        notes.append(on)
        off = midi.NoteOffEvent(channel=0)
        off.set_pitch(pitch[i])
        off.set_velocity(velocity[i])
        off.tick = tick[i]
        notes.append(off)
    total_length = 0
    for i in xrange(0, tick_length):
        ind = i % len(notes)
        track.append(notes[ind])
        if isinstance(notes[ind], midi.NoteOnEvent):
            total_length += notes[ind].tick
        if total_length > length:
            break
    track.append(midi.EndOfTrackEvent())
    return track


def generate_tempo_track(data, length):
    tick = generate_tick_seq(data, length, key="tempo_matrix")
    length = len(tick)
    mpqn = generate_markov_seq(data, length, key="tempo_matrix", tick_key="mpqn")

    track = midi.Track()
    track.append(midi.TrackNameEvent())
    track.append(midi.TextMetaEvent())
    for i in xrange(0, length):
        if mpqn[i] != 0:
            te = midi.SetTempoEvent()
            te.tick = tick[i]
            te.set_mpqn(mpqn[i])
            track.append(te)
    track.append(midi.EndOfTrackEvent())
    return track


def find_similar_instrument(instruments, midi_data):
    all_instruments = []
    for m in midi_data:
        score = 0
        for i in instruments:
            if i in m["instruments"]:
                score += 1
        for i in xrange(0, score):
            for instrument in m["instruments"]:
                times = random.randint(0, 5)
                all_instruments += [instrument] * times
    if len(all_instruments) == 0:
        for m in midi_data:
            for instrument in m["instruments"]:
                times = random.randint(0, 5)
                all_instruments += [instrument] * times
    c = Counter(all_instruments)
    most_common = None
    for i in xrange(0, len(c)):
        index = random.randint(0, len(c) - 1)
        most_common, num_most_common = c.most_common(index + 1)[index]
        if most_common not in instruments and most_common >= 55 and most_common <= 42:
            break
    return most_common


def maximize_distance(existing, possible):
    try:
        instrument = None
        counter = 0
        max_dist = 0
        while counter < 100 and ((instrument == None or max_dist <= 8) or (instrument >= 42 and instrument <= 55)):
            counter += 1
            instrument = random.choice(possible)
            max_dist = min([abs(instrument - e) for e in existing])
    except ValueError:
        return 10, random.choice(range(len(possible)))

    if instrument is None:
        return 0, 1

    return max_dist, instrument


def generate_track(tracks):
    pat = midi.Pattern(tracks=tracks)
    return pat


def write_midi_to_file(pattern, name="tmp.mid"):
    midi_path = os.path.abspath(os.path.join(settings.GENERATED_MIDI_PATH, name))
    midi.write_midifile(midi_path, pattern)
    return midi_path


class TrackGenerator(object):
    def __init__(self, track_generator=None):
        if track_generator is not None:
            self.data = track_generator.data
            self.midi_data = track_generator.midi_data

    def read_data(self):
        self.data = generate_transition_matrices(settings.TRANSITION_MATRIX_START, settings.TRANSITION_MATRIX_END)
        self.midi_data = read_all_midis()
        print("Done reading data")

    def create_pools(self, track_count=1):
        track_pool = []
        for i in xrange(0, track_count):
            log.info("On track {0}".format(i))
            track_pool.append(generate_audio_track(self.data, settings.TRACK_LENGTH))

        tempo_pool = []
        for i in xrange(0, min(1, int(math.floor(track_count / 4)))):
            log.info("On tempo {0}".format(i))
            tempo_pool.append(generate_tempo_track(self.data, settings.TRACK_LENGTH))

        all_instruments = []
        for t in track_pool:
            for e in t:
                if isinstance(e, midi.events.ProgramChangeEvent):
                    all_instruments.append(e.data[0])
        all_instruments.sort()

        self.track_pool = track_pool
        self.tempo_pool = tempo_pool
        self.all_instruments = all_instruments
        print("Done creating pools")

    def generate_tracks(self, track_count=1):
        pattern_pool = []
        for i in xrange(0, int(math.floor(track_count))):
            log.info("On track {0}".format(i))
            track_number = random.randint(2, 5)
            tempo_track = random.choice(self.tempo_pool)
            tracks = [tempo_track]
            instruments = []
            for i in xrange(0, track_number):
                instrument = find_similar_instrument(instruments, self.midi_data)
                sel_track_pool = []
                for t in self.track_pool:
                    for e in t:
                        if isinstance(e, midi.events.ProgramChangeEvent) and e.data[0] == instrument:
                            sel_track_pool.append(t)
                            break
                if len(sel_track_pool) == 0:
                    sel_track_pool = self.track_pool
                sel_track = random.choice(sel_track_pool)
                for e in sel_track:
                    try:
                        e.channel = i + 1
                    except Exception:
                        pass
                tracks.append(sel_track)
                instruments.append(instrument)
            pattern_pool.append(generate_track(tracks))

        self.pattern_pool = pattern_pool
        print("Done generating tracks")

    def write_patterns(self):
        for i, pattern in enumerate(self.pattern_pool):
            write_midi_to_file(pattern, "{0}.mid".format(i))
        print("Done writing patterns")