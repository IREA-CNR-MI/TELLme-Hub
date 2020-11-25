from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView

urlpatterns = [
    # overwrite API EdiProxy. The new version will override the mdtools.api one
    # in order to intercept TELLme keywords properly
    #url(r'^ediproxy/(?P<layername>[^/]*)/importmd$', 'geosk.mdtools.api.ediproxy_importmd', name='ediproxy_importmd')l
    url(r'^whoami$', 'geosk.mdtools.views.whoami', name='whoami'),
    url(r'^refresh_glossary_rdf', 'geosk.tellme.api.refresh_glossary_rdf', name='refresh_glossary_rdf'),
    url(r'^synchronizeHierarchicalKeywords_glossary_rdf', 'geosk.tellme.api.synchronizeHierarchicalKeywords_glossary_rdf', name='synchronizeHierarchicalKeywords_glossary_rdf'),
    url(r'^synchronizeNewGlossaryEntries', 'geosk.tellme.api.synchronizeNewGlossaryEntries', name='synchronizeNewGlossaryEntries'),
    url(r'^cleanMissingStyleTitle', 'geosk.tellme.api.cleanMissingStyleTitle', name='cleanMissingStyleTitle'),
    url(r'^delete_non_tellme_hierarchicalKeywords', 'geosk.tellme.api.delete_non_tellme_hierarchicalKeywords',
        name='delete_non_tellme_hierarchicalKeywords'),
    url(r'^set_layerid_conceptid/(?P<layer_id>[^/]*)/(?P<concept_id>[^/]*)','geosk.tellme.api.set_layerid_conceptid',name="set_layerid_conceptid"),
    url(r'^layers/(?P<layername>[^/]*)/set_conceptid/(?P<concept_id>[^/]*)','geosk.tellme.api.set_layername_conceptid',name="set_layername_conceptid"),
    url(r'^maps/(?P<map_id>[^/]*)/set_scale/(?P<sscale>[^/]*)','geosk.tellme.api.set_mapid_scale',name="set_mapid_scale"),
    url(r'^maps/(?P<map_id>[^/]*)/set_protocolid/(?P<protocol_id>[^/]*)','geosk.tellme.api.set_mapid_protocolid',name="set_mapid_protocolid"),

]
