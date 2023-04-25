import re
from urllib.parse import urlparse, urljoin, urldefrag
from collections import defaultdict
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

def scraper(url, resp):
    links = extract_next_links(url, resp)
    if links:
        return [link for link in links if is_valid(link)]
    else:
        return []

robot_parsers = {}
    
def get_robot(url):
    domain = urlparse(url).scheme + '://' + urlparse(url).hostname
    if domain not in robot_parsers:
        robot_parser = RobotFileParser()
        robot_parser.set_url(urljoin(domain, '/robots.txt'))
        robot_parser.read()
        robot_parsers[domain] = robot_parser

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

    # Detect and avoid dead URLs that return a 200 status but no data
    if resp.status != 200 or resp.error:
        return []

    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]

    allowed_links = []
    for link in links:
        absolute_links = urljoin(url, link) # Converts relative URLs to absolute URLs
        defrag_link, _ = urldefrag(absolute_links) # Defragments the URL
        robot_parser = get_robot(defrag_link)
        if robot_parser.can_fetch("*", defrag_link):
            allowed_links.append(defrag_link)

    return allowed_links
 
def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Crawl only the specified domains and paths stated in the assignment
        if not re.match(r".*\.ics\.uci\.edu/.*|.*\.cs\.uci\.edu/.*|.*\.informatics\.uci\.edu/.*|.*\.stat\.uci\.edu/.*", url):
            return False
        
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