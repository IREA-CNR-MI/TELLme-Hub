# NOTES:
# treebeard 4.1.2
# taggit 0.18.0
# percorsi in docker container django:
# /usr/local/lib/python2.7/site-packages/taggit/
# /usr/local/lib/python2.7/site-packages/treebeard/
# riferimento in geonode/base/models.py in definizione di HierarchicalKeyword che eredita da entrambi



from geonode.base.models import TopicCategory, HierarchicalKeyword
#from geonode.base.models import ResourceBase, Region, TopicCategory, ALL_LANGUAGES
#from geonode.layers.models import Layer
#from geonode.maps.models import Map

#k0=HierarchicalKeyword


root=HierarchicalKeyword.add_root(name='TELLme')

import requests
url="http://tellme.test.polimi.it/tellme_apps/tellme/export"
user="CNR"
passwd="PASSWORD_GLOSSARY"
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


def downloadFromTellMeGlossary():
    import requests
    import os
    #url = "http://tellme.test.polimi.it/tellme_apps/tellme/export"
    url = os.getenv("TELLME_GLOSSARY_URL",TELLME_GLOSSARY_URL)
    user = os.getenv("TELLME_GLOSSARY_USER",TELLME_GLOSSARY_USER)
    #passwd = "Oh]7}sg!jj"
    #passwd = "pwd456()!è**[]"
    passwd=os.getenv("TELLME_GLOSSARY_PASSWORD",TELLME_GLOSSARY_PASSWORD)
    auth_values = (user, passwd)
    response = requests.get(url, auth=auth_values)
    jj = response.json()
    return(jj)

def dumpTreeString(jj):
    from jsonpath_ng.ext import parse

    for k in jj["keywords"]:
        keyword_id = k["id"]
        keyword_title = k["title"]
        print(keyword_id.__str__() + "\t" + keyword_title) #debug
        for c in [m.value for m in parse('$.concepts[?keywordId=' + keyword_id.__str__() + ']').find(jj)]:
            print("\t"+c["id"].__str__()+"\t"+c["title"])

def setAsChildByName(hkName,hkTargetName):
    from geonode.base.models import HierarchicalKeyword
    HierarchicalKeyword.objects.get(name=hkName).move(
        HierarchicalKeyword.objects.get(name=hkTargetName,pos="sorted-child"))

def setAsSiblingByName(hkName,hkTargetName):
    from geonode.base.models import HierarchicalKeyword
    HierarchicalKeyword.objects.get(name=hkName).move(
        HierarchicalKeyword.objects.get(name=hkTargetName, pos="sorted-sibling"))

def isHierarchicalKeywordName(name):
    from geonode.base.models import HierarchicalKeyword
    try:
        hk=HierarchicalKeyword.objects.get(name=name)
        return(type(hk)==HierarchicalKeyword)
    except:
        return(False)
