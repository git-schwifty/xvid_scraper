"""
A program for viewing, rating, and getting recommendations for
pornographic videos through the website xvideos.com.
"""
#!/usr/bin/env python

from db_api    import Database
from scraper   import Scraper
from brain     import Brain
#from profile   import ProfileManager
from proj_ADTs import MyQueue
from threading import Thread, RLock

import webbrowser
import time
import pdb
import sys


# WARNING: as of right now, threading doesn't seem to play nice with
# tkinter, so any fancy threading stuff I did here is really just a
# placeholder for later when I ditch tkinter entirely.
class Mediator:
    def __init__(self, win):
        self.win  = win

        # Settings will go here.
        index_url  = "http://www.xvideos.com/c/{0}/anal-12"
        look_ahead = 80
        qmaxsize   = 25

        # State used by various objects.
        self.cur_vid_data = {}

        # Load up all the major elements of the program.
        self.scr  = Scraper(index_url=index_url, pg_n=0)
        self.db   = Database()
        self.ai   = Brain(self)
        self.q    = MyQueue(maxsize=qmaxsize)
        self.lock = RLock()

        # Scraping websites will be done as a background process.
        self.gather_process = Thread(target = self.gather,
                                     daemon = True)
        self.gather_process.start()

    def gather(self, look_ahead=4):
        """Background process that quietly fills up the video queue with urls."""
        while True:
            if self.q.not_full():
                # We'll implement this as a while loop so we can
                # ignore already seen videos.
                looked_at = 0
                while looked_at < look_ahead:
                    # Tell the scraper to set up the next
                    # video for further processing.
                    self.scr.next()
                    cur_vid = self.scr.cur_vid

                    if not self.db.has_video(cur_vid):
                        # Scrape the video page for data.
                        scraped_data = self.scr.scrape_video(cur_vid)

                        # Predict how much the user will like this video.
                        prediction = self.ai.predict(scraped_data)

                        # Save some extra data.
                        scraped_data["pic_url"] = self.scr.cur_pic
                        scraped_data["pred"]    = prediction
                        
                        # Put data into queue.
                        # Note that we put a negative sign in front of the predicton
                        # because a high rating corresponds to a large number, but for
                        # queues, a low number is considered a high priority.
                        self.lock.acquire()
                        self.q.put(scraped_data, -prediction)
                        self.lock.release()
                        looked_at += 1
            else:
                time.sleep(5)

    def next_(self):
        """Load up the next video in the queue."""
        # Wait until we have save data before going on to the next one.
        while self.q.empty():
            time.sleep(1)

        # Get our data out of the queue.
        self.lock.acquire()
        self.cur_vid_data = self.q.get()
        self.lock.release()

        # Refresh the window with new preview images.
        pic_url = self.cur_vid_data["pic_url"]
        self.win.update_images( *self.scr.load_pics(pic_url) )

        # Display a little data about the video.
        for data_point in ['title', 'duration', 'pred']:
            print("\t" + data_point, self.cur_vid_data[data_point])


    def save(self, rating):
        # I should change the name loved since the program evolved to
        # where there is no longer a binary yes/no for the rating.
        self.cur_vid_data["loved"] = rating
        self.db.save(self.cur_vid_data)
        self.next_()

    def open_vid(self):
        webbrowser.open(self.cur_vid_data["url"])

    def train(self):
        # We need to determine how many features to train on, but
        # we'll just pass in a formula that takes in as an argument
        # the number of unique tags in the database.
        n_feats = lambda n: n // 2
        all_vectors, usr_ratings, tag_to_vec = self.db.vectorize_tags(n_feats)
        self.ai.train(all_vectors, usr_ratings, tag_to_vec)

    def close(self):
        """When a window closes, disconnect from a database."""
        self.train()
        self.db.cnx.close()
        self.win.root.destroy()

if __name__ == "__main__":
    # Mediator gets called from inside window because
    # window has to be the main thread in order for it
    # to not throw up a ton of errors.
    win = Window()
