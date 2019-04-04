#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import requests
import os
from jsonpath_ng.ext import parse
import datetime

class TellMeGlossary(object):
    def __init__(self):
        self.jj = downloadFromTellMeGlossary()
        self.keywords = self._keywords2dict(self.jj)
        self.concepts = self._concepts2dict(self.jj)

    @staticmethod
    def downloadFromTellMeGlossary():
        # import requests
        # import os
        # url = "http://tellme.test.polimi.it/tellme_apps/tellme/export"
        url = os.getenv("TELLME_GLOSSARY_URL", TELLME_GLOSSARY_URL)
        user = os.getenv("TELLME_GLOSSARY_USER", TELLME_GLOSSARY_USER)
        passwd = os.getenv("TELLME_GLOSSARY_PASSWORD", TELLME_GLOSSARY_PASSWORD)
        auth_values = (user, passwd)
        response = requests.get(url, auth=auth_values)
        jj = response.json()
        return (jj)

    @staticmethod
    def _keywords2dict(jj):
        d = {}
        for k in jj["keywords"]:
            d[k["id"]] = TellMeKeyword(k)
        return d

    @staticmethod
    def _concepts2dict(jj):
        d = {}
        for k in jj["concepts"]:
            d[k["id"]] = TellMeConcept(k)
        return d

    def extractConceptsByKeywordId(self, keyword_id):
        return [m.value for m in parse('$.concepts[?keywordId=' + keyword_id.__str__() + ']').find(self.jj)]

    def getTellMeKeyword(self,id):
        return self.keywords[id.__str__()]


# alla fine richiamare con
# > for line in dumpToSkosTTL(downloadFromTellMeGlossary()): print line
class TellMeKeyword(object):
    import re

    def __init__(self, dictionary):
        self.id = dictionary["id"].__str__()
        self.title = TellMeKeyword.remove_tags(dictionary["title"]).replace(" ", "_")
        self.meaning = TellMeKeyword.remove_tags(dictionary["meaning"])
        self.context = TellMeKeyword.remove_tags(dictionary["context"])
        self.comment = TellMeKeyword.remove_tags(dictionary["comment"])
        self.reference = TellMeKeyword.remove_tags(dictionary["reference"])
        self.entryType = TellMeKeyword.remove_tags(dictionary["entryType"])

        # strings truncated to 255 chars to fit geonode tKeywords implementation.
        # This version is actually deprecated.
        self.title255 = TellMeKeyword.remove_tags255(dictionary["title"]).replace(" ", "_")
        self.meaning255 = TellMeKeyword.remove_tags255(dictionary["meaning"])
        self.context255 = TellMeKeyword.remove_tags255(dictionary["context"])
        self.comment255 = TellMeKeyword.remove_tags255(dictionary["comment"])
        self.reference255 = TellMeKeyword.remove_tags255(dictionary["reference"])
        self.entryType255 = TellMeKeyword.remove_tags255(dictionary["entryType"])

    # TAG_RE = re.compile(r'<[^>]+>')
    @staticmethod
    def remove_tags(text):
        if (text):
            text = text.replace('"', "'").replace(u"“", "'").replace(u"”", "'").replace(u"’", "'").replace(u"&nbsp;",
                                                                                                           " ")
            TAG_RE = re.compile(r'<[^>]+>')
            # return(text)
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

    skosSnippet = u'''
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

    rdfxmlSnippet = u'''
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
        # ttl = self.id.__str__() + "\t" + self.title
        date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        creator = "<http://tellmehub.get-it.it>"
        inScheme = "<http://rdfdata.get-it.it/TELLmeGlossary>"
        ttl = self.skosSnippet.format(self, date=date, creator=creator, inScheme=inScheme)
        return ttl

    def dump2SkosRDF(self):
        import datetime
        # ttl = self.id.__str__() + "\t" + self.title
        date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        creator = "http://tellmehub.get-it.it"
        inScheme = "http://rdfdata.get-it.it/TELLmeGlossary"
        ttl = self.rdfxmlSnippet.format(self, date=date, creator=creator, inScheme=inScheme)
        return ttl

    def slug(self):
        return glos2slug(self.id, self.entryType)


class TellMeConcept(TellMeKeyword):
    def __init__(self, dictionary):
        super(TellMeConcept, self).__init__(dictionary)
        # scales is a list
        self.scales = dictionary["scales"]
        #
        self.glossary = dictionary["glossary"].__str__()
        # scales in the original json are comma separated. Here we have them separated by spaces
        self.scalesAsText = TellMeKeyword.remove_tags(dictionary["scalesAsText"].replace(',', ' '))
        self.keywordId = dictionary["keywordId"]

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
TELLME_GLOSSARY_PASSWORD = '889GT3[]!1'
TELLME_GLOSSARY_USER = 'CNR'
TELLME_GLOSSARY_URL = "http://tellme.test.polimi.it/tellme_apps/tellme/export"

