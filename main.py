"""
A program for viewing, rating, and getting recommendations for
pornographic videos through the website xvideos.com.
"""
#!/usr/bin/env python

import webbrowser
import queue
import sys

from gui     import Window
from db_api  import Database
from scraper import Scraper
from brain   import Brain


class Mediator:
    """Handles communication between objects."""
    def __init__(self, look_ahead=4, skip_to_page=1, feats=500, max_q_sz=100,
                 base_url="http://www.xvideos.com/new/{0}/"):
        self.look_ahead = look_ahead
        self.features_to_train_on = feats
        self.q = queue.PriorityQueue(maxsize=max_q_sz)
        self.max_rating = 5

        self.currently_loaded_video_data = {}
        self.viewed_videos = {}

        self.scr = Scraper(base_url=base_url, pg_n=skip_to_page)
        self.db  = Database()
        self.ai  = Brain(self)
        self.win = Window(self)

        self.train()
        self.get_next()

    def get_next(self):
        """Determine which video should be selected, then update window."""
        # Throw two videos into our priority queue
        vids_added = 0
        while vids_added < self.look_ahead:
            self.scr.next()
            if self.db.has_video(self.scr.cur_vid):
                print(".", end="")
                sys.stdout.flush()
                continue
            else:
                print("!", end="")
                sys.stdout.flush()
                scraped = self.scr.scrape_video()
                # We want to be able to get the scraped data
                # and preview pics by video url.
                self.viewed_videos[self.scr.cur_vid] = (scraped, self.scr.cur_pic)
                guessed_rating = self.ai.predict(scraped)
                # priority queue takes out low numbers first.
                guess_rating = self.max_rating - guessed_rating
                self.q.put(self.scr.cur_vid, guessed_rating)
                vids_added += 1
            # Get the video likely to have the best rating
            to_show_url = self.q.get()
            scraped_data, preview_pic_url = self.viewed_videos[to_show_url]
            self.currently_loaded_video_data = scraped_data
            pic1, pic2, pic3 = self.scr.load_pics(preview_pic_url) 
            self.win.update_images(pic1, pic2, pic3)
        print()
        print("\ttitle:\t", self.currently_loaded_video_data["title"])
        print("\tlength:\t", self.currently_loaded_video_data["duration"])
        print("\ttags:\t", "  ".join(self.currently_loaded_video_data["tags"]))
        print()
        self.train()

    def save(self, rating):
        """Save the data scraped from the current video then get next video."""
        self.currently_loaded_video_data["loved"] = rating
        self.db.save(self.currently_loaded_video_data)
        self.get_next()
        
    def open_vid(self):
        webbrowser.open(self.scr.cur_vid)

    def train(self):
        tags, ratings, tag_to_vec = self.db.vectorize_tags(self.features_to_train_on)
        self.ai.train(tags, ratings, tag_to_vec)

    def close_db(self):
        """When a window closes, disconnect from a database."""
        self.db.cnx.close()

if __name__ == "__main__":
    med = Mediator()
