# Library Imports
import re
from urllib.parse import urlparse, urljoin, urldefrag
from urllib import robotparser
from collections import defaultdict, Counter
from bs4 import BeautifulSoup
import urllib.request
import nltk
import lxml
import threading

# Extra file imports
from scraper_data import ScraperData
from stopwords import STOPWORDS
from datasketch import MinHash
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# The URLS we want to visit
valid_urls = {".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"}

# Saves data about our scrapper, uses the ScraperData class to store information on visited pages, stats, longest_page, word_counts, and subdomains. 
scraper_data = ScraperData()

# Prints the information needed for reports. Uses data from ScraperData class. 
def print_report():
    with open("report.txt", "w") as f:
        f.write("Crawler Report:\n")
        f.write("Visited URLs: " + str(len(scraper_data.visited)) + "\n")
        for domain, count in scraper_data.stats.items():
            f.write("Domain: " + str(domain) + " Visited: " + str(count) + "\n")
        f.write("Longest page (by word count): " + str(scraper_data.longest_page) + "\n")
        f.write("50 most common words: " + str(scraper_data.word_counts.most_common(50)) + "\n")
        f.write("Subdomains:\n")
        for subdomain, urls in scraper_data.subdomains.items():
            f.write("Subdomain: " + str(subdomain) + " Unique pages: " + str(len(urls)) + "\n")

# Set a timer to call print_report every 30 minutes
def set_report_timer():
    threading.Timer(1800, set_report_timer).start()
    print_report()

# Main scrapper. It filters through all the links that were found and returns only the ones that pass the is_valid function tests. 
def scraper(url, resp):
    links = extract_next_links(url, resp)
    if links:
        return [link for link in links if is_valid(link)]
    else:
        return []

set_report_timer()

# Get next links
def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    new_urls = []
    try:

        # Adds URL to visited list
        url = url.replace(" ", "%20")
        if resp.raw_response:
            url = resp.raw_response.url

        scraper_data.visited.add(url)
        domain = urlparse(url).netloc
        scraper_data.stats[domain] += 1
        scraper_data.subdomains[domain].add(url)
        
        # Read url data if we get status 200
        if (resp.status == 200):
            # Make robot parser
            rp = robotparser.RobotFileParser()
            robot_page = urlparse(url).scheme + '://' + urlparse(url).netloc + '/robots.txt'
            rp.set_url(robot_page)
            rp.read()
                       
            # Check if we can get data form url if it exists
            if rp.can_fetch("*", url):       
                    # Use Beautiful Soup
                    soup = BeautifulSoup(resp.raw_response.content, 'lxml')

                    # Count words in the page and Check if page is low value
                    text = soup.get_text()
                    words = nltk.word_tokenize(text)
                    words = [word.lower() for word in words if word.isalpha()]
                    words = [word for word in words if word not in STOPWORDS]

                    # Compute the MinHash for the page
                    m = MinHash(num_perm=128)
                    for word in words:
                        m.update(word.encode('utf8'))

                    # Compare with MinHashes of previously visited pages
                    for visited_url, visited_minhash in scraper_data.page_minhashes.items():
                        similarity = m.jaccard(visited_minhash)
                        if similarity > 0.9:  # If the pages are very similar don't visit this page
                            return new_urls

                    # If the page is not similar to any visited page, add it to the list
                    scraper_data.page_minhashes[url] = m

                    if len(words) < 50:  # Check word count
                        return new_urls
                    common_words = [word for word in words if word in STOPWORDS]
                    if len(common_words) / len(words) > 0.8:  # Check proportion of common words
                        return new_urls
                    most_common_word_count = Counter(words).most_common(1)[0][1]
                    if most_common_word_count / len(words) > 0.2:  # Check diversity of words
                        return new_urls
                    
                    # If the page is not low value, update word counts and longest page
                    scraper_data.word_counts.update(words)
                    if len(words) > scraper_data.longest_page[1]:
                        scraper_data.longest_page = (url, len(words))

                    # Get all links
                    for link in soup.find_all('a'):
                        final = urldefrag(urljoin(url, link.get('href')))[0]
                        final_domain = urlparse(final).netloc
             
                        # Add the domains that we want to crawl
                        if (final not in scraper_data.visited) and (final not in new_urls):
                            for valid_domain in valid_urls:
                                if valid_domain in final_domain:
                                    new_urls.append(final)
                                    break
                                
## TODOS:
   # Detect and avoid infinite traps
   # Detect redirects and if the page redirects your crawler, index the redirected content
   # Detect and avoid crawling very large files, especially if they have low information value
   # Detect and avoid crawling very large files, especially if they have low information value

        # Respond to redirecting error codes
        elif resp.status in [300, 301, 302, 303, 307, 308]:
            response = urllib.request.urlopen(url)
            redirect = response.geturl()
            redirect_domain = urlparse(redirect).netloc
            if (redirect not in scraper_data.visited):
                for valid_url_domain in valid_url_domain:
                    if (valid_url_domain in redirect_domain):
                        new_urls.append(redirect)
                        break                           
                        
        return new_urls
    
    except:
        print("URL cannot be opened. Skipping URL:", url)
        return new_urls
 
def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Check through list of invalid queries
        if urlIsInvalid(url):
            return False
            
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise


# These functions are for trap prevention

def urlIsInvalid(url):
    # Additional bad queries
    invalid_queries = ['ical=', 'mailto:', 'image=', '=download', '=login', '=edit', 'replytocom=', '~eppstein/pix', '.calendar.', '/ml/datasets.php?']
    for invalid_query in invalid_queries:
        if invalid_query in url:
            return True

    # Check if our URL contains repeating paths
    if urlContainsRepeatingPaths(url):
        return True

    return False

def urlContainsRepeatingPaths(url):

    # Create dict of already visited path counts.
    subpath_count = defaultdict(int)
    path = urlparse(url).path
    for s in path.split("/"):
        if s != "":
            subpath_count[s] += 1
    
    # Check if we have duplicates (this is exact copies)
    for count in subpath_count.values():
        if count > 1:
            return True
    
    return False