from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	url(r'^$', 'django.views.generic.simple.redirect_to', {'url': 'charts/live'}),
    url(r'^charts/', include('charts.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
