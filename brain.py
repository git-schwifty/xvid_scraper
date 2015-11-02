from sklearn.tree import DecisionTreeClassifier as DTC
from math import log
import numpy as np
import os
import pickle


class Brain:
    def __init__(self, mediator, min_rating=1):
        self.med = mediator
        self.min_rating = min_rating
        wdfs = os.listdir()
        if "brain.pkl" in wdfs and "brain_vec.pkl" in wdfs:
            with open("brain.pkl", "rb") as f:
                self.tree = pickle.load(f)
            f.close()

            with open("brain_vec.pkl", "rb") as f:
                self.tag_to_vec = pickle.load(f)
            f.close()

        else:
            self.tree = None
            self.tag_to_vec = None

    def train(self, tags, ratings, tag_to_vec):
        # if we want to predict the rating given a certain list of tags,
        # we'll need to be able to encode it the same way we did to get
        # the training data.
        self.tag_to_vec = tag_to_vec

        # Now get and train our model.
        tree = DTC(max_depth=round(log(len(ratings))))
        tree.fit(tags, ratings)
        self.tree = tree

        # Finally, save our model
        with open("brain.pkl", "wb") as f:
            pickle.dump(tree, f)
        f.close()
        # Also, let's save our tag_to_vec, too.
        with open("brain_vec.pkl", "wb") as f:
            pickle.dump(tag_to_vec, f)
        f.close()

    def predict(self, data):
        if self.tree and self.tag_to_vec:
            # First we need to turn our data into a vector.
            this_vec = np.zeros(len(self.tag_to_vec.keys()))
            for tag in data["tags"]:
                if tag in self.tag_to_vec.keys():
                    this_vec[self.tag_to_vec[tag]] = 1
            this_vec[self.tag_to_vec["duration"]] = data["duration"]
            this_vec[self.tag_to_vec["raters"]]   = data["raters"]
            this_vec[self.tag_to_vec["rating"]]   = data["rating"]
            this_vec[self.tag_to_vec["views"]]    = data["views"]

            # now predict what the user will rate this as.
            guess = self.tree.predict(this_vec)
            if guess > self.min_rating:
                return True
            else:
                return False

        else:
            return True
