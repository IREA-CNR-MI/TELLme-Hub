import logging
#from django.conf import settings
from django.core.management.base import BaseCommand
from geonode.services.models import Service
from geonode.services.views import _register_indexed_layers

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'TELLmeGeoserverGlobal. Update layers with new ones'

    def handle(self, *args, **options):
        try:
            # service=Service.objects.all()[1] # in questo caso  <Service: TELLmeGeoserverGlobal>
            service = Service.objects.get(title="TELLmeGeoserverGlobal")
            _register_indexed_layers(service, verbosity=True)
        except Exception as e:
            log.error(e.message)