# download glossary in json from external url
def downloadFromTellMeGlossary():
    # import requests
    # import os
    # url = "http://tellme.test.polimi.it/tellme_apps/tellme/export"
    url = os.getenv("TELLME_GLOSSARY_URL", TELLME_GLOSSARY_URL)
    user = os.getenv("TELLME_GLOSSARY_USER", TELLME_GLOSSARY_USER)
    passwd = os.getenv("TELLME_GLOSSARY_PASSWORD", TELLME_GLOSSARY_PASSWORD)
    auth_values = (user, passwd)
    response = requests.get(url, auth=auth_values)
    jj = response.json()
    return (jj)


# returns a list of turtle strings. serialize with "for line in dumpToSkosTTL: print line"
def dumpToSkosTTL(jj):
    # as jj we expect a dictionary whose source is json document
    # downloaded from http://tellme.test.polimi.it/tellme_apps/tellme/export
    # from jsonpath_ng.ext import parse
    date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    skosPreamble = u'''PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX tellme: <http://rdfdata.get-it.it/TELLmeGlossary/>
PREFIX dcterms: <http://purl.org/dc/terms/>

'''

    output = []
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
        kw = TellMeKeyword(k)
        output.append(kw.dump2SkosTTL())
        for c in [m.value for m in parse('$.concepts[?keywordId=' + kw.id + ']').find(jj)]:
            # cs=concept2skos(c["id"],c["title"],kw.id,kw.title)
            # try:
            rc = TellMeConcept(c)
            # except Exception as e:
            #    print(e)
            #    #rc = TellMeConcept(c)
            #    pass
            output.append(rc.dump2SkosTTL())
            # print(output)
    return output

# return a list of strings containing RDF/XML code
def dumpToSkosRDF(jj):
    # as jj we expect a dictionary whose source is json document
    # downloaded from http://tellme.test.polimi.it/tellme_apps/tellme/export
    # from jsonpath_ng.ext import parse
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

    output = []
    output.append(skosPreambleRDF.format(date=date))

    for k in jj["keywords"]:
        kw = TellMeKeyword(k)
        output.append(kw.dump2SkosRDF())
        for c in [m.value for m in parse('$.concepts[?keywordId=' + kw.id + ']').find(jj)]:
            # cs=concept2skos(c["id"],c["title"],kw.id,kw.title)
            # try:
            rc = TellMeConcept(c)
            # except Exception as e:
            #    print(e)
            #    #rc = TellMeConcept(c)
            #    pass
            output.append(rc.dump2SkosRDF())
            # print(output)
    output.append(u"</rdf:RDF>")
    return output

# prints the trees of Keywords and related concepts
def dumpTreeString(jj):
    from jsonpath_ng.ext import parse

    for k in jj["keywords"]:
        keyword_id = k["id"]
        keyword_title = k["title"]
        print(keyword_id.__str__() + "\t" + keyword_title)  # debug
        for c in [m.value for m in parse('$.concepts[?keywordId=' + keyword_id.__str__() + ']').find(jj)]:
            print("\t" + c["id"].__str__() + "\t" + c["title"])




def TellMeGlossary2Skos(type="ttl"):
    jj = downloadFromTellMeGlossary()
    # type = "rdf"  # "ttl"
    skos = []
    try:
        if type == "rdf":
            skos = dumpToSkosRDF(jj)
        else:
            skos = dumpToSkosTTL(jj)
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

    # stringa=jj["keywords"][0]["meaning"]
    # nuovaStringa=TellMeKeyword.remove_tags(stringa)
    # print(nuovaStringa)

def glos2slug(id,type):
    if type not in {"keyword","concept"}:
        raise ValueError(type)
    return u"{type}_{id}".format(type=type ,id=id.__str__())

def slug2glosId(slug):
    return(slug[8:])

def slug2type(slug):
    return(slug[:7])

def setAsChildBySlug(hkSlug,hkTargetSlug):
    from geonode.base.models import HierarchicalKeyword
    HierarchicalKeyword.objects.get(slug=hkSlug).move(
        HierarchicalKeyword.objects.get(slug=hkTargetSlug, pos="sorted-child"))

def getKeywordGlossaryById(jj,id):
    return TellMeKeyword([k.value for k in parse('$.keywords[{id}]'.format(id=id)).find(jj)][0])

