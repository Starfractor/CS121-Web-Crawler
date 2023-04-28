# Library Imports
import re
from urllib.parse import urlparse, urljoin, urldefrag
from urllib import robotparser
from collections import defaultdict
from bs4 import BeautifulSoup
import nltk
import lxml

# Extra file imports
from scraper_data import ScraperData
from stopwords import STOPWORDS

# The URLS we want to visit
valid_urls = {".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"}

# Saves data about our scrapper
scraper_data = ScraperData()

# Main scrapper
def scraper(url, resp):
    links = extract_next_links(url, resp)
    if links:
        return [link for link in links if is_valid(link)]
    else:
        return []


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
        
        # Read url data if we get status 200
        if resp.status == 200:
            # Make robot parser
            rp = robotparser.RobotFileParser()
            robot_page = urlparse(url).scheme + '://' + \
                urlparse(url).netloc + '/robots.txt'
            rp.set_url(robot_page)
            rp.read()
                       
            # Check if we can get data form url if it exists
            if rp.can_fetch("*", url):
                    
                    # Use Beautiful Soup
                    soup = BeautifulSoup(resp.raw_response.content, 'lxml')

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

                        
        return new_urls
    
    except:
        print("URL cannot be opened. Skipping URL:", url)
        return new_urls

    return allowed_links
 
def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Check through list of invalid queries
        invalid_queries = ['ical=', 'mailto:', 'image=', '=download', '=login', '=edit', 'replytocom=', '~eppstein/pix', '.calendar.', '/ml/datasets.php?']
        for invalid_query in invalid_queries:
            if invalid_query in url:
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

    # Create dict of path counts
    subpath_count = defaultdict(int)
    path = urlparse(url).path
    for s in path.split("/"):
        if s != "":
            subpath_count[s] += 1
    
    # Check if we have duplicates 
    for count in subpath_count.values():
        if count > 1:
            return True
    
    return False

            