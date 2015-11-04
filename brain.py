from sklearn.tree         import DecisionTreeRegressor as Tree
from sklearn.svm          import SVR                   as SVMachine
from sklearn.linear_model import LogisticRegression    as LogReg
from sklearn.naive_bayes  import GaussianNB            as Bayes

from sklearn.cross_validation import train_test_split
from sklearn.metrics          import mean_squared_error as mse
from math import log

import numpy as np
import os
import pickle
import sys
import pdb


class Brain:
    def __init__(self, mediator, min_rating=1):
        self.med = mediator

        if "brain.pkl" in os.listdir() and "brain_vec.pkl" in os.listdir():
            with open("brain.pkl", "rb") as f:
                self.models, self.performance = pickle.load(f)
            f.close()

            with open("brain_vec.pkl", "rb") as f:
                self.tag_to_vec = pickle.load(f)
            f.close()

        else:
            self.models      = []
            self.performance = []
            self.tag_to_vec = None

    def train(self, tags, ratings, tag_to_vec):
        # if we want to predict the rating given a certain list of tags,
        # we'll need to be able to encode it the same way we did to get
        # the training data.
        print("training")
        sys.stdout.flush()

        # Make sure we were asked to train on data in
        # a situation in which that data exists.
        if not any(tag_to_vec.keys()):
            return None

        self.tag_to_vec = tag_to_vec

        # Split into testing and training sets.
        tr_data, te_data, tr_class, te_class = train_test_split(tags, ratings, test_size=0.20)

        # Now let's get a bunch of different models to try out.
        self.models = [Tree(), SVMachine(), LogReg(), Bayes()]
        self.model_names = ["Decision Tree",
                            "Support Vector Machine",
                            "LogisticRegression",
                            "Naive Bayes"]
        self.performances = []
        for model in self.models:
            model.fit(X=tr_data, y=tr_class)
            predicts = model.predict(te_data)
            score = mse(predicts, te_class)
            self.performances.append(float(np.mean(score)))

        print("Performance of models used to train predictive algorithm.")
        for name, score in zip(self.model_names, self.performances):
            print(str(name).ljust(20) + ":" + str(round(score, 2)))
            sys.stdout.flush()

        # Finally, save our models
        with open("brain.pkl", "wb") as f:
            pickle.dump([self.models, self.performance], f)
        f.close()

        # Also, let's save our tag_to_vec, too.
        with open("brain_vec.pkl", "wb") as f:
            pickle.dump(tag_to_vec, f)
        f.close()

    def predict(self, data):
        if self.models and self.performance:
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
            numerator = 0
            for model, weight in zip(self.models, self.performance):
                # A high weight is bad (we're using mean squared error),
                # so we divide by the weight (would you call that a de-
                # weighted average?).
                numerator += model.predict(this_vec) / weight
            
            # average and also make sure we're dealing with floats, not np.arrays
            return float(numerator) / float(sum(self.performance))

        else:
            return True
