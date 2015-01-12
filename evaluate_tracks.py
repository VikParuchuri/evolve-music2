import extract_features
from scipy.spatial.distance import cdist
import os
import settings


class TrackEvaluator(object):
    def __init__(self, track_eval=None):
        if track_eval is not None:
            self.train_data = track_eval.train_data

    def read_data(self):
        self.train_data = extract_features.generate_train_features()
        print("Done reading in data!")

    def evaluate_track(self, filepath):
        features = extract_features.generate_features(filepath)
        sel_feats = features.iloc[:-3].reshape(1, -1)
        sel_train = self.train_data.iloc[:, :-3]
        distance_vec = cdist(sel_train, sel_feats, "cosine").reshape(-1)
        return distance_vec

    def score_track(self, filepath):
        distance_vec = self.evaluate_track(filepath)
        return (distance_vec.mean() * 1000) + (distance_vec.min() * 1000)

    def score_tracks(self):
        scores = {}
        for fname in os.listdir(settings.GENERATED_OGG_PATH):
            fpath = os.path.join(settings.GENERATED_OGG_PATH, fname)
            scores[fname] = self.score_track(fpath)
        return scores
