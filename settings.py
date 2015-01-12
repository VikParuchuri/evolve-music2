import os
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
MIDI_DIR = os.path.join(DATA_DIR, "midi")
OGG_DIR = os.path.join(DATA_DIR, "ogg")
SOURCE_MIDI_DIR = os.path.join(MIDI_DIR, "full")
GENERATED_MIDI_PATH = os.path.join(MIDI_DIR, "generated")
SOUNDFONT_PATH = os.path.join(DATA_DIR, "soundfont", "GS144.sf2")

SOURCE_JSON_DESCRIPTION = os.path.join(DATA_DIR, "full.json")
TEMP_DIR = os.path.join(DATA_DIR, "temp")
GENERATED_PATH = os.path.join(DATA_DIR, "generated")
GENERATED_OGG_PATH = os.path.join(GENERATED_PATH, "ogg")
GOOD_DIR = os.path.join(DATA_DIR, "good")
GOOD_MIDI_PATH = os.path.join(GOOD_DIR, "midi")

VALUE_ROUNDOFF = 5
TICK_ROUNDOFF = 10
MELODY_DECAY = 1

TRANSITION_MATRIX_START = 1
TRANSITION_MATRIX_END = 6

TRACK_LENGTH = 4000
BASE_HARMONY_LENGTH = 30

MUSIC_TIME_LIMIT = 10
TRAIN_FEATURE_PATH = os.path.join(GENERATED_PATH, "train_features.csv")