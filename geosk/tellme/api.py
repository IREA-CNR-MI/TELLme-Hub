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

from django.contrib.auth.decorators import user_passes_test

from geosk.tellme.tellmeGlossaryIntegration import \
    TellMeGlossary, dumpTTLGlossaryToStaticDir, synchGlossaryWithHierarchicalKeywords, \
    move_genericHK_level1_under_otherkeywords_branch, synchNewKeywordsFromTELLmeGlossary



from geonode.maps import urls
def _savelayermd(layer, rndt, ediml, version='1'):
    """
    Save layer metadata from ISO/XML file.
    Analogous to the geosk omonimuos version, this method receives a geonode layer class instance
    and sets its attributes. In the TELLme case the method distinguish keywords by URIs of
    TELLme glossary RDF thesaurus and possible keywords of type=places (exploiting gmx ISO XSD)
    :param layer: (Layer)
    :param rndt: (string) ISO/XML MD file
    :param ediml: (string) EDI XML file
    :param version: (string) Only version '2' is managed by this method. Default value '1' is maintained for retrocompatibility solely.
    :return: (bool) True
    """
    if ediml:
        fileid = _get_fileid(ediml)
        # new fileid must be equal to the old one
        if layer.mdextension.fileid is not None:
            if int(layer.mdextension.fileid) != int(fileid):
                raise Exception(
                    'New fileid (%s) is different from the old one (%s)' % (fileid, layer.mdextension.fileid))
        layer.mdextension.fileid = fileid

    vals, regions, hkeywordsByURI, keywords, tellme_scales = iso2dict(etree.fromstring(rndt))

    errors = _post_validate(vals)
    if len(errors) > 0:
        raise Exception(errors)

    ''' note: (TELLme) we change here the information flow in
    #  order to query the xml (rndt) and match the TELLme
    #  keywords by ID instead of string.
    #  Example:
    #    from geosk.mdtools.api import EDI_Metadata
    #    metadataToExplore=etree.fromstring(rndt)
    #    mdata = EDI_Metadata(metadataToExplore)    #
    #    mdata.identification.keywords2   
    #  it is not possibile to inspect any MD_Metadata parent class 
    #  because, even if, there is information about originating thesaurus of the 
    #  keyword in EDI_Metadata, in the owslib version of ISO metadata class 
    #  the xlink:href in gmx:Anchor elements (substituting the literal strings) 
    #  are not managed.
    #  In alternative we directly filter the appropriate xml elements
    #  with gmx:Anchor and xlink:href with URIs.
    '''

    # print >>sys.stderr, 'VALS', vals
    # set taggit keywords
    layer.keywords.clear()
    ''' the first keywords are generic ones. In the case of TELLme profile 
    they could not appear at all, but the call is maintained for possibile 
    future updates of the profile and the EDI template'''
    layer.keywords.add(
        *keywords)  # change this in order to obtain 1-1 mapping between URI of tellme keywords (from sparql) and TELLme-HierarchicalKeywords
    layer.keywords.add(*hkeywordsByURI)  #
    '''
    NOTE: hkeywords can be HierarchicalKeyword instances or string. The invoked method add of the HierarchicalKeywordManager class
    will take care to properly manage them.
    '''

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
            # TODO: issue in the following statement if:
            #  1. email already exists for a username != the same email
            #  2. email longer than 30 characters - the following method in geosk.mdtools.api tries to create a new
            #     user Profile using the email in the username field (whose length is limited).
            #  Possible solutions indicated in mdtools.api._get_or_create_profile() T.B.D.
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

    # clean the hierarchicalKeywords tree from generic keywords, pushing them under the z_other_keywords branch
    move_genericHK_level1_under_otherkeywords_branch(keywords)

    return True


def iso2dict(exml):
    """
    generate dict of properties from EDI_Metadata (INSPIRE - RNDT)
    :param exml:
    :return:
    """

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

            tellme_scales = []

            #    [kl.split() for kl in k['keywords'] for k in mdata.identification.keywords if k['type'] == 'metropolitanscale'][0]

            for k in mdata.identification.keywords:
                if None not in k['keywords']:
                    if k['type'] == "place":
                        regions.extend(k['keywords'])
                    elif k['type'] == "metropolitanscale":
                        tellme_scales.extend(k['keywords'][0].split(" "))
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
    tellme_keywords_resolved, tellme_keywords_unresolved = resolveTellmeKeywords(exml, tellme_scales)

    tellme_keywords_unresolved.extend(keywords)

    return [vals, regions, tellme_keywords_resolved, tellme_keywords_unresolved, tellme_scales]


def resolveTellmeKeywords(exml, tellme_scales):
    """
    we directly filter the appropriate xml elements
    with gmx:Anchor and xlink:href with URIs.
    :param exml:
    :return:
    """
    from tellmeGlossaryIntegration import getHierarchicalKeywordListBySlug
    # check the keywordsTellMe list of dict.
    # they are supposed to have [""][""]
    #' returns a list of HierarchicalKeyword
    ns = namespaces
    if None in namespaces:
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
        kl = getHierarchicalKeywordListBySlug(slug)
        if len(kl) > 0:
            keywords_resolved.extend(kl)
        else:
            xpath2 = u"//gmd:MD_Keywords//gmx:Anchor[@xlink:href='{u}']/text()".format(u=u)
            keywords_unresolved.extend(exml.xpath(xpath2, namespaces=ns))


    for sca in tellme_scales:
        hksca = getHierarchicalKeywordListBySlug("scale_{scale}".format(scale=sca))
        if len(hksca) > 0:
            keywords_resolved.extend(hksca)
        else:
            keywords_unresolved.append(sca) # NOTE: passing a string to extend makes the string
            # interpreted as a list of characters, resulting in each character as an element.

    keywords_unresolved = list(set(keywords_unresolved))

    return keywords_resolved, keywords_unresolved


