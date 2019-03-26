#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import requests
import os
from jsonpath_ng.ext import parse
import datetime



# alla fine richiamare con
# > for line in dumpToSkos(downloadFromTellMeGlossary()): print line
class TellMeKeyword(object):
    import re

    def __init__(self, dictionary):
        self.id=dictionary["id"].__str__()
        self.title=TellMeKeyword.remove_tags(dictionary["title"]).replace(" ", "_")
        self.meaning=TellMeKeyword.remove_tags(dictionary["meaning"])
        self.context=TellMeKeyword.remove_tags(dictionary["context"])
        self.comment=TellMeKeyword.remove_tags(dictionary["comment"])
        self.reference=TellMeKeyword.remove_tags(dictionary["reference"])
        self.entryType=TellMeKeyword.remove_tags(dictionary["entryType"])

        # strings truncated to 255 chars to fit geonode tKeywords implementation.
        # This version is actually deprecated.
        self.title255 = TellMeKeyword.remove_tags255(dictionary["title"]).replace(" ", "_")
        self.meaning255 = TellMeKeyword.remove_tags255(dictionary["meaning"])
        self.context255 = TellMeKeyword.remove_tags255(dictionary["context"])
        self.comment255 = TellMeKeyword.remove_tags255(dictionary["comment"])
        self.reference255 = TellMeKeyword.remove_tags255(dictionary["reference"])
        self.entryType255 = TellMeKeyword.remove_tags255(dictionary["entryType"])

    #TAG_RE = re.compile(r'<[^>]+>')
    @staticmethod
    def remove_tags(text):
        if(text):
            text=text.replace('"',"'").replace(u"“","'").replace(u"”","'").replace(u"’","'").replace(u"&nbsp;"," ")
            TAG_RE = re.compile(r'<[^>]+>')
            #return(text)
            return TAG_RE.sub('', text)
        else:
            return ""

    # TAG_RE = re.compile(r'<[^>]+>')
    @staticmethod
    def remove_tags255(text):
        if (text):
            text = text[:250].replace('"', "'").replace(u"“", "'").replace(u"”", "'").replace(u"’", "'").replace(
                u"&nbsp;", " ")
            TAG_RE = re.compile(r'<[^>]+>')
            # return(text)
            return TAG_RE.sub('', text)
        else:
            return ""

    skosSnippet=u'''
tellme:keyword_{0.id}
        a                skos:Concept ;
        a                tellme:{0.entryType} ;
        dc:creator       {creator} ;
        dc:date          "{date}" ;
        owl:deprecated   "false"@en ;
        owl:versionInfo  "1"@en ;
        skos:altLabel    "{0.title}"@en , "{0.title}"@it , "{0.title}"@es ;
        skos:definition  "{0.meaning}"@en , "{0.meaning}"@it , "{0.meaning}"@es ;
        skos:inScheme    {inScheme} ;
        skos:note        "{0.comment}"@en ;
        skos:prefLabel   "{0.title}"@en , "{0.title}"@it , "{0.title}"@es ;
        skos:scopeNote   "{0.context}"@en ;
        skos:historyNote     <http://tellme.test.polimi.it/tellme_apps/tellme> .
    '''

    rdfxmlSnippet=u'''
    <skos:Concept rdf:about="http://rdfdata.get-it.it/TELLmeGlossary/keyword_{0.id}">
        <owl:versionInfo xml:lang="en">1</owl:versionInfo>
        <skos:historyNote rdf:resource="http://tellme.test.polimi.it/tellme_apps/tellme"/>
        <skos:prefLabel xml:lang="es">{0.title255}</skos:prefLabel>
        <skos:prefLabel xml:lang="it">{0.title255}</skos:prefLabel>
        <skos:prefLabel xml:lang="en">{0.title255}</skos:prefLabel>
        <skos:note xml:lang="en">{0.comment255}</skos:note>
        <skos:inScheme rdf:resource="{inScheme}"/>
        <skos:scopeNote xml:lang="en">{0.context255}</skos:scopeNote>
        <owl:deprecated xml:lang="en">false</owl:deprecated>
        <dc:date>{date}</dc:date>
        <rdf:type rdf:resource="http://rdfdata.get-it.it/TELLmeGlossary/{0.entryType}"/>
        <dc:creator rdf:resource="{creator}"/>
        <skos:definition xml:lang="es">{0.meaning255}</skos:definition>
        <skos:definition xml:lang="it">{0.meaning255}</skos:definition>
        <skos:definition xml:lang="en">{0.meaning255}</skos:definition>
        <skos:altLabel xml:lang="es">{0.title255}</skos:altLabel>
        <skos:altLabel xml:lang="it">{0.title255}</skos:altLabel>
        <skos:altLabel xml:lang="en">{0.title255}</skos:altLabel>
      </skos:Concept>
    '''

    def dump2SkosTTL(self):
        import datetime
        #ttl = self.id.__str__() + "\t" + self.title
        date=datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        creator="<http://tellmehub.get-it.it>"
        inScheme="<http://rdfdata.get-it.it/TELLmeGlossary>"
        ttl=self.skosSnippet.format(self,date=date,creator=creator, inScheme=inScheme)
        return ttl

    def dump2SkosRDF(self):
        import datetime
        #ttl = self.id.__str__() + "\t" + self.title
        date=datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        creator="http://tellmehub.get-it.it"
        inScheme="http://rdfdata.get-it.it/TELLmeGlossary"
        ttl=self.rdfxmlSnippet.format(self,date=date,creator=creator, inScheme=inScheme)
        return ttl


