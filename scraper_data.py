from collections import defaultdict, Counter
import scraper
from datasketch import MinHash

class ScraperData:
    def __init__(self):
        self.visited = set() # Set of all visited URLs
        self.simhash_list = []
        self.infinite_url_count = defaultdict(int)
        self.stats = defaultdict(int) # Number of times each domain was visited
        self.longest_page = ("", 0) # URL and word count of the longest page
        self.word_counts = Counter() # Count of words across all visited pages
        self.subdomains = defaultdict(set) # Set of unique pages for each domain
        self.page_minhashes = {} # MinHash of the visited pages

    def onexit(self):
       with open("report.txt", "w") as f:
        f.write("Crawler Report:\n")
        f.write("Visited URLs: " + str(len(self.visited)) + "\n")
        for domain, count in self.stats.items():
            f.write("Domain: " + str(domain) + " Visited: " + str(count) + "\n")
        f.write("Longest page (by word count): " + str(self.longest_page) + "\n")
        f.write("50 most common words: " + str(self.word_counts.most_common(50)) + "\n")
        f.write("Subdomains:\n")
        for subdomain, urls in self.subdomains.items():
            f.write("Subdomain: " + str(subdomain) + " Unique pages: " + str(len(urls)) + "\n")