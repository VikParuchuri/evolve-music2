import evaluate_tracks
import construct_tracks
import math
import convert_to_ogg
import os
import settings
import uuid
import shutil
import random
import midi
import sys
import logging
log = logging.getLogger(__name__)


def generate_tracks(track_generator, track_count=20):
    track_generator.create_pools(track_count * settings.POOL_MULTIPLIER)
    track_generator.generate_tracks(track_count)
    track_generator.write_patterns()
    generated_midi_to_ogg()


def generated_midi_to_ogg():
    for fname in os.listdir(settings.GENERATED_MIDI_PATH):
        if fname.endswith(".mid"):
            fpath = os.path.join(settings.GENERATED_MIDI_PATH, fname)
            convert_to_ogg.convert_to_ogg(fpath, settings.GENERATED_OGG_PATH)

def good_midi_to_ogg():
    for fname in os.listdir(settings.GOOD_MIDI_PATH):
        if fname.endswith(".mid"):
            fpath = os.path.join(settings.GOOD_MIDI_PATH, fname)
            convert_to_ogg.convert_to_ogg(fpath, settings.GOOD_OGG_PATH)

def remix(song1, song2):
    songs = [song1, song2]
    all_tracks = song1[1:] + song2[1:]
    track_len = len(song1) + len(song2) - 2
    tempo_track = random.randint(0, 1)
    tempo = songs[tempo_track][0]
    new_len = random.randint(1, track_len)
    tracks = []
    for i in xrange(0, new_len):
        choice = random.randint(0, len(all_tracks) - 1)
        tracks.append(all_tracks[choice])
        del all_tracks[choice]
        if len(all_tracks) == 0:
            break
    return midi.Pattern([tempo] + tracks)

def clear_dir_ext(path, ext):
    for f in os.listdir(path):
        if f.endswith(ext):
            os.remove(os.path.join(path, f))

def evolve_tracks(track_generator=None, track_evaluator=None, evolutions=3, track_count=30):
    if track_generator is None:
        track_generator = construct_tracks.TrackGenerator()
        track_generator.read_data()
    if track_evaluator is None:
        track_evaluator = evaluate_tracks.TrackEvaluator()
        track_evaluator.read_data()
    clear_dir_ext(settings.GENERATED_MIDI_PATH, ".mid")
    clear_dir_ext(settings.GENERATED_OGG_PATH, ".ogg")

    patterns_to_pick = int(math.floor(track_count / 4))
    remixes_to_make = int(math.floor(track_count / 4))
    generate_tracks(track_generator, track_count=track_count)
    mins = []
    for z in xrange(0, evolutions):
        scores = track_evaluator.score_tracks()

        # Move the best track out
        min_filename, min_score = min(scores.items(), key=lambda x: x[1])
        new_filename = "{0}.mid".format(str(uuid.uuid4()))
        min_filename = min_filename.replace(".ogg", ".mid")
        if min_score not in mins:
            mins.append(min_score)
            shutil.copyfile(os.path.join(settings.GENERATED_MIDI_PATH, min_filename),
                            os.path.join(settings.GOOD_MIDI_PATH, new_filename))
        log.info("Ev: {0} Min score: {1} Filename: {2}".format(z, min_score, new_filename))

        # Find the good tracks
        score_vec = [scores[k] for k in scores]
        score_vec = sorted(score_vec)[:patterns_to_pick]
        good_pattern_indexes = [int(k.replace(".ogg", "")) for k in scores if scores[k] in score_vec]
        patterns = [track_generator.pattern_pool[i] for i in good_pattern_indexes if i < len(track_generator.pattern_pool)]
        track_generator.create_pools(track_count * settings.POOL_MULTIPLIER)
        track_generator.generate_tracks(track_count - len(patterns))
        patterns += track_generator.pattern_pool

        for i in xrange(0, remixes_to_make):
            patterns.append(
                remix(random.choice(patterns[:patterns_to_pick]), random.choice(patterns[patterns_to_pick:])))
        track_generator.pattern_pool = patterns
        track_generator.write_patterns()
        generated_midi_to_ogg()
    return track_generator, track_evaluator


if __name__ == "__main__":
    logging.basicConfig(filename=settings.LOG_PATH, level=logging.DEBUG)
    args = sys.argv[1:]
    evolutions = 3
    track_count = 30
    if len(args) == 1:
        track_count = int(args[0])
    if len(args) == 2:
        track_count = int(args[0])
        evolutions = int(args[1])
    evolve_tracks(evolutions=evolutions, track_count=track_count)
    good_midi_to_ogg()