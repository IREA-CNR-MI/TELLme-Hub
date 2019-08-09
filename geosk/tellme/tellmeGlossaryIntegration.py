#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import requests
import os
from jsonpath_ng.ext import parse
import datetime
from geonode.base.models import HierarchicalKeyword


'''
TELLME_GLOSSARY_PASSWORD='<password>'
TELLME_GLOSSARY_USER='<user>'
TELLME_GLOSSARY_URL="http://tellme.test.polimi.it/tellme_apps/tellme/export"
'''
TELLME_GLOSSARY_PASSWORD = '889GT3[]!1'
TELLME_GLOSSARY_USER = 'CNR'
TELLME_GLOSSARY_URL = "http://www.tellme.polimi.it/tellme_apps/tellme/export"

class TellMeGlossary(object):
    """
    An object representing the contents of TELLme glossary with the structure
    from the Polimi App.
    """

    tellmescheme = "http://rdfdata.get-it.it/TELLmeGlossary"

    def __init__(self):
        '''
        init a new instance of TellMeGlossary calling the remote TELLme glossary application API
        '''
        self.jj = self.downloadFromTellMeGlossary()
        # dict id:keyword
        self.keywords = {k["id"]: TellMeKeyword(k) for k in self.jj["keywords"]}
        self.concepts = {k["id"]: TellMeConcept(k) for k in self.jj["concepts"]}
        self.protocols = {k["id"]: TellMeProtocol(k) for k in self.jj["protocols"]}
        self.scales = {s: TellMeScale(s) for s in self.getSetOfScales()}

    @staticmethod
    def tellmeGlossarySourceURL():
        url=os.getenv("TELLME_GLOSSARY_URL", TELLME_GLOSSARY_URL)
        return url.replace("export", "")

    @staticmethod
    def downloadFromTellMeGlossary():
        '''
        Downloads the TellMe Glossary from the API of the polimi TELLme glossary App
        :return: a dictionary from the downloaded json
        '''
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

    def dumpToSkos(self,mode="ttl"):
        '''
        serialize the Glossary in RDF.
        a list of turtle strings.
        NOTE: for debug purposes the return value can be serialized with
        "for line in <returnValue>: print line"
        :param mode: (string) "ttl" | "xml" | "txt"
        :return: RDF (or textual) serialization of the glossary. The return value is actually a list of strings
        '''
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
                    skos:historyNote     <{tellmeGlossarySourceURL}> .
                '''.format(scale=scale,
                           creator="http://tellmehub.get-it.it",
                           tellmescheme="http://rdfdata.get-it.it/TELLmeGlossary",
                           tellmeGlossarySourceURL=TellMeGlossary.tellmeGlossarySourceURL()))
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
        skos:historyNote     <{tellmeGlossarySourceURL}> .
    ''',
        "xml": u'''
    <skos:Concept rdf:about="{tellmescheme}/{0.entryType}_{0.id}">
        <owl:versionInfo xml:lang="en">1</owl:versionInfo>
        <skos:historyNote rdf:resource="{tellmeGlossarySourceURL}"/>
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
        rdf = self.skosSnippet[mode].format(self, date=date, creator=creator, tellmescheme=tellmescheme,
                                            tellmeGlossarySourceURL=TellMeGlossary.tellmeGlossarySourceURL())
        return rdf

    def slug(self):
        """
        Return the slug of the represented entry.
        It is intended to be the slug for the HierarchicalKeyword in get-it
        :return:
        """
        return self.glos2slug(self.id, self.entryType)

    # def get_parent_hk(self):
    #     pass

    def toHierarchicalKeywordChildOf(self, hk_parent):
        """
        get or create a HierarchicalKeyword under the given parent (Do nothing if already ok).
        :param hk_parent: (HierarchicalKeyword)
        :return: (HierarchicalKeyword) the obtained HK
        """

        from geonode.base.models import HierarchicalKeyword
        if HierarchicalKeyword.objects.filter(slug=self.slug()).exists():
            hk = HierarchicalKeyword.objects.get(slug=self.slug())
            # TODO: implement the logics needed to update eventually changed title of the concept in the glossary sw
            #  e.g.
            # if(hk.name!=self.title):
            #   hk.name=self.title
            #   hk.save()
            setAsChild(hk, HierarchicalKeyword.objects.get(id=hk_parent.id))
            return hk
        elif HierarchicalKeyword.objects.filter(name=self.title).exists():
            hk = HierarchicalKeyword.objects.get(name=self.title)
            hk.slug = self.slug()
            hk.save()
            setAsChild(hk, HierarchicalKeyword.objects.get(id=hk_parent.id))
            return hk
        else:
            # create a new HierarchicalKeyword and put it under hk_parent
            hk = HierarchicalKeyword(slug=self.slug(), name=self.title)
            HierarchicalKeyword.objects.get(id=hk_parent.id).add_child(instance=hk)
            return hk

    @staticmethod
    def glos2slug(id,type):
        """
        Return the slug of the entry corresponding to given id and type.
        It is intended to be the slug for the HierarchicalKeyword in get-it
        :param id: (string or int)
        :param type: (string) "keyword" | "concept"
        :return:
        """
        if type not in {"keyword","concept"}:
            raise ValueError(type)
        return u"{type}_{id}".format(type=type ,id=id.__str__())

    @staticmethod
    def slug2glosId(slug):
        """
        Return the id in the tellme glossary given the Entry slug
        :param slug:
        :return: (string)
        """
        try:
            return slug.split("_")[1]
        except Exception as e:
            pass


    @staticmethod
    def slug2type(slug):
        """
        Return the type in the tellme glossary given the Entry slug
        :param slug:
        :return: (string)
        """
        try:
            return slug.split("_")[0]
        except Exception as e:
            pass


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
                   u'''tellme:{0.entryType}_{0.id}       skos:broader     tellme:keyword_{0.keywordId} ;
        skos:editorialNote "glossaryFlag:{0.glossary}"@en ;
        tellme:scales   "{0.scalesAsText}"@en .
    ''',
                   "xml": u'''
    <skos:Concept rdf:about="{tellmescheme}/{0.entryType}_{0.id}">
        <owl:versionInfo xml:lang="en">1</owl:versionInfo>
        <skos:historyNote rdf:resource="{tellmeGlossarySourceURL}"/>
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

