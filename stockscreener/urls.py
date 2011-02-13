from django.conf.urls.defaults import *
import settings
import os.path as os_path

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

"""
Define which URLs we want to handle, and which functions must handle them.

/admin/ is handled by admin.site.root function
/distrgraph/<stock property id>/ is handled by distrgraph in views
.. etc ..
"""
urlpatterns = patterns('',
                       (r'^admin/(.*)', admin.site.root),
                       (r'^distrgraph/(?P<stock_property_id>\d+)/$', 'stockscreener.search.views.distrgraph'),
                       (r'^search/$', 'stockscreener.search.views.index'),
                       (r'^search/criteria/(?P<stock_property_id>\d+)/$', 'stockscreener.search.views.addcriteria'),
                       (r'^search/result/$', 'stockscreener.search.views.getresult'),
                       # Example:
                       # (r'^stockscreener/', include('stockscreener.foo.urls')),
)

# this handles the site_media (taken from Freyr configuration)
if settings.DEBUG:
    urlpatterns += patterns('',
                            (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os_path.join(settings.PROJECT_PATH, 'site_media')}),
    )

