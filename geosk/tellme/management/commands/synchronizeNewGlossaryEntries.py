import logging
#from django.conf import settings
from django.core.management.base import BaseCommand
#from django.utils.translation import ugettext_noop as _
#from geosk.tellme.tellmeGlossaryIntegration import dumpTTLGlossaryToStaticDir
#from geosk.tellme.tellmeGlossaryIntegration import synchGlossaryWithHierarchicalKeywords
#from geosk.tellme.tellmeGlossaryIntegration import TellMeGlossary
from geosk.tellme.tellmeGlossaryIntegration import synchNewKeywordsFromTELLmeGlossary, delete_non_tellme_hierarchicalKeywords

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'TELLme Glossary. Synch HierarchicalKeywords only with new terms in tellme glossary software and delete all non-tellme hierarchical keywords'

    def handle(self, *args, **options):
        try:
            delete_non_tellme_hierarchicalKeywords()
            synchNewKeywordsFromTELLmeGlossary()

        except Exception as e:
            log.error(e.message)