def synchGlossaryWithHierarchicalKeywords(g):
    #g=TellMeGlossary()
    jj=g.jj

    #[m.value for m in parse('$.concepts[?keywordId=' + keyword_id.__str__() + ']').find(self.jj)]
    glossaryKIds=[k.value for k in parse('$.keywords[*].id').find(jj)]
    glossaryCIds=[k.value for k in parse('$.concepts[*].id').find(jj)]

    expectedKSlugsInHK=[glos2slug(*g) for g in [(k.value["id"], k.value["entryType"]) for k in parse('$.keywords[*]').find(jj)]]
    expectedCSlugsInHK=[glos2slug(*g) for g in [(k.value["id"], k.value["entryType"]) for k in parse('$.concepts[*]').find(jj)]]

    if HierarchicalKeyword.objects.filter(name="TELLme").exists():
        root = HierarchicalKeyword.objects.get(name="TELLme")
    else:
        root = HierarchicalKeyword(name="TELLme")
        HierarchicalKeyword.add_root(instance=root)

    if HierarchicalKeyword.objects.filter(name="z_otherKeywords").exists():
        other_root = HierarchicalKeyword.objects.get(name="z_otherKeywords")
    else:
        other_root = HierarchicalKeyword(name="z_otherKeywords")
        HierarchicalKeyword.add_root(instance=other_root)

    def setAsOtherKeyword(hk):
        setAsChildBySlug(hk.slug, other_root.slug)

    def setAsTellmeKeyword(hk):
        setAsChildBySlug(hk.slug, root.slug)

    # sposto tutto in root secondaria
    for hk in HierarchicalKeyword.objects.exclude(id=root.id).exclude(id=other_root.id):
        setAsOtherKeyword(hk)

    # sposto tutte le kewyord come figlie di root
    for k in g.keywords.items():
        gk=k[1]

        if HierarchicalKeyword.objects.filter(slug = gk.slug()).exists():
            try:
                hk=HierarchicalKeyword.objects.get(slug=gk.slug())
                setAsTellmeKeyword(hk)
            except:
                pass
        else:
            try:
                hk=HierarchicalKeyword(slug=gk.slug(), name=gk.title)
                root.add_child(hk)
            except:
                pass



    # 1. go through id of keywords in glossary.
    #    a. does the corresponding slug exist?
    #       - no: create a corresponding HK
    #       - yes: check if it is synchronised with this version. If not, update the HK.
    # 2. go through id of concepts in glossary
    #    a. does the slug exist?
    #       - no: create the HK
    #       - yes: check if they are synched. If not, update the HK.
    # 3. Go through all the keywords in "TELLme" branch (TELLme is the root of HK related to Tellme)
    #    If a slug2glos id of type keyword is not present within the glossary, remove it from Tellme branch and put it under
    #    the "_other" branch of HK
    from geonode.base.models import HierarchicalKeyword

    HierarchicalKeyword.objects.get(slug=s)

# ipotesi lavoro sui metadati
mitree= Layer.objects.get(name__contains="zone decentramento milano")
# se leggo mi.metadata_xml ho un file diverso da quello di EDI!!!!
# devo leggere la versione "clean" di mdextension, se no mi da errore
mitree= etree.fromstring(mi.mdextension.rndt_xml_clean)
mdata=EDI_Metadata(mitree)
mdata.identification.keywords
# a questo punto ritrovo quel che mi aspettavo:
'''
[{'keywords': ['Administrative units'],
  'thesaurus': {'date': '2008-06-01',
   'datetype': 'publication',
   'title': 'GEMET - INSPIRE themes, version 1.0'},
  'type': None},
 {'keywords': ['Milano'],
  'thesaurus': {'date': None, 'datetype': None, 'title': None},
  'type': 'place'},
 {'keywords': ['Land_use'],
  'thesaurus': {'date': '2019-03-28T17:20:45',
   'datetype': 'publication',
   'title': 'http://rdfdata.get-it.it/TELLmeGlossary/'},
  'type': None},
 {'keywords': ['L M'],
  'thesaurus': {'date': None, 'datetype': None, 'title': None},
  'type': None}]
'''

for k in exml.findall(util.nspath_eval(
        'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gmx:Anchor',
        namespaces)):
    print etree.tostring(k)
    print type(k)
'''
< gmx:Anchor
xmlns:gmx = "http://www.isotc211.org/2005/gmx"
xmlns:xlink = "http://www.w3.org/1999/xlink"
xmlns:gmd = "http://www.isotc211.org/2005/gmd"
xmlns:gco = "http://www.isotc211.org/2005/gco"
xmlns:gml = "http://www.opengis.net/gml"
xmlns:xsi = "http://www.w3.org/2001/XMLSchema-instance"
xlink:href = "http://rdfdata.get-it.it/TELLmeGlossary/concept_4" > Airport < / gmx:Anchor >

< type
'lxml.etree._Element' >
'''

