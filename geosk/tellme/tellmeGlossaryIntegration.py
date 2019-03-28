#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import requests
import os
from jsonpath_ng.ext import parse
import datetime


'''
TELLME_GLOSSARY_PASSWORD='<password>'
TELLME_GLOSSARY_USER='<user>'
TELLME_GLOSSARY_URL="http://tellme.test.polimi.it/tellme_apps/tellme/export"
'''
TELLME_GLOSSARY_PASSWORD = '889GT3[]!1'
TELLME_GLOSSARY_USER = 'CNR'
TELLME_GLOSSARY_URL = "http://tellme.test.polimi.it/tellme_apps/tellme/export"


class TellMeGlossary(object):

    tellmescheme = "http://rdfdata.get-it.it/TELLmeGlossary"

    def __init__(self):
        self.jj = self.downloadFromTellMeGlossary()
        # dict id:keyword
        self.keywords = {k["id"]: TellMeKeyword(k) for k in self.jj["keywords"]}
        self.concepts = {k["id"]: TellMeConcept(k) for k in self.jj["concepts"]}
        self.protocols = {k["id"]: TellMeProtocol(k) for k in self.jj["protocols"]}

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

    def listConceptsByKeyword(self, keyword):
        return [self.concepts[m.value["id"]] for m in parse('$.concepts[?keywordId=' + keyword.id + ']').find(self.jj)]

    def getSetOfScales(self):
        o=set()
        for c in self.concepts.values():
            for s in c.scales:
                o.add(s["scale"])
        return o

    # returns a list of turtle strings. serialize with "for line in dumpToSkosTTL: print line"
    def dumpToSkos(self,mode="ttl"):
        # as jj we expect a dictionary whose source is json document
        # downloaded from http://tellme.test.polimi.it/tellme_apps/tellme/export
        # from jsonpath_ng.ext import parse
        date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        skosPreamble={
            "ttl": u'''PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX tellme: <{tellmescheme}/>
PREFIX dcterms: <http://purl.org/dc/terms/>

<{tellmescheme}>
    a               skos:ConceptScheme ;
    dc:issues       "{date}"@en ;
    dc:description "TELLme Glossary. Developed in the context of TELLme Erasmus plus project"@en ;
    dcterms:issued "{date}" ;
    dc:title        "TELLme"@en , "TELLme Glossary"@it ;
    skos:prefLabel  "TELLme"@en , "TELLme Glossary"@it .
''',
            "xml": u'''<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcterms="http://purl.org/dc/terms/"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:owl="http://www.w3.org/2002/07/owl#"
    xmlns:skos="http://www.w3.org/2004/02/skos/core#"
    xmlns:tellme="{tellmescheme}/">
        <skos:ConceptScheme rdf:about="{tellmescheme}">
            <skos:prefLabel xml:lang="it">TELLme Glossary</skos:prefLabel>
            <skos:prefLabel xml:lang="en">TELLme</skos:prefLabel>
            <dc:title xml:lang="it">TELLme Glossary</dc:title>
            <dc:title xml:lang="en">TELLme</dc:title>
            <dc:issues xml:lang="en">{date}</dc:issues>
            <dc:description xml:lang="en">TELLme Glossary. Developed in the context of TELLme Erasmus plus project</dc:description>
            <dcterms:issued>{date}</dcterms:issued>
        </skos:ConceptScheme>
''',
            "txt":"dump of {tellmescheme} - {date}\n"
        }

        skosFooter={"ttl": u"",
                    "xml": u"</rdf:RDF>",
                    "txt": ""}

        output = []
        output.append(skosPreamble[mode].format(date=date, tellmescheme=self.tellmescheme))
        for kw in self.keywords.values():
            output.append(kw.dump2Skos(mode=mode))
            for rc in self.listConceptsByKeyword(kw):
                output.append(rc.dump2Skos(mode=mode))
        for protocol in self.protocols.values():
            output.append(protocol.dump2Skos(mode=mode))
        for scale in self.getSetOfScales():
            output.append(u'''
            tellme:scale_{scale}
                    a                skos:Concept ;
                    a                tellme:scale ;
                    dc:creator       <{creator}> ;
                    owl:deprecated   "false"@en ;                    
                    skos:altLabel    "{scale}"@en , "{scale}"@it , "{scale}"@es ;
                    skos:definition  "{scale}"@en , "{scale}"@it , "{scale}"@es ;
                    skos:inScheme    <{tellmescheme}> ;
                    skos:prefLabel   "{scale}"@en , "{scale}"@it , "{scale}"@es ;
                    skos:historyNote     <http://tellme.test.polimi.it/tellme_apps/tellme> .
                '''.format(scale=scale,
                           creator="http://tellmehub.get-it.it",
                           tellmescheme="http://rdfdata.get-it.it/TELLmeGlossary"))
        output.append(skosFooter[mode])
        return output


