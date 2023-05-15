from collections import defaultdict 
import atexit
import pickle
from os.path import exists

class ScraperData:
  def __init__(self):
    self.visited = set()
    self.similarity_list = []
    self.infinite_url_count = defaultdict(int)
    self.longest_page_count = -1
    self.longest_page = ""
    self.words_count = defaultdict(int)
    self.url_content_length = {}
    self.subdomains_count = defaultdict(int)

  def onexit(self):
    with open('report.txt', 'w') as report_file:
        report_file.write('NUMBER OF UNIQUE PAGES FOUND\n')
        report_file.write(str(len(self.visited)))
        report_file.write('\n')

        report_file.write('LONGEST PAGE\n')
        report_file.write(str(self.longest_page))
        report_file.write('\n')

        report_file.write('LONGEST PAGE COUNT\n')
        report_file.write(str(self.longest_page_count))
        report_file.write('\n')

        for word, num_occ in sorted(self.words_count.items(), key=lambda item: item[1], reverse=True)[:50]:
            report_file.write('COMMON WORD\n')
            report_file.write(str(word))
            report_file.write(' ')
            report_file.write(str(num_occ))
            report_file.write('\n')

        report_file.write("NUMBER OF UNIQUE SUBDOMAINS FOUND\n")
        report_file.write(str(len(self.subdomains_count)))
        report_file.write('\n')

        for key in sorted(self.subdomains_count):
            value = str(self.subdomains_count[key])
            report_file.write('SUBDOMAIN\n')
            report_file.write(key)
            report_file.write('    ')
            report_file.write(value)
            report_file.write('\n')