@login_required
def ediproxy_importmd(request, layername):
    """
    Override the omonimuos method in geosk in order to intercept TELLme Keywords from
    the ISO-XML TELLme profile produced by EDI server and passed to this API by the
    integration among get-it (geosk) and EDI.
    :param request:
    :param layername:
    :return:
    """
    layer = _resolve_layer(request, layername, 'base.change_resourcebase', _PERMISSION_MSG_METADATA)
    isoml = request.POST.get('generatedXml').encode('utf8')
    ediml = request.POST.get('ediml').encode('utf8')
    edimlid = request.POST.get('edimlid')
    try:
        _savelayermd(layer, isoml, ediml, version='2')
    except Exception as e:
        return json_response(exception=e, status=500, body={'success': False,'answered_by': 'tellme', 'error': e, 'error raised by':'_savelayermd'})
    # try:
    #     pass
    #     # TODO: we must make this call thread safe
    #     #g = TellMeGlossary()
    #     #synchGlossaryWithHierarchicalKeywords(g, force=False)
    # except Exception as e:
    #     return json_response(exception=e, status=500, body={'success': False,'answered_by': 'tellme', 'error': e, 'error raised by':'synchGlossaryWithHierarchicalKeywords'})
    return json_response(body={'success': True, 'answered_by': 'tellme'})


@user_passes_test(lambda u: u.is_superuser)
def refresh_glossary_rdf(request):
    try:
        g = TellMeGlossary()
        dumpTTLGlossaryToStaticDir(g)
    except Exception as e:
        return json_response(exception=e, status=500)
    return json_response(body={'success': True, 'answered_by': 'tellme.api.refresh_glossary_rdf'})

@user_passes_test(lambda u: u.is_superuser)
def synchronizeHierarchicalKeywords_glossary_rdf(request):
    try:
        g = TellMeGlossary()
        synchGlossaryWithHierarchicalKeywords(g)
    except Exception as e:
        return json_response(exception=e, status=500)
    return json_response(body={'success': True, 'answered_by': 'tellme.api.synchronizeHierarchicalKeywords_glossary_rdf'})

@user_passes_test(lambda u: u.is_superuser)
def synchronizeNewGlossaryEntries(request):
    try:
        synchNewKeywordsFromTELLmeGlossary()
    except Exception as e:
        return json_response(exception=e, status=500)
    return json_response(body={'success': True, 'answered_by': 'tellme.api.synchronizeHierarchicalKeywords_newFromTELLmeGlossary'})

# CHECK - 20200701 manually imported (paolo): uploaded this version to tellmehub, along with corresponding urls.py and test it through VLab api calls
@user_passes_test(lambda u: u.is_superuser)
def set_layerid_conceptid(request, layer_id, concept_id):
    from geonode.base.models import HierarchicalKeyword
    from geonode.layers.models import Layer
    concept_slug=u"concept_{id}".format(id=concept_id.__str__())

    if (Layer.objects.filter(id=layer_id).exists() and
        HierarchicalKeyword.objects.filter(slug=concept_slug).exists()):
        layer=Layer.objects.get(id=layer_id)
        hk = HierarchicalKeyword.objects.get(slug=concept_slug)
        layer.keywords.clear()
        layer.keywords.add(hk)
        return json_response(body={'success': True, 'layer_id': layer_id, 'layername ': layer.name, 'keyword': layer.keywords})
    else:
        return json_response(body={'success': False, 'layer_id': layer_id})


@user_passes_test(lambda u: u.is_superuser)
def set_layername_conceptid(request, layername, concept_id):
    from geonode.layers.models import Layer
    from geonode.layers.views import _resolve_layer, \
        _PERMISSION_MSG_METADATA, layer_detail

    layer = _resolve_layer(request, layername, 'layers.change_layer', _PERMISSION_MSG_METADATA)

    return set_layerid_conceptid(request, layer.id, concept_id)


@user_passes_test(lambda u: u.is_superuser)
def set_mapid_scale(request, map_id, sscale):
    from geonode.maps.models import Map
    from geonode.base.models import HierarchicalKeyword
    slug = u"scale_{sscale}".format(sscale=sscale.__str__())

    if (Map.objects.filter(id=map_id).exists() and
        HierarchicalKeyword.objects.filter(slug=slug).exists()):

        m = Map.objects.get(id=map_id)
        hk = HierarchicalKeyword.objects.get(slug=slug)
        m.keywords.clear()
        m.keywords.add(hk)
        return json_response(body={'success': True, 'layer_id': map_id, 'map_title ': m.title, 'keyword': slug})

    else:
        return json_response(body={'success': False, 'map_id': map_id})


