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
import note_phrases
import itertools

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

def find_match(note_mats, last_val, note_type="tick", max_val=None):
    inds = []
    for i in xrange(0, len(note_mats)):
        inds.append([int(i) for i in note_mats[i][note_type]["inds"]])
    for i in xrange(0, len(note_mats)):
        ind = inds[i].index(find_closest_element(last_val, inds[i]))
    t = 0
    multiplier = 1
    divisor = 1
    for i in xrange(0, len(note_mats)):
        mat = note_mats[i][note_type]["mat"]
        sind = pick_proba(mat[ind, :] / np.sum(mat[ind, :]))
        t += (inds[i][sind]) * multiplier
        divisor += multiplier
        multiplier /= settings.MELODY_DECAY

    t /= divisor
    t = find_closest_element(t, inds[0])
    if max_val is not None and t > max_val:
        t = max_val
    return t

def find_next_phrase(pitch, velocity, tick, instrument_phrases):
    diffs = []
    for phrase in instrument_phrases:
        diff = abs(pitch - phrase["pitch"][0]) + abs(velocity - phrase["velocity"][0]) + abs(tick - phrase["tick"][0])
        diffs.append(diff)
    ind = diffs.index(min(diffs))
    return instrument_phrases[ind]

def generate_note_sequence(instrument_phrases, note_mats, length, tick_max=160):
    next_phrase = random.choice(instrument_phrases)
    phrases = []
    sofar = 0
    while sofar < length:
        phrases.append(next_phrase)
        sofar += sum([next_phrase["tick"][i] for i in xrange(0,len(next_phrase["tick"])) if next_phrase["type"][i] == "on"])
        last_pitch = next_phrase["pitch"][-1]
        last_tick = next_phrase["tick"][-1]
        last_velocity = next_phrase["velocity"][-1]
        pitch = find_match(note_mats, last_pitch, note_type="pitch")
        velocity = find_match(note_mats, last_velocity, note_type="velocity")
        tick = find_match(note_mats, last_tick, note_type="tick")
        next_phrase = find_next_phrase(pitch, velocity, tick, instrument_phrases)

    return phrases

def generate_audio_track(data, note_phrases, length, instrument=None):
    notes = data[0]["note_matrix"]
    if instrument is None:
        valid_instruments = list(set(notes.keys()).intersection(note_phrases.keys()))
        instrument = random.choice(valid_instruments)
    note_mats = [d["note_matrix"][instrument] for d in data]
    if len(note_phrases[instrument]) == 0:
        return None
    phrases = generate_note_sequence(note_phrases[instrument], note_mats, length, tick_max=160)

    track = midi.Track()
    track.append(midi.TrackNameEvent())
    prog = midi.ProgramChangeEvent()
    prog.set_value(instrument)
    track.append(prog)
    for i in xrange(0, len(phrases)):
        for j in xrange(0, len(phrases[i]["tick"])):
            pitch = phrases[i]["pitch"][j]
            velocity = phrases[i]["velocity"][j]
            note_type = phrases[i]["type"][j]
            tick = phrases[i]["tick"][j]
            obj = midi.NoteOnEvent(channel=0)
            if note_type == "off":
                obj = midi.NoteOffEvent(channel=0)
            obj.set_pitch(pitch)
            obj.set_velocity(velocity)
            obj.tick = tick
            track.append(obj)
    track.append(midi.EndOfTrackEvent())
    return track


def generate_tempo_track(data, length, mpqn=20):
    track = midi.Track()
    track.append(midi.TrackNameEvent())
    track.append(midi.TextMetaEvent())
    te = midi.SetTempoEvent()
    te.tick = length
    te.set_mpqn(mpqn)
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

def next_instrument(chosen, all):
    for k in all:
        if k not in chosen:
            return k
    chosen_count = Counter(chosen)
    all_tuples = [(k,all[k]) for k in all]
    chosen_tuples = [(k, chosen[k]) for k in chosen_count]
    all_tuples = sorted(all_tuples, key=lambda tup: tup[1])
    chosen_tuples = sorted(chosen_tuples, key=lambda tup: tup[1])
    for i, t in enumerate(chosen_tuples):
        if t[0] != all_tuples[i][0]:
            return all_tuples[i][0]
    return all_tuples[0][0]

class TrackGenerator(object):
    def __init__(self, track_generator=None):
        if track_generator is not None:
            self.data = track_generator.data
            self.midi_data = track_generator.midi_data
            self.note_phrases = track_generator.note_phrases

    def read_data(self):
        self.data = generate_transition_matrices(settings.TRANSITION_MATRIX_START, settings.TRANSITION_MATRIX_END)
        self.midi_data = read_all_midis()
        self.note_phrases = note_phrases.generate_note_phrases()
        log.info("Done reading data")

    def create_pools(self, track_count=1):
        instrument_lists = [m["instruments"] for m in self.midi_data]
        all_instruments = Counter(list(itertools.chain.from_iterable(instrument_lists)))
        chosen_instruments = []
        track_pool = []
        for i in xrange(0, track_count):
            instrument = next_instrument(chosen_instruments, all_instruments)
            track = generate_audio_track(self.data, self.note_phrases, settings.TRACK_LENGTH, instrument=instrument)
            if track is not None:
                track_pool.append(track)
                chosen_instruments.append(instrument)

        tempo_pool = []
        for i in xrange(0, min(1, int(math.floor(track_count / 4)))):
            tempo_pool.append(generate_tempo_track(self.data, settings.TRACK_LENGTH, mpqn=random.choice(settings.TEMPO_CHOICES)))

        all_instruments = []
        for t in track_pool:
            for e in t:
                if isinstance(e, midi.events.ProgramChangeEvent):
                    all_instruments.append(e.data[0])
        all_instruments.sort()

        self.track_pool = track_pool
        self.tempo_pool = tempo_pool
        self.all_instruments = all_instruments
        log.info("Done creating pools")

    def generate_tracks(self, track_count=1):
        pattern_pool = []
        instrument_lists = [self.midi_data[i]["instruments"] for i in xrange(0,len(self.midi_data)) if len(self.midi_data[i]["instruments"]) > 0]
        for i in xrange(0, int(math.floor(track_count))):
            instruments = random.choice(instrument_lists)
            track_number = random.randint(1, min(5, len(instruments)))
            tempo_track = random.choice(self.tempo_pool)
            tracks = [tempo_track]
            for i in xrange(0, track_number):
                instrument = instruments[i]
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
        log.info("Done generating tracks")

    def write_patterns(self):
        for i, pattern in enumerate(self.pattern_pool):
            write_midi_to_file(pattern, "{0}.mid".format(i))
        log.info("Done writing patterns")

    def create_and_write(self, track_count=10):
        self.create_pools(track_count * settings.POOL_MULTIPLIER)
        self.generate_tracks(track_count)
        self.write_patterns()