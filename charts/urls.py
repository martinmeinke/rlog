from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'charts.views.index'),
    url(r'^live$', 'charts.views.live'),
    url(r'^stats$', 'charts.views.stats'),
    url(r'^liveData$', 'charts.views.liveData'),
)
