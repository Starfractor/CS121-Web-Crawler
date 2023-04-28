from collections import defaultdict 
import scraper

class ScraperData:
    def __init__(self):
        self.visited = set()
        self.longestPageCount = -1
        self.longestPage = ""
        self.wordsCount = defaultdict(int)