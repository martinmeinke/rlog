from django.conf.urls import url, include
from django.views.generic import RedirectView
from django.conf import settings

# Uncomment the next two lines to enable the admin:
if settings.ADMIN_ENABLED:
    from django.contrib import admin
    admin.autodiscover()

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='charts/live')),
    url(r'^charts/', include('charts.urls')),
]

if settings.ADMIN_ENABLED:
    urlpatterns += [
        url(r'^admin/', include(admin.site.urls)),
    ]
