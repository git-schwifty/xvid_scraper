import sqlite3 as sql
import re
from copy import copy


class Database:
    """SQLite backend for storing, retrieving, and viewing video information."""
    def __init__(self):
        self.cnx = sql.connect('xvid.db')
        self.c   = self.cnx.cursor()
        self.c.execute("""CREATE TABLE IF NOT EXISTS
                          videos(url      STR   PRIMARY KEY,
                                 title    STR,
                                 duration INT,
                                 raters   INT,
                                 rating   FLOAT,
                                 loved    INT,
                                 views    INT);""")
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

        self.c.execute("""INSERT INTO videos
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
            self.c.execute("""INSERT INTO tags
                              VALUES ("{0}", "{1}")""".format(
                                  data["url"],
                                  tag))
            self.cnx.commit()

    def has_video(self, url):
        self.c.execute("""SELECT title
                          FROM   videos
                          WHERE  url = '{0}';
                       """.format(url))
        return any(self.c.fetchall())

    def vectorize_tags(self):
        """ Create a binary vector for each video representing
          the presence or absense of tags. """
        # TODO: make this less ugly
        if not self.tags:
            # First, grab the top 100 common tags from our database.
            self.c.execute("""
              SELECT tag, COUNT(tag) AS cnt FROM tags
              GROUP by tag
              ORDER BY cnt DESC
              LIMIT 100;
            """)
            self.tags = [tag[0] for tag in self.c.fetchall()]

        # Get the corresponding tags to all the titles.
        all_vectors = []
        usr_ratings = []
        self.c.execute("""
          SELECT DISTINCT url FROM videos;
        """)
        urls = self.c.fetchall()
        urls = [u[0] for u in urls]
        for url in urls:
            self.c.execute("""
              SELECT tag FROM tags
              WHERE url = '{0}';
            """.format(url))
            cur_tags = [t[0] for t in self.c.fetchall()]
            all_vectors.append([master_tag in cur_tags for master_tag in self.tags])
            # Now we have to get what the user thinks of that particular movie.
            self.c.execute("""
              SELECT loved FROM videos WHERE url = '{0}';
            """.format(url))
            usr_ratings.append(self.c.fetchall()[0][0])

        return list(zip(all_vectors, usr_ratings))

    def __del__(self):
        self.cnx.close()

