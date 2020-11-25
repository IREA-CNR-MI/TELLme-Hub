from geonode.layers.models import Layer
from geonode.maps.models import Map, MapLayer
from geonode.base.models import TopicCategory
from tellmeGlossaryIntegration import TELLME_SCHEME

def getTellMeGlossaryProtocol(self):
    pass

def isCategory_validSemanticPackage(topicCategory):
    sp=topicCategory
    valid_semantic_package_prefixes = ["protocol_", "package_", "dynamic_"]
    if(sp):
        return any([prefix in sp.identifier for prefix in valid_semantic_package_prefixes])
    else:
        return False


def semanticPackageUrl(self):
    m=self
    sp=m.category
    if isCategory_validSemanticPackage(sp):
        return TELLME_SCHEME+sp.identifier
    else:
        return None

def semanticPackageName(self):
    m = self
    sp = m.category
    if isCategory_validSemanticPackage(sp):
        return sp.description
    else:
        return None




def get_associated_tellme_relatedConcepts(self):
    """
    Returns a dictionary with all the tellme keywords and related concepts associated to this map
    via the presence of a layer with the corresponding HierarchicalKeyword.
    {
        <keyword1>:[relatedConcept_1_1, ..., relatedConcept_1_H],
        ...
        <keywordN>:[relatedConcept_N_1, ..., ..., relatedConcept_N_K]
    }
    :param self:
    :return:
    """
    maplayers=self.layers
    m=self

    #l_set = set(Layer.objects.filter(alternate__in={l.layer_title for l in m.layers if l.group != 'background'}))
    #---- NOT IN GIT --- Sovrascrivere questo con eventuale nuova versione dopo un revert di questo file
    l_set = set(Layer.objects.filter(title__in={l.layer_title for l in m.layers if l.group != 'background'})).union(
        set(Layer.objects.filter(alternate__in={l.layer_title for l in m.layers if l.group != 'background'})))
    #----
    lista = []

    for l in l_set:
        lista.extend(l.keywords.all())


    k_set = set(lista)

    #[(k.slug, k.name) for k in k_set if (k.get_root()).name == 'TELLme']

    #[(k.get_parent().name, k.name) for k in k_set if (k.get_root()).name == 'TELLme']
    tellme_keywords = {}
    for kc in [(k.get_parent().name, k.name) for k in k_set if k.get_parent() and (k.get_root()).name == 'TELLme']:
        if kc[0] not in tellme_keywords.keys():
            tellme_keywords[kc[0]] = []
        tellme_keywords[kc[0]].append(kc[1])

    ''' example usage 
    
    for k in tellme_keywords:
        print(k)
        for c in tellme_keywords[k]:
            print("  " + c)
            
    '''
    return tellme_keywords


def dict_layer_title_2_tellme_concepts(self):
    """
    Returns a dictionary mapping each map-layer title into the corresponding list of
    tellme concepts:
    {
        <layer_1_title>:[<rcA>,<rcB>,...,<rcN>],
        ...,
        <layer_M_title>:[<rcAM>,...,<rcN>]
    }
    :param self:
    :return: dictionary
    """
    m = self
    dictionary_title_concepts={}

    #---- NOT IN GIT --- Sovrascrivere questo con eventuale nuova versione dopo un revert di questo file
    l_set = set(Layer.objects.filter(title__in={l.layer_title for l in m.layers if l.group != 'background'})).union(
        set(Layer.objects.filter(alternate__in={l.layer_title for l in m.layers if l.group != 'background'})))
    #-----
    # Here I am simplifying the selection, using the naming convention for tellme-related-concepts slugs.
    #  This can be changed with the commented code block below, which uses the hierarchy imposed
    #  to HierarchicalKeywords containing tellme concepts.
    #array_title_concepts = [{la.alternate: [k.name for k in la.keywords.filter(slug__icontains="concept_")]} for la in
    #            Layer.objects.filter(alternate__in={l.layer_title for l in m.layers if l.group != 'background'})]

    array_title_concepts = [{la.alternate: [k.name for k in la.keywords.filter(slug__icontains="concept_")]} for la in l_set]



    #array_title_concepts = [{la.title: [k.name for k in la.keywords.all() if (k.get_root()).name == 'TELLme']} for la in
    #                        Layer.objects.filter(
    #                           alternate__in={l.layer_title for l in m.layers if l.group != 'background'})]

    for el in array_title_concepts:
        dictionary_title_concepts.update(el)

    return dictionary_title_concepts