class TellMeEntry(object):
    skosSnippet = {
        "ttl": u'''
tellme:{0.entryType}_{0.id}
        a                skos:Concept ;
        a                tellme:{0.entryType} ;
        dc:creator       <{creator}> ;
        dc:date          "{date}" ;
        owl:deprecated   "false"@en ;
        owl:versionInfo  "1"@en ;
        skos:altLabel    "{0.title}"@en , "{0.title}"@it , "{0.title}"@es ;
        skos:definition  "{0.meaning}"@en , "{0.meaning}"@it , "{0.meaning}"@es ;
        skos:inScheme    <{tellmescheme}> ;
        skos:note        "{0.comment}"@en ;
        skos:prefLabel   "{0.title}"@en , "{0.title}"@it , "{0.title}"@es ;
        skos:scopeNote   "{0.context}"@en ;
        skos:historyNote     <http://tellme.test.polimi.it/tellme_apps/tellme> .
    ''',
        "xml": u'''
    <skos:Concept rdf:about="{tellmescheme}/{0.entryType}_{0.id}">
        <owl:versionInfo xml:lang="en">1</owl:versionInfo>
        <skos:historyNote rdf:resource="http://tellme.test.polimi.it/tellme_apps/tellme"/>
        <skos:prefLabel xml:lang="es">{0.title255}</skos:prefLabel>
        <skos:prefLabel xml:lang="it">{0.title255}</skos:prefLabel>
        <skos:prefLabel xml:lang="en">{0.title255}</skos:prefLabel>
        <skos:note xml:lang="en">{0.comment255}</skos:note>
        <skos:inScheme rdf:resource="{tellmescheme}"/>
        <skos:scopeNote xml:lang="en">{0.context255}</skos:scopeNote>
        <owl:deprecated xml:lang="en">false</owl:deprecated>
        <dc:date>{date}</dc:date>
        <rdf:type rdf:resource="{tellmescheme}/{0.entryType}"/>
        <dc:creator rdf:resource="{creator}"/>
        <skos:definition xml:lang="es">{0.meaning255}</skos:definition>
        <skos:definition xml:lang="it">{0.meaning255}</skos:definition>
        <skos:definition xml:lang="en">{0.meaning255}</skos:definition>
        <skos:altLabel xml:lang="es">{0.title255}</skos:altLabel>
        <skos:altLabel xml:lang="it">{0.title255}</skos:altLabel>
        <skos:altLabel xml:lang="en">{0.title255}</skos:altLabel>
    </skos:Concept>
    ''',
        "txt":u"{0.entryType}_{0.id}\t{0.title}"
    }

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

    def dump2Skos(self,mode):
        import datetime
        date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        creator = "http://tellmehub.get-it.it"
        tellmescheme = "http://rdfdata.get-it.it/TELLmeGlossary"
        rdf = self.skosSnippet[mode].format(self, date=date, creator=creator, tellmescheme=tellmescheme)
        return rdf

    def slug(self):
        return self.glos2slug(self.id, self.entryType)

    # def get_parent_hk(self):
    #     pass

    # get or create a HierarchicalKeyword under the given parent.
    # The method instantiates the HierarchicalKeyword and returns it.
    def toHierarchicalKeywordChildOf(self, hk_parent):
        from geonode.base.models import HierarchicalKeyword
        if HierarchicalKeyword.objects.filter(slug=self.slug()).exists():
            hk = HierarchicalKeyword.objects.get(slug=self.slug())
            setAsChild(hk, HierarchicalKeyword.objects.get(id=hk_parent.id))
            return hk
        elif HierarchicalKeyword.objects.filter(name=self.title).exists():
            hk = HierarchicalKeyword.objects.get(name=self.title)
            hk.slug = self.slug()
            setAsChild(hk, HierarchicalKeyword.objects.get(id=hk_parent.id))
            return hk
        else:
            hk = HierarchicalKeyword(slug=self.slug(), name=self.title)
            HierarchicalKeyword.objects.get(id=hk_parent.id).add_child(instance=hk)
            return hk

    @staticmethod
    def glos2slug(id,type):
        if type not in {"keyword","concept"}:
            raise ValueError(type)
        return u"{type}_{id}".format(type=type ,id=id.__str__())

    @staticmethod
    def slug2glosId(slug):
        return slug[8:]

    @staticmethod
    def slug2type(slug):
        return slug[:7]


class TellMeKeyword(TellMeEntry):

    # def get_parent_hk(self):
    #     from geonode.base.models import HierarchicalKeyword
    #     self.getHKroot()

    import re

    # TAG_RE = re.compile(r'<[^>]+>')

    # TAG_RE = re.compile(r'<[^>]+>')