# note: TellMeScales are treated differently within the same TellMeGlossary class
class TellMeScale(TellMeEntry):
    def __init__(self, title):
        self.title = title
        self.entryType = u"scale"
        #self.id=title

    def slug(self):
        return u"{type}_{id}".format(type=self.entryType, id=self.title)


def dumpTTLGlossaryToStaticDir(g):
    """
    Write the RDF ttl serialization in the tellme static directory of the get-it, reachable at the url
    http://<get-it-URL>/static/tellme/TELLmeGlossary.ttl
    :param g:
    :return:
    """
    import geosk
    #g = TellMeGlossary()
    #jj = g.jj
    mode = "ttl"
    skos = g.dumpToSkos(mode=mode)
    outdir = os.path.dirname(geosk.__file__) + "/static/tellme/"
    with open(outdir + 'TELLmeGlossary.{mode}'.format(mode=mode), 'w') as fileoutput:
        for line in skos:
            try:
                fileoutput.write(line.encode('utf-8'))
            except Exception as e:
                print(e)
                pass


# TODO: refactor creating a Binder class aware of both
#  HierarchicalKeyword and TellMeEntries and remove references of HK from other classes
def setAsChild(hk,targetHk):
    """
    move any existing HierarchicalKeyword as child of a target
    NOTE: the passed HierarchicalKeywords slugs must be consistent with their
    database versions. Save them before calling this method.
    :param hk:
    :param targetHk:
    :return:
    """
    def setAsChildBySlug(hkSlug, hkTargetSlug):
        from geonode.base.models import HierarchicalKeyword

        if HierarchicalKeyword.objects.get(slug=hkSlug).is_child_of(
                HierarchicalKeyword.objects.get(slug=hkTargetSlug)):
            pass
        else:
            HierarchicalKeyword.objects.get(slug=hkSlug).move(
                HierarchicalKeyword.objects.get(slug=hkTargetSlug), pos="sorted-child")

    return setAsChildBySlug(hk.slug, targetHk.slug)

# def getKeywordGlossaryById(jj,id):
#     return TellMeKeyword([k.value for k in parse('$.keywords[{id}]'.format(id=id)).find(jj)][0])


# the returned HierarchicalKeyword will be instantiated in the DB
def getOrCreateHierarchicalKeywordRootByName(root_name):
    """
    Create or retrurn the existing HierarchicalKeyword with the given name
    :param root_name:
    :return: (HierarchicalKeyword)
    """
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


