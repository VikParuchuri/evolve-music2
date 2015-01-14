import os
import settings
import subprocess


def convert_to_ogg(mfile, ogg_path=settings.OGG_DIR):
    file_end = mfile.split("/")[-1].split(".")[0]
    oggfile = file_end + ".ogg"
    oggpath = os.path.abspath(os.path.join(ogg_path, oggfile))
    wavpath = os.path.abspath(os.path.join(settings.TEMP_DIR, "temp.wav"))
    rawpath = os.path.abspath(os.path.join(settings.TEMP_DIR, "temp"))
    subprocess.call(
        ['fluidsynth', '-i', '-n', '-F', rawpath, "-r 44100", settings.SOUNDFONT_PATH, mfile],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    subprocess.call(
        ["sox", "-t", "raw", "-r", "44100", "-b", "16", "-c", "1", "-e", "signed", "--norm", rawpath, wavpath],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    subprocess.call(
        ['oggenc', "-Q", "-o", oggpath, wavpath],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    os.remove(wavpath)
    os.remove(rawpath)


def convert_all_to_ogg():
    for f in os.listdir(settings.SOURCE_MIDI_DIR):
        if f.endswith(".mid"):
            convert_to_ogg(os.path.join(settings.SOURCE_MIDI_DIR, f))