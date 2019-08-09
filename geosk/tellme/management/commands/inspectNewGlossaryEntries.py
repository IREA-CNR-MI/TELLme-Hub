import logging
#from django.conf import settings
from django.core.management.base import BaseCommand
#from django.utils.translation import ugettext_noop as _
#from geosk.tellme.tellmeGlossaryIntegration import dumpTTLGlossaryToStaticDir
#from geosk.tellme.tellmeGlossaryIntegration import synchGlossaryWithHierarchicalKeywords
#from geosk.tellme.tellmeGlossaryIntegration import TellMeGlossary
from geosk.tellme.tellmeGlossaryIntegration import list_new_entries_from_glossary

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = """TELLme Glossary. Inspect which new terms have been added to the Glossary software.
            Use the command synchronizeNewGlossaryEntries to insert the 
            corresponding HierarchicalKeywords
            """

    def handle(self, *args, **options):
        try:
            list_new_entries_from_glossary()

        except Exception as e:
            log.error(e.message)