def getHierarchicalKeywordListBySlug(slug):
    """
    Given a slug return the corresponding HK objects
    :param slug:
    :return: (list) of HierarchicalKeywords
    """
    from geonode.base.models import HierarchicalKeyword
    return HierarchicalKeyword.objects.filter(slug=slug)

def move_genericHK_level1_under_otherkeywords_branch(keywords=[]):
    """
    Move all the HK  at root level having their name in the passed keywords list
    under the OtherKeywords branch
    :param keywords: (list) names of the keywords to move if they are at root level
    :return: (void)
    """
    # node.id in list if node is root, node is not one of the predefined roots, node.name is one of the
    # names in "keywords" parameter
    list_nodes_id_to_move = \
        [k.id for k in HierarchicalKeyword.
            get_root_nodes().
            exclude(id__in=_getPredefinedHKRootNodesIdList()).
            filter(name__in=keywords)]

    map((lambda x: HierarchicalKeyword.objects.get(id=x.id).
         move(HierarchicalKeyword.objects.get(id=_getOtherKeywordsRoot().id), "sorted-child")),
        HierarchicalKeyword.objects.filter(id__in=list_nodes_id_to_move)
        )

def _getPredefinedHKRootNodesIdList():
    """
    :return: (list) id of predefined roots
    """
    #from geonode.base.models import HierarchicalKeyword
    root = getOrCreateHierarchicalKeywordRootByName(u"TELLme")
    rootScales = getOrCreateHierarchicalKeywordRootByName(u"TELLme-scales")
    other_root = _getOtherKeywordsRoot()
    id_list = [root.id, rootScales.id, other_root.id]
    return id_list

def _getOtherKeywordsRoot():
    """
    get or create the root node to host the "other keywords"
    :return:
    """
    return getOrCreateHierarchicalKeywordRootByName(u"z_otherKeywords")


# added 2019/07/29
def delete_non_tellme_hierarchicalKeywords():
    from geonode.base.models import HierarchicalKeyword
    slugs=[c.slug for c in HierarchicalKeyword.objects.exclude(slug__icontains="concept_").exclude(slug__icontains="keyword_").exclude(slug__icontains="scale_").exclude(name__in=[u"TELLme", u"TELLme-scales", u"z_otherKeywords"])]
    for slug in slugs:
        HierarchicalKeyword.objects.get(slug=slug).delete()


def synchNewKeywordsFromTELLmeGlossary():
    """
    The method reads the actual version of the glossary and adds the keywords/related concepts
    that are not present as HK in the Hub. Older keywords/related concepts are left untouched evev
    if some changes occured in the Glossary software
    :param g:
    :return: dictionary: {"added_keywords": added_keywords,
                          "added_concepts": added_concepts,
                          "with_issues": issues}"
    """
    missingGConcepts, missingGKeywords = list_new_entries_from_glossary()

    issues = []
    added_keywords = []
    added_concepts = []

    # generate missing keywords as HierarchicalKeywords
    for k in missingGKeywords:
        try:
            k.toHierarchicalKeywordChildOf(getOrCreateHierarchicalKeywordRootByName(u"TELLme"))
            added_keywords.append(k)
        except Exception as e:
            issues.append(e)

    for c in missingGConcepts:
        its_keyword_slug = TellMeEntry.glos2slug(c.keywordId, "keyword")
        try:
            #hkk=HierarchicalKeyword.objects.get(slug=its_keyword_slug)
            c.toHierarchicalKeywordChildOf(HierarchicalKeyword.objects.get(slug=its_keyword_slug))
            added_concepts.append(c)
        except Exception as e:
            issues.append(e)
    return {"added_keywords": added_keywords,
            "added_concepts": added_concepts,
            "with_issues": issues}


