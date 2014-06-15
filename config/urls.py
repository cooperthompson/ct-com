from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', 'soccercal.views.home', name='home'),
                       url(r'^team/(?P<team_id>.+)/$', 'soccercal.views.team', name='team'),
                       url(r'^team/(?P<team_id>.+)/.+.ics$', 'soccercal.views.ics', name='team'),
                       url(r'^league/(?P<league_id>.+)/$', 'soccercal.views.league', name='league'),
                       url(r'^ics/Master.ics', 'soccercal.views.master_ics', name='master_ics'),
                       url(r'^ics/(?P<team_name>.+).ics', 'soccercal.views.ics', name='ics'),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^chaining/', include('smart_selects.urls')),
                       (r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
                       (r'^admin/',  include(admin.site.urls)),  # admin site
)


