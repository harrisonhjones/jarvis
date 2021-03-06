from django.conf.urls.defaults import *
from django.http import HttpResponseRedirect
from django.views.generic.simple import direct_to_template

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^login/$', 'jarvis_web.door_control.views.login', name='login'),
    url(r'^logout/$', 'jarvis_web.door_control.views.logout', name='logout'),
    (r'^door/', include('jarvis_web.door_control.urls')),
    (r'^robots.txt', direct_to_template, { 'template': 'robots.txt' }),
    (r'^$', lambda request: HttpResponseRedirect('/door')),
    # Example:
    # (r'^jarvis_web/', include('jarvis_web.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
