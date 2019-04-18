# coding=utf-8
from lxml import etree
from owslib.iso import MD_Metadata, CI_ResponsibleParty, util, namespaces
from geosk.mdtools.api import _post_validate, _get_fileid, \
    get_topic_category, _set_contact_role_scope, EDI_Metadata,\
    get_datetype
from geonode.layers.models import Layer
from geosk.mdtools.models import MdExtension

def layer2edixml_etree(layer):
    from lxml import etree
    return etree.fromstring(layer.mdextension.rndt_xml_clean)

def print_edixml_from_layer(layer):
    print(etree.tostring(layer2edixml_etree(layer)))

def layer2EDIMetadata(layer):
    return EDI_Metadata(layer2edixml_etree(layer))

def extract_keywords(layer):
    mdata=layer2EDIMetadata(layer)
    return mdata.identification.keywords

def print_layerEDI_section_by_xpath(layer, xpath):
    ns = namespaces
    if None in namespaces:
        del (ns[None])
    exml = layer2edixml_etree(layer)
    for u in exml.xpath(xpath, namespaces=ns):
        print(etree.tostring(u))