ns=namespaces
ns[None]=None
exml.xpath("//gmx:Anchor[@xlink:href='http://rdfdata.get-it.it/TELLmeGlossary/concept_4']",namespaces=ns)

'''
--> [<Element {http://www.isotc211.org/2005/gmx}Anchor at 0x7f02691857a0>]
''''

k=exml.xpath("//gmx:Anchor[@xlink:href='http://rdfdata.get-it.it/TELLmeGlossary/concept_4']",namespaces=ns)
print etree.tostring(k[0])

k=exml.xpath("//gmx:Anchor[text()='Airport']",namespaces=ns)
print etree.tostring(k[0])


k=exml.xpath("//gmd:MD_Keywords[.//gmx:Anchor/text()='Airport']",namespaces=ns)
print etree.tostring(k[0])
'''
<gmd:MD_Keywords xmlns:gmd="http://www.isotc211.org/2005/gmd" xmlns:gco="http://www.isotc211.org/2005/gco" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:gml="http://www.opengis.net/gml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:gmx="http://www.isotc211.org/2005/gmx">
               <gmd:keyword>
                  <gmx:Anchor xlink:href="http://rdfdata.get-it.it/TELLmeGlossary/concept_4">Airport</gmx:Anchor>
               </gmd:keyword>
               <gmd:thesaurusName>
                  <gmd:CI_Citation>
                     <gmd:title>
                        <gco:CharacterString>http://rdfdata.get-it.it/TELLmeGlossary/</gco:CharacterString>
                     </gmd:title>
                     <gmd:date>
                        <gmd:CI_Date>
                           <gmd:date>
                              <gco:Date>2019-03-28T17:20:45</gco:Date>
                           </gmd:date>
                           <gmd:dateType>
                              <gmd:CI_DateTypeCode codeList="http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/Codelist/ML_gmxCodelists.xml#CI_DateTypeCode" codeListValue="publication">publication</gmd:CI_DateTypeCode>
                           </gmd:dateType>
                        </gmd:CI_Date>
                     </gmd:date>
                  </gmd:CI_Citation>
               </gmd:thesaurusName>
            </gmd:MD_Keywords>

'''
##########
'''
Non capisco questo comportamento:
'''
#
'''

In [203]: k=exml.xpath(u"//gmd:MD_Keywords//gmx:Anchor/@xlink:href",namespaces=ns)

In [204]: k
Out[204]: ['http://rdfdata.get-it.it/TELLmeGlossary/concept_4']

In [205]: k=exml.xpath(u"//gmd:MD_Keywords[//gmx:Anchor/@xlink:href]",namespaces=ns)

In [206]: k
Out[206]:
[<Element {http://www.isotc211.org/2005/gmd}MD_Keywords at 0x7f02690ec098>,
 <Element {http://www.isotc211.org/2005/gmd}MD_Keywords at 0x7f026a70cf38>,
 <Element {http://www.isotc211.org/2005/gmd}MD_Keywords at 0x7f0269170050>,
 <Element {http://www.isotc211.org/2005/gmd}MD_Keywords at 0x7f0269104200>]

In [207]: for kw in k:
     ...:     print kw.xpath("//gmx:Anchor/@xlink:href",namespaces=ns)
     ...:
['http://rdfdata.get-it.it/TELLmeGlossary/concept_4']
['http://rdfdata.get-it.it/TELLmeGlossary/concept_4']
['http://rdfdata.get-it.it/TELLmeGlossary/concept_4']
['http://rdfdata.get-it.it/TELLmeGlossary/concept_4']

In [208]: for kw in k:
     ...:     print kw.xpath("//gmx:Anchor/@xlink:href",namespaces=ns)
     ...:     print kw.xpath("//gmx:Anchor",namespaces=ns)
['http://rdfdata.get-it.it/TELLmeGlossary/concept_4']
[<Element {http://www.isotc211.org/2005/gmx}Anchor at 0x7f026908b128>]
['http://rdfdata.get-it.it/TELLmeGlossary/concept_4']
[<Element {http://www.isotc211.org/2005/gmx}Anchor at 0x7f026908b128>]
['http://rdfdata.get-it.it/TELLmeGlossary/concept_4']
[<Element {http://www.isotc211.org/2005/gmx}Anchor at 0x7f026908b128>]
['http://rdfdata.get-it.it/TELLmeGlossary/concept_4']
[<Element {http://www.isotc211.org/2005/gmx}Anchor at 0x7f026908b128>]

'''