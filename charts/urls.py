from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'charts.views.index'),
    url(r'^live$', 'charts.views.live'),
    url(r'^stats/?$', 'django.views.generic.simple.redirect_to', {'url': 'stats/timeframe_mon'}),
    url(r'^stats/(?P<timeframe_url>\w+)/$', 'charts.views.stats'),
    url(r'^overview$', 'charts.views.overview'),
    url(r'^liveData$', 'charts.views.liveData'),
)