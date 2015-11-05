##from sklearn.tree import DecisionTreeRegressor as Model
from sklearn.ensemble import AdaBoostClassifier as Model
from math import log

import numpy as np
import os
import pickle
import sys


class Brain:
    def __init__(self, mediator, min_rating=1):
        self.med = mediator
        self.model = []
        self.tag_to_vec = {}

        if ("brain.pkl" in os.listdir()) and ("brain_vec.pkl" in os.listdir()):
            with open("brain.pkl", "rb") as f:
                self.model = pickle.load(f)
            f.close()

            with open("brain_vec.pkl", "rb") as f:
                self.tag_to_vec = pickle.load(f)
            f.close()

    def train(self, data_vectors, classifications, tag_to_vec):
        # Make sure we were asked to train on data in
        # a situation in which that data exists.
        self.med.feedback("training")
        if not any(tag_to_vec.keys()):
            self.med.feedback("no data to train on")
            return None

        self.tag_to_vec = tag_to_vec

        # Other processes may use this while we're fitting and
        # I don't feel like setting up a lock for this right now,
        # so we only replace the current model once that's done.
        model = Model()
        model.fit(X=data_vectors, y=classifications)
        self.mode = model

        # Finally, save our models
        with open("brain.pkl", "wb") as f:
            pickle.dump(self.model, f)
        f.close()

        # Also, let's save our tag_to_vec, too.
        with open("brain_vec.pkl", "wb") as f:
            pickle.dump(tag_to_vec, f)
        f.close()

        self.med.feedback("training complete")

    def predict(self, data):
        if self.model:
            # First we need to turn our data into a vector.
            this_vec = np.zeros(len(self.tag_to_vec.keys()))
            for tag in data["tags"]:
                if tag in self.tag_to_vec.keys():
                    this_vec[self.tag_to_vec[tag]] = 1

            # Vectorize non-tag information, too.
            this_vec[self.tag_to_vec["duration"]] = data["duration"]
            this_vec[self.tag_to_vec["raters"]]   = data["raters"]
            this_vec[self.tag_to_vec["rating"]]   = data["rating"]
            this_vec[self.tag_to_vec["views"]]    = data["views"]

            # now predict what the user will rate this as.
            return self.model.predict(this_vec)[0]

        else:
            return 0
