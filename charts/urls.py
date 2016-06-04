from django.conf.urls import url
from django.views.generic import RedirectView
from django.conf import settings
from charts import views as chart_views

app_name = 'charts'

# Uncomment the next two lines to enable the admin:
if settings.ADMIN_ENABLED:
    from django.contrib import admin
    admin.autodiscover()

urlpatterns = [
    url(r'^$', chart_views.index, name="index"),
    url(r'^live$', chart_views.live, name="live"),
    url(r'^stats/?$', RedirectView.as_view(url='stats/timeframe_day'), name="stats"),
    url(r'^stats/(?P<timeframe_url>\w+)/$', chart_views.stats, name="stats"),
    url(r'^overview$', chart_views.overview, name="overview"),
    url(r'^liveData$', chart_views.liveData, name="liveData"),
]