def list_new_entries_from_glossary():
    g = TellMeGlossary()
    from geonode.base.models import HierarchicalKeyword
    # root = getOrCreateHierarchicalKeywordRootByName(u"TELLme")
    all_current_keyword_slugs = [k[1].slug() for k in g.keywords.items()]
    all_current_concept_slugs = [c[1].slug() for c in g.concepts.items()]
    all_current_HK_keyword_slugs = [hc.slug for hc in HierarchicalKeyword.objects.filter(slug__icontains="keyword_")]
    all_current_HK_concept_slugs = [hc.slug for hc in HierarchicalKeyword.objects.filter(slug__icontains="concept_")]
    # get missing keywords and concepts from HK. We must create the corresponding HK
    missingHK_keywords = list(set.difference(set(all_current_keyword_slugs), set(all_current_HK_keyword_slugs)))
    missingHK_concepts = list(set.difference(set(all_current_concept_slugs), set(all_current_HK_concept_slugs)))
    # [[g.concepts[i].id == i.__str__()] for i in g.concepts.keys()]
    # [[g.keywords[i].id == i.__str__()] for i in g.keywords.keys()]
    # missingKeywordsId=[TellMeKeyword.slug2glosId(slug) for slug in missingHK_keywords]
    # missingConceptsId=[TellMeConcept.slug2glosId(slug) for slug in missingHK_concepts]
    # g.keywords[missingKeywordsId]
    missingGKeywords = [g.keywords[int(TellMeKeyword.slug2glosId(slug))] for slug in missingHK_keywords]
    missingGConcepts = [g.concepts[int(TellMeConcept.slug2glosId(slug))] for slug in missingHK_concepts]
    return missingGConcepts, missingGKeywords




