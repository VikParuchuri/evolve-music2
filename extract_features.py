import pandas as pd
import logging
import settings
import os
from scikits.audiolab import oggwrite, play, oggread
from scipy.fftpack import dct
from itertools import chain
import numpy as np
import math

log = logging.getLogger(__name__)


def read_sound(fpath, limit=settings.MUSIC_TIME_LIMIT):
    try:
        data, fs, enc = oggread(fpath)
        upto = fs * limit
    except IOError:
        log.error("Could not read file at {0}".format(fpath))
        raise IOError
    if data.shape[0] < upto:
        log.error("Music file at {0} not long enough.".format(fpath))
        raise ValueError
    try:
        if len(data.shape) == 1 or data.shape[1] != 2:
            data = np.vstack([data, data]).T
    except Exception:
        log.error("Invalid dimension count for file at {0}. Do you have left and right channel audio?".format(fpath))
        raise ValueError
    data = data[0:upto, :]
    return data, fs, enc


def calc_slope(x, y):
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    x_dev = np.sum(np.abs(np.subtract(x, x_mean)))
    y_dev = np.sum(np.abs(np.subtract(y, y_mean)))

    slope = (x_dev * y_dev) / (x_dev * x_dev)
    return slope


def get_indicators(vec):
    mean = np.mean(vec)
    slope = calc_slope(np.arange(len(vec)), vec)
    std = np.std(vec)
    return mean, slope, std


def calc_u(vec):
    fft = np.fft.fft(vec)
    return np.sum(np.multiply(fft, vec)) / np.sum(vec)


def calc_mfcc(fft):
    ps = np.abs(fft) ** 2
    fs = np.dot(ps, mel_filter(ps.shape[0]))
    ls = np.log(fs)
    ds = dct(ls, type=2)
    return ds


def mel_filter(blockSize):
    numBands = 13
    maxMel = int(freqToMel(24000))
    minMel = int(freqToMel(10))

    filterMatrix = np.zeros((numBands, blockSize))

    melRange = np.array(xrange(numBands + 2))

    melCenterFilters = melRange * (maxMel - minMel) / (numBands + 1) + minMel

    aux = np.log(1 + 1000.0 / 700.0) / 1000.0
    aux = (np.exp(melCenterFilters * aux) - 1) / 22050
    aux = 0.5 + 700 * blockSize * aux
    aux = np.floor(aux)  # Arredonda pra baixo
    centerIndex = np.array(aux, int)  # Get int values

    for i in xrange(numBands):
        start, center, end = centerIndex[i:(i + 3)]
        k1 = np.float32(center - start)
        k2 = np.float32(end - center)
        up = (np.array(xrange(start, center)) - start) / k1
        down = (end - np.array(xrange(center, end))) / k2

        filterMatrix[i][start:center] = up
        try:
            filterMatrix[i][center:end] = down
        except ValueError:
            pass

    return filterMatrix.transpose()


def freqToMel(freq):
    return 1127.01048 * math.log(1 + freq / 700.0)


def melToFreq(freq):
    return 700 * (math.exp(freq / 1127.01048 - 1))


def calc_features(vec, freq):
    # bin count
    bc = settings.MUSIC_TIME_LIMIT
    bincount = list(range(bc))
    # framesize
    fsize = 512
    #mean
    m = np.mean(vec)
    #spectral flux
    sf = np.mean(vec - np.roll(vec, fsize))
    mx = np.max(vec)
    mi = np.min(vec)
    sdev = np.std(vec)
    binwidth = len(vec) / bc
    bins = []

    for i in xrange(0, bc):
        bins.append(vec[(i * binwidth):(binwidth * i + binwidth)])
    peaks = [np.max(i) for i in bins]
    mins = [np.min(i) for i in bins]
    amin, smin, stmin = get_indicators(mins)
    apeak, speak, stpeak = get_indicators(peaks)
    #fft = np.fft.fft(vec)
    bin_fft = []
    for i in xrange(0, bc):
        bin_fft.append(np.fft.fft(vec[(i * binwidth):(binwidth * i + binwidth)]))

    mel = [list(calc_mfcc(j)) for (i, j) in enumerate(bin_fft) if i % 3 == 0]
    mels = list(chain.from_iterable(mel))

    cepstrums = [np.fft.ifft(np.log(np.abs(i))) for i in bin_fft]
    inter = [get_indicators(i) for i in cepstrums]
    acep, scep, stcep = get_indicators([i[0] for i in inter])
    aacep, sscep, stsscep = get_indicators([i[1] for i in inter])

    zero_crossings = np.where(np.diff(np.sign(vec)))[0]
    zcc = len(zero_crossings)
    zccn = zcc / freq

    u = [calc_u(i) for i in bins]
    spread = np.sqrt(u[-1] - u[0] ** 2)
    skewness = (u[0] ** 3 - 3 * u[0] * u[5] + u[-1]) / spread ** 3

    #Spectral slope
    #ss = calc_slope(np.arange(len(fft)),fft)
    avss = [calc_slope(np.arange(len(i)), i) for i in bin_fft]
    savss = calc_slope(bincount, avss)
    mavss = np.mean(avss)

    features = [m, sf, mx, mi, sdev, amin, smin, stmin, apeak, speak, stpeak, acep, scep, stcep, aacep, sscep, stsscep,
                zcc, zccn, spread, skewness, savss, mavss] + mels + [i[0] for (j, i) in enumerate(inter) if j % 5 == 0]

    for i in xrange(0, len(features)):
        try:
            features[i] = features[i].real
        except Exception:
            pass
    return features


def extract_features(sample, freq):
    left = calc_features(sample[:, 0], freq)
    right = calc_features(sample[:, 1], freq)
    return left + right


def process_song(vec, f):
    try:
        features = extract_features(vec, f)
    except Exception:
        log.error("Cannot generate features for file {0}".format(f))
        return None

    return features


def generate_features(filepath):
    frame = None
    data, fs, enc = read_sound(filepath)
    features = process_song(data, fs)
    frame = pd.Series(features)
    frame['fs'] = fs
    frame['enc'] = enc
    frame['fname'] = filepath
    return frame


def generate_train_features():
    if not os.path.isfile(settings.TRAIN_FEATURE_PATH):
        d = []
        encs = []
        fss = []
        fnames = []
        for i, p in enumerate(os.listdir(settings.OGG_DIR)):
            if not p.endswith(".ogg"):
                continue
            log.debug("On file {0}".format(p))
            filepath = os.path.join(settings.OGG_DIR, p)
            try:
                data, fs, enc = read_sound(filepath)
            except Exception:
                continue
            try:
                features = process_song(data, fs)
            except Exception:
                log.error("Could not get features for file {0}".format(p))
                continue
            d.append(features)
            fss.append(fs)
            encs.append(enc)
            fnames.append(p)
        frame = pd.DataFrame(d)
        frame['fs'] = fss
        frame['enc'] = encs
        frame['fname'] = fnames
        frame.to_csv(settings.TRAIN_FEATURE_PATH)
    else:
        frame = pd.read_csv(settings.TRAIN_FEATURE_PATH)
        frame = frame.iloc[:, 1:]
    return frame