class TellMeConcept(TellMeKeyword):
    def __init__(self,dictionary):
        super(TellMeConcept,self).__init__(dictionary)
        #scales is a list
        self.scales=dictionary["scales"]
        #
        self.glossary=dictionary["glossary"].__str__()
        #scales in the original json are comma separated. Here we have them separated by spaces
        self.scalesAsText=TellMeKeyword.remove_tags(dictionary["scalesAsText"].replace(',', ' '))
        self.keywordId=dictionary["keywordId"]

    skosSnippet = u'''
tellme:relatedConcept_{0.id}
        a                skos:Concept ;
        a                tellme:relatedConcept;
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
        tellme:scales   "{0.scalesAsText}"@en .
    '''
    rdfxmlSnippet = u'''
    <skos:Concept rdf:about="http://rdfdata.get-it.it/TELLmeGlossary/relatedConcept_{0.id}">
        <owl:versionInfo xml:lang="en">1</owl:versionInfo>
        <skos:historyNote rdf:resource="http://tellme.test.polimi.it/tellme_apps/tellme"/>
        <skos:prefLabel xml:lang="es">{0.title255}</skos:prefLabel>
        <skos:prefLabel xml:lang="it">{0.title255}</skos:prefLabel>
        <skos:prefLabel xml:lang="en">{0.title255}</skos:prefLabel>
        <skos:note xml:lang="en">{0.comment255}</skos:note>
        <skos:inScheme rdf:resource="{inScheme}"/>
        <skos:scopeNote xml:lang="en">{0.context255}</skos:scopeNote>
        <owl:deprecated xml:lang="en">false</owl:deprecated>
        <dc:date>{date}</dc:date>
        <rdf:type rdf:resource="http://rdfdata.get-it.it/TELLmeGlossary/{0.entryType}"/>
        <dc:creator rdf:resource="{creator}"/>
        <skos:definition xml:lang="es">{0.meaning255}</skos:definition>
        <skos:definition xml:lang="it">{0.meaning255}</skos:definition>
        <skos:definition xml:lang="en">{0.meaning255}</skos:definition>
        <skos:altLabel xml:lang="es">{0.title255}</skos:altLabel>
        <skos:altLabel xml:lang="it">{0.title255}</skos:altLabel>
        <skos:altLabel xml:lang="en">{0.title255}</skos:altLabel>
        <tellme:scales xml:lang="en">{0.scalesAsText}</tellme:scales>
        <skos:editorialNote xml:lang="en">glossaryFlag:True</skos:editorialNote>
        <skos:broader rdf:resource="http://rdfdata.get-it.it/TELLmeGlossary/keyword_{0.keywordId}"/>
      </skos:Concept>
      '''



'''
TELLME_GLOSSARY_PASSWORD='<password>'
TELLME_GLOSSARY_USER='<user>'
TELLME_GLOSSARY_URL="http://tellme.test.polimi.it/tellme_apps/tellme/export"
'''
TELLME_GLOSSARY_PASSWORD='889GT3[]!1'
TELLME_GLOSSARY_USER='CNR'
TELLME_GLOSSARY_URL="http://tellme.test.polimi.it/tellme_apps/tellme/export"


