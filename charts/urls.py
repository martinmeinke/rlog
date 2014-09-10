from django.conf.urls import patterns, url, include
from django.views.generic import RedirectView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'charts.views.index'),
    url(r'^live$', 'charts.views.live'),
    url(r'^stats/?$', RedirectView.as_view(url='stats/timeframe_mon')),
    url(r'^stats/(?P<timeframe_url>\w+)/$', 'charts.views.stats'),
    url(r'^overview$', 'charts.views.overview'),
    url(r'^liveData$', 'charts.views.liveData'),
)
