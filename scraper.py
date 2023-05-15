import ssl
from collections import defaultdict
from bs4 import BeautifulSoup
import urllib.request
from urllib import robotparser
from urllib.parse import urlparse, urljoin, urldefrag
import re
import nltk
import time
import atexit
from stopwords import STOPWORDS
from scraper_data import ScraperData
nltk.download('punkt')
ssl._create_default_https_context = ssl._create_unverified_context

url_set = {".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"}

scraper_data = ScraperData()

# Main Scraper
def scraper(url, resp):
    links = extract_next_links(url, resp)

    if links:
        return [link for link in links if is_valid(link)]
    else:
        return []

def extract_next_links(url, resp):
    new_urls = []
    try:
        url = url.replace(" ", "%20")
        if resp.raw_response:
            url = resp.raw_response.url

        scraper_data.visited.add(url)

        with open('report.txt', 'w') as report_file:
            report_file.write('NUMBER OF UNIQUE PAGES FOUND\n')
            report_file.write(str(len(scraper_data.visited)))
            report_file.write('\n')

            report_file.write('LONGEST PAGE\n')
            report_file.write(str(scraper_data.longest_page))
            report_file.write('\n')

            report_file.write('LONGEST PAGE COUNT\n')
            report_file.write(str(scraper_data.longest_page_count))
            report_file.write('\n')

            for word, num_occ in sorted(scraper_data.words_count.items(), key=lambda item: item[1], reverse=True)[:50]:
                report_file.write('COMMON WORD\n')
                report_file.write(str(word))
                report_file.write(' ')
                report_file.write(str(num_occ))
                report_file.write('\n')

            report_file.write("NUMBER OF UNIQUE SUBDOMAINS FOUND\n")
            report_file.write(str(len(scraper_data.subdomains_count)))
            report_file.write('\n')

            for key in sorted(scraper_data.subdomains_count):
                value = str(scraper_data.subdomains_count[key])
                report_file.write('SUBDOMAIN\n')
                report_file.write(key)
                report_file.write('    ')
                report_file.write(value)
                report_file.write('\n')


        if resp.status == 200:

            # Creates robot to read through file
            rp = robotparser.RobotFileParser()
            robot_page = urlparse(url).scheme + '://' + \
                                  urlparse(url).netloc + '/robots.txt'
            rp.set_url(robot_page)
            rp.read()

            if rp.can_fetch("*", url):
                if resp.raw_response.content:   # checks if url has data

                    # check if this url is a subdomain
                    subdomain_check(urldefrag(url))


                    soup = BeautifulSoup(resp.raw_response.content, 'lxml')

                    # tokenize text here
                    text = soup.get_text()
                    tokens = nltk.word_tokenize(text)

                    # Check for similar pages
                    # check if similar
                    url_freq_dict = defaultdict(int)
                    most_words_count = 0
                    for word in tokens:
                        word_lower = word.lower()
                        if word_lower not in STOPWORDS and word.isalpha():  # justification: only interested
                            url_freq_dict[word_lower] += 1
                            scraper_data.words_count[word_lower] += 1
                            most_words_count += 1

                    url_binary = sim_hash(url_freq_dict)

                    similar = False

                    for b in scraper_data.similarity_list:
                        if is_near_duplicate(compare_sim_hashes(b, url_binary)):
                            similar = True

                    # avoid empty/low info content and very large files (via number of tokens)
                    if not similar and len(tokens) < 6000 and len(tokens) > 10:
                        scraper_data.similarity_list.append(url_binary)

                        # process tokenize using nltk, add to defaultdict
                        if most_words_count > scraper_data.longest_page_count:
                            scraper_data.longest_page_count = most_words_count
                            scraper_data.longest_page = url

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
            response = request.urlopen(url)
            redirect = response.geturl()
            redirect_domain = urlparse(redirect).netloc
            if (redirect not in scraper_data.visited):
                for valid_url_domain in url_set:
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

        if isValidURL(url):
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

# Trap detection
def urlRepeatsPaths(url):
    subpath_count = defaultdict(int)
    path = urlparse(url).path
    for s in path.split("/"):
        if s != "":
            subpath_count[s] += 1
    
    # if a duplicate path is found 
    for count in subpath_count.values():
        if count > 1:
            return True
    
    return False