def downloadFromTellMeGlossary():
    #import requests
    #import os
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
    #from jsonpath_ng.ext import parse
    date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    skosPreamble = u'''PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX tellme: <http://rdfdata.get-it.it/TELLmeGlossary/>
PREFIX dcterms: <http://purl.org/dc/terms/>

'''

    output=[]
    output.append(skosPreamble)
    output.append('''<http://rdfdata.get-it.it/TELLmeGlossary>
        a               skos:ConceptScheme ;
        dc:issues       "{date}"@en ;
        dc:description "TELLme Glossary. Developed in the context of TELLme Erasmus plus project"@en
        dcterms:issued "{date}"
        
        dc:title        "TELLme"@en , "TELLme Glossary"@it ;
        skos:prefLabel  "TELLme"@en , "TELLme Glossary"@it .
    '''.format(date=date))
    for k in jj["keywords"]:
        kw=TellMeKeyword(k)
        output.append(kw.dump2SkosTTL())
        for c in [m.value for m in parse('$.concepts[?keywordId=' + kw.id + ']').find(jj)]:
            #cs=concept2skos(c["id"],c["title"],kw.id,kw.title)
            #try:
            rc=TellMeConcept(c)
            #except Exception as e:
            #    print(e)
            #    #rc = TellMeConcept(c)
            #    pass
            output.append(rc.dump2SkosTTL())
            #print(output)
    return output

def dumpToSkosRDF(jj):
    # as jj we expect a dictionary whose source is json document
    # downloaded from http://tellme.test.polimi.it/tellme_apps/tellme/export
    #from jsonpath_ng.ext import parse
    date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    skosPreambleRDF = u'''<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcterms="http://purl.org/dc/terms/"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:owl="http://www.w3.org/2002/07/owl#"
    xmlns:skos="http://www.w3.org/2004/02/skos/core#"
    xmlns:tellme="http://rdfdata.get-it.it/TELLmeGlossary/">
        <skos:ConceptScheme rdf:about="http://rdfdata.get-it.it/TELLmeGlossary">
            <skos:prefLabel xml:lang="it">TELLme Glossary</skos:prefLabel>
            <skos:prefLabel xml:lang="en">TELLme</skos:prefLabel>
            <dc:title xml:lang="it">TELLme Glossary</dc:title>
            <dc:title xml:lang="en">TELLme</dc:title>
            <dc:issues xml:lang="en">{date}</dc:issues>
            <dc:description xml:lang="en">TELLme Glossary. Developed in the context of TELLme Erasmus plus project</dc:description>
            <dcterms:issued>{date}</dcterms:issued>
        </skos:ConceptScheme>
    '''.format(date=date)

    output=[]
    output.append(skosPreambleRDF.format(date=date))

    for k in jj["keywords"]:
        kw=TellMeKeyword(k)
        output.append(kw.dump2SkosRDF())
        for c in [m.value for m in parse('$.concepts[?keywordId=' + kw.id + ']').find(jj)]:
            #cs=concept2skos(c["id"],c["title"],kw.id,kw.title)
            #try:
            rc=TellMeConcept(c)
            #except Exception as e:
            #    print(e)
            #    #rc = TellMeConcept(c)
            #    pass
            output.append(rc.dump2SkosRDF())
            #print(output)
    output.append(u"</rdf:RDF>")
    return output

def dumpTreeString(jj):
    from jsonpath_ng.ext import parse

    for k in jj["keywords"]:
        keyword_id = k["id"]
        keyword_title = k["title"]
        print(keyword_id.__str__() + "\t" + keyword_title) #debug
        for c in [m.value for m in parse('$.concepts[?keywordId=' + keyword_id.__str__() + ']').find(jj)]:
            print("\t"+c["id"].__str__()+"\t"+c["title"])

def TellMeGlossary2Skos(type="ttl"):
    jj = downloadFromTellMeGlossary()
    #type = "rdf"  # "ttl"
    skos = []
    try:
        if type == "rdf":
            skos = dumpToSkosRDF(jj)
        else:
            skos = dumpToSkos(jj)
    except Exception as e:
        print(e)
        pass
    with open('TellMeGlossary.{type}'.format(type=type), 'w') as fileoutput:
        for line in skos:
            try:
                fileoutput.write(line.encode('utf-8'))
            except Exception as e:
                print(e)
                pass

if __name__ == "__main__":
    TellMeGlossary2Skos(type="ttl")

    #stringa=jj["keywords"][0]["meaning"]
    #nuovaStringa=TellMeKeyword.remove_tags(stringa)
    #print(nuovaStringa)

