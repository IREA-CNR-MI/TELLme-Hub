import logging
#from django.conf import settings
from django.core.management.base import BaseCommand
#from django.utils.translation import ugettext_noop as _
from geosk.tellme.tellmeGlossaryIntegration import dumpTTLGlossaryToStaticDir
from geosk.tellme.tellmeGlossaryIntegration import synchGlossaryWithHierarchicalKeywords
from geosk.tellme.tellmeGlossaryIntegration import TellMeGlossary

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'TELLme Glossary. Synch HierarchicalKeywords with remote tellme glossary software'

    def handle(self, *args, **options):
        try:
            g = TellMeGlossary()
            synchGlossaryWithHierarchicalKeywords(g)
        except Exception as e:
            log.error(e.message)
