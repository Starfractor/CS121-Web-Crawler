from collections import defaultdict, Counter
import scraper
from datasketch import MinHash

class ScraperData:
    def __init__(self):
        self.visited = set() # Set of all visited URLs
        self.stats = defaultdict(int) # Number of times each domain was visited
        self.longest_page = ("", 0) # URL and word count of the longest page
        self.word_counts = Counter() # Count of words across all visited pages
        self.subdomains = defaultdict(set) # Set of unique pages for each domain
        self.page_minhashes = {} # MinHash of the visited pages