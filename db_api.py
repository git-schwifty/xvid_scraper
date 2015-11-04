import sqlite3 as sql

from threading import Lock
from copy      import copy

import sys
import re


class Database:
    """SQLite backend for storing, retrieving, and viewing video information."""
    def __init__(self, med):
        self.med = med
        self.crs_lock = Lock()  # lock for using a SQL cursor
        self.cnx = sql.connect('xvid.db', check_same_thread=False)  # must enable multithreading
        self.c   = self.cnx.cursor()
        self.c.execute("""
          CREATE TABLE IF NOT EXISTS
          videos(url      STR   PRIMARY KEY,
                 title    STR,
                 duration INT,
                 raters   INT,
                 rating   FLOAT,
                 loved    INT,
                 views    INT);
          """)
        self.cnx.commit()
        self.c.execute("""CREATE TABLE IF NOT EXISTS
                          tags(url STR, tag STR)""")
        self.cnx.commit()
        # We'll want to define what is a valid character.
        self.regex = re.compile("[0-9a-zA-Z ]+")
        self.tags = []

    def save(self, data):
        # Remove invalid characters.
        for k, v in copy(zip(data.keys(), data.values())):
            if type(v) == str and k != "url":
                m = self.regex.match(v)
                if m:
                    data[k] = m.group()
                else:
                    data[k] = "invalid"
        try:
            with self.crs_lock:
                self.c.execute("""
                  INSERT INTO videos
                  VALUES ("{0}", "{1}", {2}, {3}, {4}, {5}, {6});
                  """.format(data["url"],
                             data["title"],
                             data["duration"],
                             data["raters"],
                             data["rating"],
                             data["loved"],
                             data["views"]))
                self.cnx.commit()

                for tag in data["tags"]:
                    self.c.execute("""INSERT INTO tags VALUES ("{0}", "{1}")
                                   """.format(data["url"], tag))
                    self.cnx.commit()

        except sqlite.IntegrityError:
            # UNIQUE constraint failed: videos.url
            self.med.feedback("Program attempted to add a video to \
                               the database that was already in there.")
            self.med.next_()

    def has_video(self, url):
        with self.crs_lock:
            self.c.execute("""
              SELECT title
              FROM   videos
              WHERE  url = '{0}';
            """.format(url))
        return any(self.c.fetchall())

    def vectorize_tags(self, feats_fn):
        """ Create a binary vector for each video representing
          the presence or absense of tags. """
        # TODO: make this less ugly

        with self.crs_lock:
            # Determine how many unique tags are in our database so we can
            # figure out how many tags to train on (read: reasonably common).
            self.c.execute("""
              SELECT COUNT(tag) FROM (SELECT DISTINCT tag FROM tags);
            """)
            take_top = feats_fn(self.c.fetchall()[0][0])
            sys.stdout.flush()

            # Grab the top _ most common tags from our database.
            self.c.execute("""
              SELECT tag, COUNT(tag) AS cnt FROM tags
              GROUP by tag
              ORDER BY cnt DESC
              LIMIT {0};
            """.format(take_top))
            top_tags = [tag[0] for tag in self.c.fetchall()]
            top_tags += ["duration", "raters", "rating", "views"]  # other info we want

            # We need to create a mapping of each tag to a position in our vector.
            tag_to_vec = {tag:i for tag, i in zip(top_tags, range(len(top_tags)))}

            # We use urls as the unique identifier for each video. Grab them.
            self.c.execute("""
              SELECT DISTINCT url FROM videos;
            """)
            urls = self.c.fetchall()
            urls = [u[0] for u in urls]

            # Now for each video, get a vector of tags and the user's opinion.
            all_vectors = []
            usr_ratings = []
            for url in urls:
                # Get all tags associated with this video.
                self.c.execute("""
                  SELECT tag FROM tags
                  WHERE url = '{0}';
                """.format(url))
                fetched = self.c.fetchall()
                this_vids_tags = [t[0] for t in fetched]

                # Now turn those tags into a vector of numbers.
                # Start by making an empty vector to fit all our tags plus
                # the duration, number of raters, average rating, and number
                # of views.
                tag_vector = np.zeros(take_top + 4)
                for tag in this_vids_tags:
                    if tag in tag_to_vec.keys():
                        position = tag_to_vec[tag]
                        tag_vector[position] = 1
                all_vectors.append(tag_vector)

                # Now we get non-tag data for our vector.
                self.c.execute("""
                  SELECT loved, duration, raters, rating, views
                  FROM videos WHERE url = '{0}';
                """.format(url))
                non_tag = self.c.fetchall()
                for loved, duration, raters, rating, views in non_tag:
                    usr_ratings.append(loved)
                    tag_vector[tag_to_vec["duration"]] = duration
                    tag_vector[tag_to_vec["raters"]]   = raters
                    tag_vector[tag_to_vec["rating"]]   = rating
                    tag_vector[tag_to_vec["views"]]    = views

        return all_vectors, usr_ratings, tag_to_vec

    def __del__(self):
        self.cnx.close()

