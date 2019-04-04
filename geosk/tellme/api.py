# coding=utf-8
import sys
import json
import requests
import re
import datetime
from lxml import etree
from email.utils import parseaddr
from owslib.iso import MD_Metadata, CI_ResponsibleParty, util, namespaces
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from geonode.base.models import SpatialRepresentationType, TopicCategory
from geonode.layers.metadata import set_metadata, sniff_date
from geonode.layers.models import Layer
from geonode.layers.views import _resolve_layer, \
    _PERMISSION_MSG_METADATA, layer_detail
from geonode.utils import http_client, _get_basic_auth_info, json_response
from geonode.people.enumerations import ROLE_VALUES
from geonode.people.models import Profile #, Role
from geonode.base.enumerations import ALL_LANGUAGES, \
    HIERARCHY_LEVELS, UPDATE_FREQUENCIES, \
    DEFAULT_SUPPLEMENTAL_INFORMATION, LINK_TYPES

from geosk.skregistration.models import SkRegistration
from geosk.skregistration.views import get_key

from geosk.mdtools.forms import UploadMetadataFileForm
from geosk.mdtools.models import ResponsiblePartyScope, MultiContactRole, \
    SCOPE_VALUES
from geosk import UnregisteredSKException

from geosk.mdtools.api import _post_validate, _get_fileid, \
    get_topic_category, _set_contact_role_scope, EDI_Metadata,\
    get_datetype
from geonode.layers.utils import resolve_regions

def _savelayermd(layer, rndt, ediml, version='1'):
    if ediml:
        fileid = _get_fileid(ediml)
        # new fileid must be equal to the old one
        if layer.mdextension.fileid is not None:
            if int(layer.mdextension.fileid) != int(fileid):
                raise Exception(
                    'New fileid (%s) is different from the old one (%s)' % (fileid, layer.mdextension.fileid))
        layer.mdextension.fileid = fileid

    vals, regions, hkeywordsByURI, keywords = iso2dict(etree.fromstring(rndt))

    errors = _post_validate(vals)
    if len(errors) > 0:
        raise Exception(errors)

    # TODO: (TELLme) we could change here the information flow in
    #  order to query the xml (rndt) and match the TELLme
    #  keywords by ID instead of string.
    #  Example:
    #  we can also inspect MD_Metadata parent class of EDI_Metadata
    #  that already contains keywords2, a list of MD_keywords objects
    #  with several elements parsed from XML.
    #  In alternative we can directly filter the appropriate xml elements
    #  with gmx:Anchor and xlink:href with URIs.
    # from geosk.mdtools.api import EDI_Metadata
    # metadataToExplore=etree.fromstring(rndt)
    # mdata = EDI_Metadata(metadataToExplore)    #
    # mdata.identification.keywords2

    # print >>sys.stderr, 'VALS', vals
    # set taggit keywords
    layer.keywords.clear()
    layer.keywords.add(
        *keywords)  # change this in order to obtain 1-1 mapping between URI of tellme keywords (from sparql) and TELLme-HierarchicalKeywords
    layer.keywords.add(*hkeywordsByURI)  # TODO: check this

    # set model properties
    for (key, value) in vals.items():
        # print >>sys.stderr, key, unicode(value).encode('utf8')
        # EDI_Metadata e MD_Metadata non riesco a leggerlo, inoltre EDI può averlo multiplo mentre GeoNode no
        if key == 'spatial_representation_type':
            value, is_created = SpatialRepresentationType.objects.get_or_create(identifier=value)
        elif key == 'topic_category':
            key = 'category'
            value = TopicCategory.objects.get(identifier=get_topic_category(value.encode('utf8')))
        elif key == 'supplemental_information' and value is None:
            value = ' '
        elif key in ['md_contact', 'citation_contact', 'identification_contact', 'distributor_contact']:
            _set_contact_role_scope(key, value, layer.mdextension)
        setattr(layer, key, value)

    layer.save()

    # save rndt & edi xml
    layer.mdextension.md_language = vals['md_language']
    layer.mdextension.md_date = vals['md_date'] if vals['md_date'] is not None else layer.date
    layer.mdextension.rndt_xml = rndt
    layer.mdextension.ediversion = version
    if ediml:
        layer.mdextension.elements_xml = ediml
    layer.mdextension.save()

    return True


