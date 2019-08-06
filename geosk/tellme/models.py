from geonode.layers.models import Layer
from geonode.maps.models import Map, MapLayer


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

    l_set = set(Layer.objects.filter(alternate__in={l.layer_title for l in m.layers if l.group != 'background'}))
    lista = []

    for l in l_set:
        lista.extend(l.keywords.all())


    k_set = set(lista)

    #[(k.slug, k.name) for k in k_set if (k.get_root()).name == 'TELLme']

    #[(k.get_parent().name, k.name) for k in k_set if (k.get_root()).name == 'TELLme']
    tellme_keywords = {}
    for kc in [(k.get_parent().name, k.name) for k in k_set if (k.get_root()).name == 'TELLme']:
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

    # Here I am simplifying the selection, using the naming convention for tellme-related-concepts slugs.
    #  This can be changed with the commented code block below, which uses the hierarchy imposed
    #  to HierarchicalKeywords containing tellme concepts.
    array_title_concepts = [{la.title: [k.name for k in la.keywords.filter(slug__icontains="concept_")]} for la in
                Layer.objects.filter(alternate__in={l.layer_title for l in m.layers if l.group != 'background'})]

    #array_title_concepts = [{la.title: [k.name for k in la.keywords.all() if (k.get_root()).name == 'TELLme']} for la in
    #                        Layer.objects.filter(
    #                           alternate__in={l.layer_title for l in m.layers if l.group != 'background'})]

    for el in array_title_concepts:
        dictionary_title_concepts.update(el)

    return dictionary_title_concepts


def panel_concept_selection_html(self, ul1_tag="ul", ul2_tag="ul", li1_tag="li", li2_tag="li"):
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

    tellme_keywords=self.get_associated_tellme_relatedConcepts()

    out=u"<{ul1}>"
    kul=u"<{li1}>{k}</{li1}><{ul2}>{c_lis}</{ul2}>"
    for k in tellme_keywords:
        c_lis = u""
        for c in tellme_keywords[k]:
            c_lis += u"<{li2} class='conceptToggle active' id='{c}'>{c}</{li2}>"\
                .format(c=c, li2=li2_tag)
        out += kul.format(k=k, c_lis=c_lis, ul2=ul2_tag,
                          li1=li1_tag)
    out += u"</{ul1}>"
    return out.format(ul1=ul1_tag)


def panel_concept_selection_js(self):
    """
    Returns a <script> element with the jQuery logics to set the onclick events of the li items
    produced by the function panel_concept_selection_html.
    The events do the following: select all the checkboxes of the map view page specifying a class
    named as the id of the clicked li (that will be the name of a tellme related concept).
    :param self:
    :return: html/javascript (string)
    """
    outjs=u"""<script language="text/javascript">
    $(".conceptToggle").on("click", function() {
        if($(this).hasClass("active")){
            //disable all layers related to this concept: select the active ones and click them
            $("."+self.id).filter(function(idx){return $(this).prop("checked")}).click();
        }
        else{
            //enable all layers that are not "checked"
            $("."+self.id).filter(function(idx){return $(this).prop("checked")===false}).click();
        }
        //then toggle the active class on this concept toggle
        self.toggleClass("active");
    })
    </script>
    """
    return outjs


Map.get_associated_tellme_relatedConcepts = get_associated_tellme_relatedConcepts
Map.dict_layer_title_2_tellme_concepts = dict_layer_title_2_tellme_concepts
Map.panel_concept_selection_html = panel_concept_selection_html
Map.panel_concept_selection_js = panel_concept_selection_js