import logging
#from django.conf import settings
from django.core.management.base import BaseCommand
#from django.utils.translation import ugettext_noop as _
from geosk.tellme.tellmeGlossaryIntegration import dumpTTLGlossaryToStaticDir
#from geosk.tellme.tellmeGlossaryIntegration import synchGlossaryWithHierarchicalKeywords
from geosk.tellme.tellmeGlossaryIntegration import TellMeGlossary

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'TELLme Glossary. Update rdf turtle file from remote tellme glossary software'

    def handle(self, *args, **options):
        try:
            g = TellMeGlossary()
            dumpTTLGlossaryToStaticDir(g)
        except Exception as e:
            log.error(e.message)