def iso2dict(exml):
    """generate dict of properties from EDI_Metadata (INSPIRE - RNDT)"""

    vals = {}
    regions = []
    keywordsTellMe = []
    keywords = []

    mdata = EDI_Metadata(exml)

    # metadata
    if mdata.identifier is not None:
        vals['uuid'] = mdata.identifier
    vals['md_language'] = mdata.languagecode
    vals['md_date'] = sniff_date(mdata.datestamp) if mdata.datestamp is not None else None

    vals['spatial_representation_type'] = mdata.hierarchy

    if hasattr(mdata, 'identification'):
        #
        if len(mdata.identification.date) > 0:
            vals['date'] = sniff_date(mdata.identification.date[0].date) if mdata.identification.date[0].date is not None else None
            vals['date_type'] = get_datetype(mdata.identification.date[0].type) if mdata.identification.date[0].type is not None else None

        # ci sono problemi nei nella mappatura dei codici delle lingue es. grc e gree per il greco
        if len(mdata.identification.resourcelanguage) > 0:
            vals['language'] = mdata.identification.resourcelanguage[0]

        vals['title'] = mdata.identification.title
        vals['abstract'] = mdata.identification.abstract
        vals['purpose'] = mdata.identification.purpose
        vals['supplemental_information'] = mdata.identification.supplementalinformation if mdata.identification.supplementalinformation is not None else DEFAULT_SUPPLEMENTAL_INFORMATION

        vals['temporal_extent_start'] = mdata.identification.temporalextent_start
        vals['temporal_extent_end'] = mdata.identification.temporalextent_end

        if len(mdata.identification.topiccategory) > 0:
            vals['topic_category'] = get_topic_category(mdata.identification.topiccategory[0])
            vals['topic_category_orig'] = mdata.identification.topiccategory[0]

        if (hasattr(mdata.identification, 'keywords') and
                len(mdata.identification.keywords) > 0):
            for k in mdata.identification.keywords:
                if None not in k['keywords']:
                    if k['type'] == "place":
                        regions.extend(k['keywords'])
                    elif k['thesaurus']['title'] == "http://rdfdata.get-it.it/TELLmeGlossary/":
                        pass # NOTE: current implementation of EDIMetadata does not read gmx:Anchor!!!
                        #keywordsTellMe.extend(k['keywords'])
                    else:
                        keywords.extend(k['keywords'])

        if len(mdata.identification.securityconstraints) > 0:
            vals['constraints_use'] = \
                mdata.identification.securityconstraints[0]
        if len(mdata.identification.otherconstraints) > 0:
            vals['constraints_other'] = \
                mdata.identification.otherconstraints[0]

        vals['purpose'] = mdata.identification.purpose

        citation_contact = []
        for c in mdata.identification.cited:
            c = c.__dict__
            if c['onlineresource'] is not None:
                c['onlineresource'] = c['onlineresource'].__dict__
            citation_contact.append(c)
        vals['citation_contact'] = citation_contact

        md_contact = []
        for c in mdata.contact:
            c = c.__dict__
            if c['onlineresource'] is not None:
                c['onlineresource'] = c['onlineresource'].__dict__
            md_contact.append(c)
        vals['md_contact'] = md_contact

        identification_contact = []
        for c in mdata.identification.contact:
            c = c.__dict__
            if c['onlineresource'] is not None:
                c['onlineresource'] = c['onlineresource'].__dict__
            identification_contact.append(c)
        vals['identification_contact'] = identification_contact

        distributor_contact = []
        if hasattr(mdata.distribution, 'distributor'):
            for d in mdata.distribution.distributor:
                c = d.contact
                c = c.__dict__
                if c['onlineresource'] is not None:
                    c['onlineresource'] = c['onlineresource'].__dict__
                distributor_contact.append(c)
            vals['distributor_contact'] = distributor_contact

    if mdata.dataquality is not None:
        vals['data_quality_statement'] = mdata.dataquality.lineage

    # resolve regions (check if they are among Region model instances
    regions_resolved, regions_unresolved = resolve_regions(regions)
    keywords.extend(regions_unresolved)

    # resolve TELLme keywords. keywordsByURI is a list of HierarchicalKeywords
    tellme_keywords_resolved, tellme_keywords_unresolved = resolveTellmeKeywords(exml)

    return [vals, regions, tellme_keywords_resolved, tellme_keywords_unresolved]


def resolveTellmeKeywords(exml):
    from tellmeGlossaryIntegration import getHierarchicalKeywordListBySlug
    # check the keywordsTellMe list of dict.
    # they are supposed to have [""][""]
    #' returns a list of HierarchicalKeyword
    ns = namespaces
    del(ns[None])
    keywords_resolved = []
    keywords_unresolved = []
    # TODO: check possible issues with non-unicode char
    # k = exml.xpath(u"//gmd:MD_Keywords[.//gmx:Anchor/text()='{k}']".format(k='Airport'.decode('utf-8')), namespaces=ns)
    #xpath=u"//gmd:MD_Keywords[.//gmx:Anchor/text()='{k}']".format(k=k.decode('utf-8'))
    #xpath=u"//gmd:MD_Keywords[.//gmx:Anchor/@xlink:href]"
    xpath = u"//gmd:MD_Keywords//gmx:Anchor/@xlink:href"

    # for KW in exml.xpath(xpath, namespaces=ns):
    #     #print KW.xpath("//gmx:Anchor/@xlink:href",ns)
    #     urllist=KW.xpath("//gmx:Anchor/@xlink:href",ns)
    #     # in the future one could get several keywords within the same MD_Keywords element!
    for u in exml.xpath(xpath, namespaces=ns):
        splitu = u.split("/")
        # in the TellMeHub we have TELLme keyword slugs defined as the last part of the TELLme keywords uri.
        slug = splitu[len(splitu) - 1]
        kl=getHierarchicalKeywordListBySlug(slug)
        if len(kl) > 0:
            keywords_resolved.extend(kl)
        else:
            xpath2 = u"//gmd:MD_Keywords//gmx:Anchor[@xlink:href='{u}']/text()".format(u=u)
            keywords_unresolved.extend(exml.xpath(xpath2, namespaces=ns))

    return keywords_resolved, keywords_unresolved


@login_required
def ediproxy_importmd(request, layername):
    layer = _resolve_layer(request, layername, 'base.change_resourcebase', _PERMISSION_MSG_METADATA)
    isoml = request.POST.get('generatedXml').encode('utf8')
    ediml = request.POST.get('ediml').encode('utf8')
    edimlid = request.POST.get('edimlid')
    try:
        _savelayermd(layer, isoml, ediml, version='2')
    except Exception as e:
        return json_response(exception=e, status=500)
    return json_response(body={'success':True})
