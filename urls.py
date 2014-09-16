from django.conf.urls import patterns, url, include
from django.views.generic import RedirectView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='charts/live')),
    url(r'^charts/', include('charts.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
