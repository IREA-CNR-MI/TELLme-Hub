from django.conf.urls import patterns, url
from django.views.generic import TemplateView

urlpatterns = [
    # overwrite API EdiProxy. The new version will override the mdtools.api one
    # in order to intercept TELLme keywords properly
    #url(r'^ediproxy/(?P<layername>[^/]*)/importmd$', 'geosk.mdtools.api.ediproxy_importmd', name='ediproxy_importmd')l
    url(r'^whoami$', 'geosk.mdtools.views.whoami', name='whoami',
]