# TODO: this method should be revised.
def synchGlossaryWithHierarchicalKeywords(g, force=True):
    """
    Read the content of TELLme Glossary object, check the presence of corresponding
    geonode HierarchicalKeywords (HK) in GET-IT instance.
    New TellmeGlossary keywords and concepts are translated in HK and organized according the hierarchy
    of the glossary under the HK root node "TELLme Keywords".
    HK of other kind are organized as direct descendants of the "_zOtherKeywords" root HK
    (the method creates it if this root node is not present).
    [hint: Call the method with g = TellMeGlossary()]
    :param g: TellmeGlossary object
    :param force: (bool) True force recreation of the full tree, otherwise tries to adjust the actual tree with possibile new entries
    :return: nothing
    """
    from geonode.base.models import HierarchicalKeyword

    # obtain root and other root. The getCreateHierarchicalKeywordRootByName
    # grant existence and root-ness!
    root = getOrCreateHierarchicalKeywordRootByName(u"TELLme")
    rootScales = getOrCreateHierarchicalKeywordRootByName(u"TELLme-scales")
    other_root = _getOtherKeywordsRoot()

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

    list_of_predefined_root_id = _getPredefinedHKRootNodesIdList()

    predefined_roots_and_descendants_id = list_of_predefined_root_id
    # TODO: check if get_descendants returns correct hk. An issue occurred caused by subsequent call to this function.
    #  Probably, it would be better to use explicit calls to HK.ojects.get also for retrieving descendants...
    predefined_roots_and_descendants_id.extend([hk.id for hk in root.get_descendants()])
    predefined_roots_and_descendants_id.extend([hk.id for hk in rootScales.get_descendants()])
    predefined_roots_and_descendants_id.extend([hk.id for hk in other_root.get_descendants()])

    if force:

        # TODO: to keep the tree cleaner, implement a routine to force deletion of all the non-tellme hierarchical
        #  keywords that are automatically added by the base geonode when inserting layers
        #  the code should be something like
        #  (PLEASE CHECK IF ALL PREFIXES AND RESERVED TELLme HierarchicalKeywords are
        #  properly excluded before deleting!):
        # -------------
        # slugs=[c.slug for c in HierarchicalKeyword.objects.exclude(slug__icontains="concept_").exclude(slug__icontains="keyword_").exclude(slug__icontains="scale_").exclude(name__in=[u"TELLme", u"TELLme-scales", u"z_otherKeywords"])]
        # for slug in slugs:
        #     HierarchicalKeyword.objects.get(slug=slug).delete()
        #
        # -------------
        # Inserted in the method that can be invoked here:
        # delete_non_tellme_hierarchicalKeywords()


        # move any non-root keyword at root level
        map((lambda x: HierarchicalKeyword.objects.get(id=x).
             move(HierarchicalKeyword.get_last_root_node(), "sorted-sibling")),
            [h.id for h in HierarchicalKeyword.objects.exclude(id__in=[rid.id for rid in HierarchicalKeyword.get_root_nodes()])])

        # fix inconsistencies
        HierarchicalKeyword.fix_tree()

        # move any root node, with the exception of the predefined roots, under the "other keywords" root
        map((lambda x: HierarchicalKeyword.objects.get(id=x.id).
             move(HierarchicalKeyword.objects.get(id=other_root.id), "sorted-child")),
            HierarchicalKeyword.objects.filter(depth=1).exclude(id__in=list_of_predefined_root_id)
        )
        #=root.id).exclude(id=other_root.id).exclude(id=rootScales.id))

    else:
        # move non-root keyword at root level, with the exception of descendants of the predefined roots
        map((lambda x: HierarchicalKeyword.objects.get(id=x).
             move(HierarchicalKeyword.get_last_root_node(), "sorted-sibling")),
            [h.id for h in HierarchicalKeyword.objects.exclude(id__in=predefined_roots_and_descendants_id)])
        #[h.id for h in HierarchicalKeyword.objects.exclude(id__in=[rid.id for rid in HierarchicalKeyword.get_root_nodes()])])

        HierarchicalKeyword.fix_tree()

        # put all HierarchicalKeyword tree nodes under other_root
        map((lambda x: HierarchicalKeyword.objects.get(id=x.id).
             move(HierarchicalKeyword.objects.get(id=other_root.id), "sorted-child")),
            HierarchicalKeyword.objects.filter(depth=1).exclude(id__in=predefined_roots_and_descendants_id))
            #    HierarchicalKeyword.objects.filter(depth=1).exclude(id=root.id).exclude(id=other_root.id).exclude(id=rootScales.id))

    # TODO: needs optimization
    #move all tellme glossary kewyords under "root" node
    for k in g.keywords.items():
        gk = k[1]  # gk is a 2-ple (id,TELLmeKeyword)

        # get the corresponding HierarchicalKeyword (existing or new) after
        # having moved it under root node
        hgk = gk.toHierarchicalKeywordChildOf(root)
        for c in g.listConceptsByKeyword(gk):
            c.toHierarchicalKeywordChildOf(hgk)  # c is already a TELLmeConcept

    for sca in g.scales.items():
        gsca=sca[1]
        gsca.toHierarchicalKeywordChildOf(rootScales)

    if force:
        # NOTE: we have to obtain again the nodes because references are now obsolete
        root = getOrCreateHierarchicalKeywordRootByName(u"TELLme")
        rootScales = getOrCreateHierarchicalKeywordRootByName(u"TELLme-scales")
        other_root = _getOtherKeywordsRoot()

        # redo in case of force (TELLme keywords and scales are now in proper position under their roots.
        # We can push other remaining keywords under the other_keywords_root.
        predefined_roots_and_descendants_id = list_of_predefined_root_id
        predefined_roots_and_descendants_id.extend([hk.id for hk in root.get_descendants()])
        predefined_roots_and_descendants_id.extend([hk.id for hk in rootScales.get_descendants()])
        predefined_roots_and_descendants_id.extend([hk.id for hk in other_root.get_descendants()])
        # put all HierarchicalKeyword tree nodes under other_root
        map((lambda x: HierarchicalKeyword.objects.get(id=x.id).
             move(HierarchicalKeyword.objects.get(id=other_root.id), "sorted-child")),
            HierarchicalKeyword.objects.filter(depth=1).exclude(id__in=predefined_roots_and_descendants_id))

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
    from geonode.base.models import HierarchicalKeyword
    g = TellMeGlossary()
    #jj=g.jj
    mode="ttl"
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
        dumpTTLGlossaryToStaticDir(g)
        #synchSparqlEndpoint()
        synchGlossaryWithHierarchicalKeywords(g)


#TODO: implement the method.
def synchSparqlEndpoint(endpoint="", user="", password=""):
    import requests

    url = "{endpoint}/update".format(endpoint=os.getenv("TELLME_SPARQL_ENDPOINT", endpoint)
    user=os.getenv("SPARQL_ENDPOINT_USER", user)
    password=os.getenv("SPARQL_ENDPOINT_PASSWORD", password)

    glossaryTTLurl = u"http://{dns}/static/tellme/static/tellme/TELLmeGlossary.ttl".format(dns=os.getenv("GEONODE_LB_HOST_IP"))

    data = {'update': 'DELETE \nwhere{?s ?p ?o}\n\n#'}

    responseDelete = requests.post('endpoint', data=data,
                             auth=('user', 'password'))


    data = {'update': 'LOAD <{glossaryTTLurl}>'.format(glossaryTTLurl = glossaryTTLurl)}

    responseLoad = requests.post('endpoint', data=data,
                             auth=('user', 'password'))

    return responseDelete, responseLoad

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
