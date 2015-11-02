"""
A program for viewing, rating, and getting recommendations for
pornographic videos through the website xvideos.com.
"""
#!/usr/bin/env python

import webbrowser
import sys
import os

from gui     import Window
from db_api  import Database
from scraper import Scraper
from brain   import Brain
from queue   import PriorityQueue

from threading import Thread, RLock

class Mediator:
    """Handles communication between objects."""
    def __init__(self, look_ahead=4, skip_to_page=0, feats=10, max_q_sz=100,
                 base_url="http://www.xvideos.com/c/{0}/anal-12"):
        # Let's set this up so gathering new videos can happen in the background.
        self.scraped_videos = {}
        gather_args = (look_ahead, skip_to_page, feats, max_q_sz)
        self.gather_process = Thread(target = self.gather,
                                     args   = gather_args,
                                     daemon = True)

        self.scr = Scraper(base_url=base_url, pg_n=skip_to_page)
        self.db  = Database()
        self.ai  = Brain(self)
        self.win = Window(self)

        self.currently_loaded_video_data = {}
        self.feats = feats

        self.q = PriorityQueue(maxsize=max_q_sz)
        self.lock = RLock()

        if "brain.pkl" in os.listdir():
            self.train()
        self.get_next()

    def start_gathering(self):
        self.gather_process.start()

    def get_next(self):
        """Determine which video should be selected, then update window."""
        # Get the video likely to have the best rating
        if self.q.qsize():
            self.lock.acquire()
            to_show_url = self.q.get()
            self.lock.release()
            scraped_data, preview_pic_url, guessed_rating = self.scraped_videos[to_show_url]
            self.currently_loaded_video_data = scraped_data
            pic1, pic2, pic3 = self.scr.load_pics(preview_pic_url) 
            self.win.update_images(pic1, pic2, pic3)
            url = scraped_data["url"]
            print("\n")
            print("\ttitle:\t", scraped_data["title"])
            print("\tlength:\t", scraped_data["duration"])
            print("\tguessed rating:\t", guessed_rating)
            print("\ttags:\t", "  ".join(scraped_data["tags"]))
            print()
        else:
            print("Error: still gathering videos.")

    def gather(self, look_ahead, skip_to_page, feats, max_q_sz):
        """ Add videos to the priority queue independently
          of rating and loading videos. """
        while True:
            if self.q.qsize() < max_q_sz:
                for i in range(look_ahead):
                    self.scr.next()
                    if self.db.has_video(self.scr.cur_vid):
                        # make sure we only work on unrated videos
                        print(".", end="")
                        continue
                    scraped_data = self.scr.scrape_video()
                    pred_rating  = self.ai.predict(scraped_data)
                    self.scraped_videos[self.scr.cur_vid] = (scraped_data,
                                                            self.scr.cur_pic,
                                                            pred_rating)
                    self.lock.acquire()
                    self.q.put(self.scr.cur_vid, -pred_rating)
                    self.lock.release()
                    print(":", end="")

    def save(self, rating):
        """Save the data scraped from the current video then get next video."""
        self.currently_loaded_video_data["loved"] = rating
        sys.stdout.flush()
        self.db.save(self.currently_loaded_video_data)
        self.get_next()
        
    def open_vid(self):
        webbrowser.open(self.scr.cur_vid)

    def train(self):
        tags, ratings, tag_to_vec = self.db.vectorize_tags(self.feats)
        self.ai.train(tags, ratings, tag_to_vec)

    def close_db(self):
        """When a window closes, disconnect from a database."""
        self.db.cnx.close()

if __name__ == "__main__":
    med = Mediator()
