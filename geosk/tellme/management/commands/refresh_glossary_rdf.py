import logging
#from django.conf import settings
from django.core.management.base import BaseCommand
#from django.utils.translation import ugettext_noop as _
from geosk.tellme.tellmeGlossaryIntegration import dumpTTLGlossaryToStaticDir
#from geosk.tellme.tellmeGlossaryIntegration import synchGlossaryWithHierarchicalKeywords
from geosk.tellme.tellmeGlossaryIntegration import TellMeGlossary, synchSparqlEndpoint, list_new_entries_from_glossary

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'TELLme Glossary. Update rdf turtle file from remote tellme glossary software'

    def handle(self, *args, **options):
        try:
            nc, nk = list_new_entries_from_glossary()
            if len(nc)+len(nk) > 0:
                g = TellMeGlossary()
                dumpTTLGlossaryToStaticDir(g)
                synchSparqlEndpoint()
        except Exception as e:
            log.error(e.message)
