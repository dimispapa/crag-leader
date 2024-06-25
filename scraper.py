import requests
from bs4 import BeautifulSoup

class Crag:

  def __init__(self, crag_url):
    self.crag_url = crag_url
    # define full url containing routelist
    self.routelist_url = f"{self.crag_url}routelist"
    # initialize request session object
    self.session = requests.Session()

  def get_boulders(self):
    # get response from url
    response = self.session.get(self.routelist_url)
    # parse response html content
    soup = BeautifulSoup(response.content, 'html5lib')
    # locate anchor elements with "sector-item" class.
    # These contain the boulder pages, exclude the first one which is a combined list of all routes
    boulder_anchors = soup.find_all('a', attrs={'class':'sector-item'})[1:]
    
    boulders = [] # iniatilize empty boulders list

    return soup, boulder_anchors

# testing  
CRAG_URL = "https://27crags.com/crags/inia-droushia/"
inia_droushia_crag = Crag(CRAG_URL)
test_soup, test_boulder_anchors = inia_droushia_crag.get_boulders()
print(test_boulder_anchors)
