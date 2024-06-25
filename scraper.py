import requests
from bs4 import BeautifulSoup

class Crag:
  
  def __init__(self, crag_url):
    self.crag_url = crag_url
    self.routelist_url = f"{self.crag_url}routelist"
    self.session = requests.Session()
    
  def get_boulders(self):
    response = self.session.get(self.routelist_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup
  
CRAG_URL = "https://27crags.com/crags/inia-droushia/"
inia_droushia_crag = Crag(CRAG_URL)
test = inia_droushia_crag.get_boulders()
print(test)
