import os
import midi
import settings

def generate_note_phrase(filepath, data=None):
    if data is None:
        data = {}
    m = midi.read_midifile(filepath)

    instruments = []
    for track in m:
        instrument = None
        track_pitch = []
        track_velocity = []
        track_tick = []
        track_types = []
        for e in track:
            if isinstance(e, midi.events.ProgramChangeEvent):
                instrument = e.data[0]
                instruments.append(instrument)
            if isinstance(e, midi.events.NoteOnEvent) or isinstance(e, midi.events.NoteOffEvent):
                if instrument is not None:
                    pitch, velocity = e.data
                    tick = e.tick
                    if instrument not in data:
                        data[instrument] = []
                    track_pitch.append(pitch)
                    track_velocity.append(velocity)
                    track_tick.append(tick)
                    track_type = "on"
                    if isinstance(e, midi.events.NoteOffEvent):
                        track_type = "off"
                    track_types.append(track_type)
        for i in xrange(0,len(track_tick), settings.NOTE_STEP * 2):
            phrase_end = i + settings.NOTE_STEP * 2
            data[instrument].append({
                "pitch": track_pitch[i:phrase_end],
                "velocity": track_pitch[i:phrase_end],
                "tick": track_pitch[i:phrase_end],
                "type": track_types[i:phrase_end]
            })
    return data

def generate_note_phrases():
    data = {}
    for i, f in enumerate(os.listdir(settings.SOURCE_MIDI_DIR)):
        if f.endswith(".mid"):
            generate_note_phrase(os.path.join(settings.SOURCE_MIDI_DIR, f), data)
    return data
