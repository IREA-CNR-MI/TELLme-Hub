# alla fine richiamare con
# > for line in dumpToSkos(downloadFromTellMeGlossary()): print line
class TellMeKeyword(object):
    import re

    def __init__(self, dictionary):
        self.id=dictionary["id"].__str__()
        self.title=TellMeKeyword.remove_tags(dictionary["title"])
        self.meaning=TellMeKeyword.remove_tags(dictionary["meaning"])
        self.context=TellMeKeyword.remove_tags(dictionary["context"])
        self.comment=TellMeKeyword.remove_tags(dictionary["comment"])
        self.reference=TellMeKeyword.remove_tags(dictionary["reference"])
        self.entryType=TellMeKeyword.remove_tags(dictionary["entryType"])



    TAG_RE = re.compile(r'<[^>]+>')
    @staticmethod
    def remove_tags(text):
        return(text)
        #return TAG_RE.sub('', text)

    skosSnippet=u'''
        tellme:keyword_{0.id}
            a                skos:Concept ;
            dc:creator       {creator} ;
            dc:date          "{date}"@en ;
                owl:deprecated   "false"@en ;
                owl:versionInfo  "1"@en ;
                skos:altLabel    "{0.title}"@en , "{0.title}"@it , "{0.title}"@es ;
                skos:broader     tellme:{0.entryType} ;
                skos:definition  "{0.meaning}"@en , "{0.meaning}"@it , "{0.meaning}"@es ;
                skos:inScheme    {inScheme} ;
                skos:note        "{0.comment}"@en ;
                skos:prefLabel   "{0.title}"@en , "{0.title}"@it , "{0.title}"@es ;
                skos:scopeNote   "{0.context}"@en ;
                skos:historyNote     <http://tellme.test.polimi.it/tellme_apps/tellme> .
        '''

    def dump2SkosTTL(self):
        import datetime
        #ttl = self.id.__str__() + "\t" + self.title
        date=datetime.datetime.utcnow().isoformat()
        creator="<http://tellmehub.get-it.it>"
        inScheme="<http://rdfdata.get-it.it/TELLmeGlossary> "
        ttl=self.skosSnippet.format(self,date=date,creator=creator, inScheme=inScheme)
        return ttl

class TellMeConcept(TellMeKeyword):
    def __init__(self,dictionary):
        super(TellMeConcept,self).__init__(dictionary)
        self.scales=TellMeKeyword.remove_tags(dictionary["scales"])
        self.glossary=dictionary["glossary"].__str__()
        self.scalesAsText=TellMeKeyword.remove_tags(dictionary["scalesAsText"])
        self.keywordId=TellMeKeyword.remove_tags(dictionary["keywordId"])

    skosSnippet = u'''
            tellme:relatedConcept_{0.id}
                a                skos:Concept ;
                dc:creator       {creator} ;
                dc:date          "{date}"@en ;
                    owl:deprecated   "false"@en ;
                    owl:versionInfo  "1"@en ;
                    skos:altLabel    "{0.title}"@en , "{0.title}"@it , "{0.title}"@es ;
                    skos:broader     tellme:keyword_{0.keywordId} ;
                    skos:definition  "{0.meaning}"@en , "{0.meaning}"@it , "{0.meaning}"@es ;
                    skos:inScheme    {inScheme} ;
                    skos:note        "{0.comment}"@en ;
                    skos:prefLabel   "{0.title}"@en , "{0.title}"@it , "{0.title}"@es ;
                    skos:scopeNote   "{0.context}"@en ;
                    skos:historyNote     <http://tellme.test.polimi.it/tellme_apps/tellme> ;
                    skos:editorialNote "glossaryFlag:{0.glossary}"@en ;
                    tellme:scales   "{0.scalesAsText}"@en
            '''

TELLME_GLOSSARY_PASSWORD='<password>'
TELLME_GLOSSARY_USER='<user>'
TELLME_GLOSSARY_URL="http://tellme.test.polimi.it/tellme_apps/tellme/export"

def downloadFromTellMeGlossary():
    import requests
    import os
    #url = "http://tellme.test.polimi.it/tellme_apps/tellme/export"
    url = os.getenv("TELLME_GLOSSARY_URL",TELLME_GLOSSARY_URL)
    user = os.getenv("TELLME_GLOSSARY_USER",TELLME_GLOSSARY_USER)
    passwd=os.getenv("TELLME_GLOSSARY_PASSWORD",TELLME_GLOSSARY_PASSWORD)
    auth_values = (user, passwd)
    response = requests.get(url, auth=auth_values)
    jj = response.json()
    return(jj)

# returns a list of strings. serialize with "for line in dumpToSkos: print line"
def dumpToSkos(jj):
    # as jj we expect a dictionary whose source is json document
    # downloaded from http://tellme.test.polimi.it/tellme_apps/tellme/export
    from jsonpath_ng.ext import parse
    date = datetime.datetime.utcnow().isoformat()

    skosPreamble = '''
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX tellme: <http://rdfdata.get-it.it/TELLmeGlossary/>
        '''

    output=[]
    output.append(skosPreamble)
    output.append('''<http://rdfdata.get-it.it/TELLmeGlossary>
        a               skos:ConceptScheme ;
        dc:issues       "{date}"@en ;
        dc:title        "TELLme"@en , "TELLme Glossary"@it ;
        skos:prefLabel  "TELLme"@en , "TELLme Glossary"@it .
    '''.format(date=date))
    for k in jj["keywords"]:
        kw=TellMeKeyword(k)
        output.append(kw.dump2SkosTTL())
        for c in [m.value for m in parse('$.concepts[?keywordId=' + kw.id + ']').find(jj)]:
            #cs=concept2skos(c["id"],c["title"],kw.id,kw.title)
            rc=TellMeConcept(c)
            output.append(rc.dump2SkosTTL())
            #print(output)
    return output
