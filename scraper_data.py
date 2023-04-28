from collections import defaultdict, Counter
import scraper

class ScraperData:
    def __init__(self):
        self.visited = set()
        self.stats = defaultdict(int)
        self.longest_page = ("", 0)
        self.word_counts = Counter()
        self.subdomains = defaultdict(set)