class TellMeConcept(TellMeEntry):
    def __init__(self, dictionary):
        super(TellMeConcept, self).__init__(dictionary)
        # scales is a list
        self.scales = dictionary["scales"]
        #
        self.glossary = dictionary["glossary"].__str__()
        # scales in the original json are comma separated. Here we have them separated by spaces
        self.scalesAsText = TellMeKeyword.remove_tags(dictionary["scalesAsText"].replace(',', ' '))
        self.keywordId = dictionary["keywordId"]

    # def get_parent_hk(self):
    #     from geonode.base.models import HierarchicalKeyword
    #
    # def get_parentKeyword(self):
    #

    skosSnippet = {"ttl": TellMeEntry.skosSnippet["ttl"]+
                   u'''        skos:broader     tellme:keyword_{0.keywordId} ;
        skos:editorialNote "glossaryFlag:{0.glossary}"@en ;
        tellme:scales   "{0.scalesAsText}"@en .
    ''',
                   "xml": u'''
    <skos:Concept rdf:about="{tellmescheme}/{0.entryType}_{0.id}">
        <owl:versionInfo xml:lang="en">1</owl:versionInfo>
        <skos:historyNote rdf:resource="http://tellme.test.polimi.it/tellme_apps/tellme"/>
        <skos:prefLabel xml:lang="es">{0.title255}</skos:prefLabel>
        <skos:prefLabel xml:lang="it">{0.title255}</skos:prefLabel>
        <skos:prefLabel xml:lang="en">{0.title255}</skos:prefLabel>
        <skos:note xml:lang="en">{0.comment255}</skos:note>
        <skos:inScheme rdf:resource="{tellmescheme}"/>
        <skos:scopeNote xml:lang="en">{0.context255}</skos:scopeNote>
        <owl:deprecated xml:lang="en">false</owl:deprecated>
        <dc:date>{date}</dc:date>
        <rdf:type rdf:resource="{tellmescheme}/{0.entryType}"/>
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
      ''',
                   "txt": u"\n\t {txt}".format(txt=TellMeEntry.skosSnippet["txt"])
                   }


class TellMeProtocol(TellMeEntry):
    def __init__(self, dictionary):
        super(TellMeProtocol, self).__init__(dictionary)
        self.scales = dictionary["scales"]

    scaleSnippet = {
        "ttl": u"\ntellme:{0.entryType}_{0.id} tellme:containsAtScale_{scale} tellme:{entryType}_{id} ."
    }

    def getScaleSnippets(self):
        output=[]
        s=""
        scalelist=self.scales
        for scale in scalelist:
            sscale = scale["scale"]
            for c in scale["concepts"]:
                sa = self.scaleSnippet["ttl"].format(self, entryType=c["entryType"], id=c["id"].__str__(), scale=sscale)
                output.append(sa)
        for so in output:
            s += so
        return s
            # for o in [{"scale": scale["scale"], "concepts": scale["concepts"]} for scale in self.scales]:
            # for cdict in o["concepts"]:
            #     c = TellMeConcept(cdict)
            #     print self.scaleSnippet["ttl"].format(self, c, scale=o["scale"])

    def dump2Skos(self, mode):
        s = super(TellMeProtocol, self).dump2Skos(mode)
        if mode=="ttl":
            s += self.getScaleSnippets()
        return s


def dumpTTLGlossaryToStaticDir():
    import geosk
    g = TellMeGlossary()
    jj = g.jj
    mode = "ttl"
    skos = g.dumpToSkos(mode=mode)
    outdir = os.path.dirname(geosk.__file__) + "/static/tellme/"
    with open(outdir + 'TellMeGlossary.{mode}'.format(mode=mode), 'w') as fileoutput:
        for line in skos:
            try:
                fileoutput.write(line.encode('utf-8'))
            except Exception as e:
                print(e)
                pass


# TODO: refactor creating a Binder class aware of both
#  HierarchicalKeyword and TellMeEntries and remove references of HK from other classes
def setAsChild(hk,targetHk):
    # move any existing HierarchicalKeyword as child of a target
    def setAsChildBySlug(hkSlug, hkTargetSlug):
        from geonode.base.models import HierarchicalKeyword
        HierarchicalKeyword.objects.get(slug=hkSlug).move(
            HierarchicalKeyword.objects.get(slug=hkTargetSlug), pos="sorted-child")

    return setAsChildBySlug(hk.slug, targetHk.slug)

# def getKeywordGlossaryById(jj,id):
#     return TellMeKeyword([k.value for k in parse('$.keywords[{id}]'.format(id=id)).find(jj)][0])