def panel_concept_selection_html(self, ul1_tag="ul", ul2_tag="ul", li1_tag="li", li2_tag="li", separate_lod_link=True):
    """
    Returns an html chunk containing a nested structure (defaults to an ul list) with
    all the tellme keywords and concepts associated to this map.
    The inner li elements have the classes "conceptToggle" and "active". Their ids are
    tellme related concepts names.
    NOTE: To be used with the panel_concept_selection_js function to set the inner js element onclick events.
    :param self:
    :param ul1_tag: (ul)
    :param ul2_tag: (ul)
    :param li1_tag: (li)
    :param li2_tag: (li)
    :return: html (string)
    """
    from geonode.base.models import HierarchicalKeyword

    tellme_keywords=self.get_associated_tellme_relatedConcepts()

    out=u"<{ul1} id='ul_tellme_semantics'>"
    kul=u"<{li1} class='li_tellme_keyword'>{k}</{li1}><{ul2} class='ul_tellme_concepts'>{c_lis}</{ul2}>"

    for k in tellme_keywords:
        #kk=k+URItagfromHKName(k)
        kk = URItagfromHKName(k, separate_lod_link)
        c_lis = u""
        for c in tellme_keywords[k]:
            #cc = c+URItagfromHKName(c)
            cc = URItagfromHKName(c, separate_lod_link)
            c_lis += u"<{li2} class='conceptToggle active' id='{c}'>{cc}</{li2}>"\
                .format(c=c, cc=cc, li2=li2_tag)
        out += kul.format(k=kk, c_lis=c_lis, ul2=ul2_tag,
                          li1=li1_tag)
    out += u"</{ul1}>"
    return out.format(ul1=ul1_tag)

def panel_concept_selection_html_linkTheLabels(self):
    return self.panel_concept_selection_html(separate_lod_link=False)


def slugFromHKName(kname):
    from geonode.base.models import HierarchicalKeyword
    kslug=""
    try:
        kslug = [k for k in HierarchicalKeyword.objects.filter(name=kname) if (k.get_root()).name == 'TELLme'][0].slug
    except Exception as e:
        pass
    return kslug


def URItagfromHKName(kname, separate_lod_link=True):
    slug=slugFromHKName(kname)
    uripattern=u"http://rdfdata.get-it.it/TELLmeGlossary/{slug}"
    if(separate_lod_link):
        uritag = u"{label}<a href='{uri}' target='blank'>(^^)</a>"
    else:
        uritag = u"<a href='{uri}' target='blank'>{label}</a>"
    retpattern = uritag.format(uri=uripattern, label=kname)
    if (slug == ""):
        return kname
    else:
        return retpattern.format(slug=slug)


# def panel_concept_selection_js(self):
#     """
#     Returns a javascript code chunk with the jQuery logics to set the onclick events of the li items
#     produced by the function panel_concept_selection_html.
#     The events do the following: select all the checkboxes of the map view page specifying a class
#     named as the id of the clicked li (that will be the name of a tellme related concept).
#     :param self:
#     :return: html/javascript (string)
#     """
#     outjs=u"""
#     $(".conceptToggle").on("click", function() {
#         if($(this).hasClass("active")){
#             //disable all layers related to this concept: select the active ones and click them
#             $("."+self.id).filter(function(idx){return $(this).prop("checked")}).click();
#         }
#         else{
#             //enable all layers that are not "checked"
#             $("."+self.id).filter(function(idx){return $(this).prop("checked")===false}).click();
#         }
#         //then toggle the active class on this concept toggle
#         self.toggleClass("active");
#     })
#     """
#     return outjs

# override method calling messages causing issues TODO: check cause of issue
def view_count_up(self, user, do_local=True):
    """ increase view counter, if user is not owner and not super
    hacking omonimous Layer method
    :param self:
    :param user:
    :param do_local:
    :return:

    @param user which views layer
    @type User model

    @param do_local - do local counter update even if pubsub is enabled
    @type bool
    """
    if user == self.owner or user.is_superuser:
        return
    if False:
        from geonode.messaging import producer
        producer.viewing_layer(str(user), str(self.owner), self.id)

    else:
        from django.db import models
        Layer.objects.filter(id=self.id) \
            .update(popular_count=models.F('popular_count') + 1)


Layer.view_count_up = view_count_up
Map.get_associated_tellme_relatedConcepts = get_associated_tellme_relatedConcepts
Map.dict_layer_title_2_tellme_concepts = dict_layer_title_2_tellme_concepts
Map.panel_concept_selection_html = panel_concept_selection_html
Map.panel_concept_selection_html_linkTheLabels = panel_concept_selection_html_linkTheLabels
#Map.panel_concept_selection_js = panel_concept_selection_js
Map.semanticPackageUrl = semanticPackageUrl
Map.semanticPackageName = semanticPackageName
