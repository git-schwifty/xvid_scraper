from sklearn.svm import SVR as SupportVectorMachine
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
        # After testing out a couple of different plausible models,
        # SVM came out on top with Decision Trees coming out second.
        # Models that assume independence of variable didn't do too
        # well. The following data is typical of the sorts of results
        # I'd get:
        #
        # Predictive Model        Mean Squared Error
        # Decision Tree           0.65
        # Support Vector Machine  5.7
        # Logistic Regression     0.8
        # Naive Bayes             1.4

        # Make sure we were asked to train on data in
        # a situation in which that data exists.
        if not any(tag_to_vec.keys()):
            return None

        self.tag_to_vec = tag_to_vec

        self.model = SupportVectorMachine()
        self.model.fit(X=data_vectors, y=classifications)

        # Finally, save our models
        with open("brain.pkl", "wb") as f:
            pickle.dump(self.model, f)
        f.close()

        # Also, let's save our tag_to_vec, too.
        with open("brain_vec.pkl", "wb") as f:
            pickle.dump(tag_to_vec, f)
        f.close()

    def predict(self, data):
        sys.stdout.flush()
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
            raise RuntimeError("This isn't supposed to happen.")