# the returned HierarchicalKeyword will be instantiated in the DB
def getOrCreateHierarchicalKeywordRootByName(root_name):
    from geonode.base.models import HierarchicalKeyword
    if HierarchicalKeyword.objects.filter(name=root_name).exists():
        root = HierarchicalKeyword.objects.get(name=root_name)
        if not root.is_root():
            root.move(
                HierarchicalKeyword.get_first_root_node(), pos="sorted-sibling")
    else:
        root = HierarchicalKeyword(name=root_name)
        HierarchicalKeyword.add_root(instance=root)
    return root


def synchGlossaryWithHierarchicalKeywords(g):
    from geonode.base.models import HierarchicalKeyword

    # obtain root and other root. The getCreateHierarchicalKeywordRootByName
    # grant existence and root-ness!
    root = getOrCreateHierarchicalKeywordRootByName(u"TELLme")
    other_root = getOrCreateHierarchicalKeywordRootByName(u"z_otherKeywords")

    # NOTE: Before each call of any processing of a HierarchicalKeyword previously obtained,
    # we must refresh the HierarchicalKeyword from the db,
    # otherwise the in-memory objects (called for instance by a "filter" or "get" statement
    # that we assigned to variables, could not be in the current state, i.e. decoupled from the underlying db record.
    # For example, if I obtain a list of HierarchicalKeyword, e.g. with HierarchicalKeyword.objects.filter(depth=1),
    # and then (with a for loop or with a map) I process the first list element,
    # the database record related to all the other elements in the list are updated too.
    # At this point the python instances I collected within the list are not in a consistent state with respect
    # to their db record counterparts, so, if I process them without refreshing from db, I get many troubles
    # and an inconsistent HierarchicalKeyword tree.
    # The following code should resolve this issue.

    # def maxdepth():
    #     ''':returns: the HierarchicalKeyword tree height'''
    #     from functools import reduce
    #     if HierarchicalKeyword.objects.count() > 0:
    #         return reduce((lambda x, y: max(x, y)), [node.depth for node in HierarchicalKeyword.objects.all()])
    #     else:
    #         return 0

    # completely flatten the tree
    # while maxdepth()>1:
    #     map((lambda x: HierarchicalKeyword.objects.get(id=x).move(HierarchicalKeyword.get_last_root_node(), "sorted-sibling")),
    #         [h.id for h in HierarchicalKeyword.objects.filter(depth=maxdepth())])

    map((lambda x: HierarchicalKeyword.objects.get(id=x).move(HierarchicalKeyword.get_last_root_node(), "sorted-sibling")),
        [h.id for h in HierarchicalKeyword.objects.exclude(id__in=[rid.id for rid in HierarchicalKeyword.get_root_nodes()])])

    # put all HierarchicalKeyword tree nodes under other_root
    map((lambda x: HierarchicalKeyword.objects.get(id=x).move(HierarchicalKeyword.objects.get(id=other_root.id), "sorted-child")),
        HierarchicalKeyword.objects.filter(depth=1).exclude(id=root.id).exclude(id=other_root.id))

    #move all tellme glossary kewyords under "root" node
    for k in g.keywords.items():
        gk = k[1]  # gk is a 2-ple (id,TELLmeKeyword)

        # get the corresponding HierarchicalKeyword (existing or new) after
        # having moved it under root node
        hgk = gk.toHierarchicalKeywordChildOf(root)
        for c in g.listConceptsByKeyword(gk):
            c.toHierarchicalKeywordChildOf(hgk)  # c is already a TELLmeConcept

    # # 1. go through id of keywords in glossary.
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


if __name__ == "__main__":
    #g = TellMeGlossary()
    #jj=g.jj
    #mode="ttl"
    if False:
        with open('TellMeProtocols.{mode}'.format(mode=mode), 'w') as fileoutput:
            for p in jj["protocols"]:
                protocol=TellMeProtocol(p)
                skos=protocol.dump2Skos(mode)
                #protocol.scales

                for line in skos:
                    fileoutput.write(line.encode('utf-8'))
                #print protocol.getScaleSnippets()

    if True:
        dumpTTLGlossaryToStaticDir()


# #recover state in db.
#
# def _get_path(path, depth, newstep):
#     """
#     Builds a path given some values
#     :param path: the base path
#     :param depth: the depth of the  node
#     :param newstep: the value (integer) of the new step
#     """
#
#     alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
#     steplen = 4
#
#     parentpath = _get_basepath(path, depth - 1)
#     key = _int2str(newstep)
#     return '{0}{1}{2}'.format(
#         parentpath,
#         alphabet[0] * (steplen - len(key)),
#         key
#     )
#
# NumConv(len(cls.alphabet), cls.alphabet)
#
#
# def _int2str(cls, num):
#     return cls.numconv_obj().int2str(num)
#
#
# def _get_basepath(cls, path, depth):
#     """:returns: The base path of another path up to a given depth"""
#     if path:
#         return path[0:depth * cls.steplen]
#     return ''
#