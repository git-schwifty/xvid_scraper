"""
A program for viewing, rating, and getting recommendations for
pornographic videos through the website xvideos.com.
"""
#!/usr/bin/env python

import webbrowser

from gui     import Window
from db_api  import Database
from scraper import Scraper
from brain   import Brain


class Mediator:
    """Handles communication between objects."""
    def __init__(self):
        self.data = {}

        self.scr = Scraper(base_url="http://www.xvideos.com/new/{0}/", pg_n=1)
        self.db  = Database()
        self.ai  = Brain(self)
        self.win = Window(self)

        self.get_next()

    def get_next(self):
        """Determine which video should be selected, then update window."""
        while True:
            print("evaluating video")
            self.scr.next()
            if self.db.has_video(self.scr.cur_vid):
                print("video already rated, moving on")
                continue
            self.data = self.scr.scrape_video()
            if self.ai.predict(self.data):
                pic1, pic2, pic3 = self.scr.load_pics() 
                self.win.update_images(pic1, pic2, pic3)
                break
            else:
                print("video rejected")

    def save(self, rating):
        """Save the data scraped from the current video then get next video."""
        self.data["loved"] = rating
        self.db.save(self.data)
        self.get_next()
        
    def open_vid(self):
        webbrowser.open(self.scr.cur_vid)

    def train(self):
        print("getting top tags")
        tags, ratings, tag_to_vec = self.db.vectorize_tags()
        print("training on tags.")
        self.ai.train(tags, ratings, tag_to_vec)
        print("finished training")

    def close_db(self):
        """When a window closes, disconnect from a database."""
        self.db.cnx.close()

if __name__ == "__main__":
    med = Mediator()
