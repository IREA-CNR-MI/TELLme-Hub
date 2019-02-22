from geonode.base.models import TopicCategory, HierarchicalKeyword
#from geonode.base.models import ResourceBase, Region, TopicCategory, ALL_LANGUAGES
#from geonode.layers.models import Layer
#from geonode.maps.models import Map

#k0=HierarchicalKeyword


root=HierarchicalKeyword.add_root(name='TELLme')

import requests
url="http://tellme.test.polimi.it/tellme_apps/tellme/export"
user="CNR"
passwd="Oh]7}sg!jj"
auth_values = (user, passwd)
response = requests.get(url, auth=auth_values)
jj=response.json()
print(jj)

#from jsonpath_rw import jsonpath, parse
#jsonpath_expr = parse('$.concepts[?@.keywordId]')
#jsonpath_expr = parse('$.concepts[*].id')
#jsonpath_expr = parse('$.concepts[?(@.keywordId)]')

from jsonpath_ng import jsonpath
# cfr. answer to https://github.com/h2non/jsonpath-ng/issues/8
# it is necessary to import from .ext to exploit filters
from jsonpath_ng.ext import parse

#tutti i concetti riferiti a keyword=1
jsonpath_expr = parse('$.concepts[?keywordId=1]')

#estraggo solo keyword 1
expr_k1=parse('$.keywords[?id=1]')
l_k1=[match.value for match in expr_k1.find(jj)]

# write json the opposite direction
import json
dumpback=json.dumps(l_k1) # A STRING

jj_k1=json.loads(dumpback)


lc=[match.value for match in jsonpath_expr.find(jj)]
#lc.sort() # sort avviene inline, nell'oggetto stesso
#print(lc)

matches=jsonpath_expr.find(jj)

for match in jsonpath_expr.find(jj):
    print(match.value)