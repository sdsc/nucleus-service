from django.conf.urls import patterns, include, url
import views
from rest_framework.routers import Route, DynamicDetailRoute
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter

class ClusterRouter(SimpleRouter):
    routes = [
        Route(
            url=r'^{prefix}/$',
            mapping={'get': 'list',
            'put':'create'},
            name='{basename}-list',
            initkwargs={'suffix': 'List'}
        ),
        Route(
           url=r'^{prefix}/{lookup}/$',
           mapping={'get': 'retrieve',
            'delete': 'destroy'},
           name='{basename}-detail',
           initkwargs={'suffix': 'Detail'}
        )
    ]

class ComputeRouter(SimpleRouter):
    routes = [
        Route(
           url=r'^{prefix}/{lookup}/$',
           mapping={'get': 'retrieve',
            'delete': 'destroy'},
           name='{basename}-detail',
           initkwargs={'suffix': 'Detail'}
        ),
        DynamicDetailRoute(
            url=r'^{prefix}/{lookup}/{methodname}$',
            name='{basename}-{methodname}',
            initkwargs={}
        )
    ]

class ComputeSetRouter(SimpleRouter):
    routes = [
        Route(
            url=r'^{prefix}/$',
            mapping={'get': 'list',
            'post':'poweron'},
            name='{basename}-list',
            initkwargs={'suffix': 'List'}
        ),
        Route(
           url=r'^{prefix}/{lookup}/$',
           mapping={'get': 'retrieve'},
           name='{basename}-detail',
           initkwargs={'suffix': 'Detail'}
        ),
         DynamicDetailRoute(
            url=r'^{prefix}/{lookup}/{methodname}$',
            name='{basename}-{methodname}',
            initkwargs={}
        )
    ]

class FrontendRouter(NestedSimpleRouter):
    routes = [
        DynamicDetailRoute(
            url=r'^{prefix}/{methodname}$',
            name='{basename}-{methodname}',
            initkwargs={}
        )
    ]

class CallRouter(SimpleRouter):
    routes = [
        Route(
           url=r'^{prefix}/{lookup}/$',
           mapping={'get': 'retrieve'},
           name='{basename}-detail',
           initkwargs={'suffix': 'Detail'}
        ),
        DynamicDetailRoute(
            url=r'^{prefix}/{lookup}/{methodname}$',
            name='{basename}-{methodname}',
            initkwargs={}
        )
    ]


router = ClusterRouter()
router.register(r'^', views.ClusterViewSet, base_name='cluster')

compute_router = ComputeRouter()
compute_router.register(r'^', views.ComputeViewSet, base_name='compute')

computeset_router = ComputeSetRouter()
computeset_router.register(r'^', views.ComputeSetViewSet, base_name='computeset')

frontend_router = FrontendRouter(router, r'^', lookup="frontend")
frontend_router.register(r'frontend', views.FrontendViewSet, base_name='cluster-frontend')

call_router = CallRouter()
call_router.register(r'^', views.CallViewSet, base_name='call')

urlpatterns = patterns(
    'api.views',
    url(r'^accounts', include('django.contrib.auth.urls')),
    url(r'^cluster', include(router.urls)),
    url(r'^compute', include(compute_router.urls)),
    url(r'^cluster', include(frontend_router.urls)),

    url(r'^call', include(call_router.urls)),
    url(r'^computeset', include(computeset_router.urls)),
    #
    # Users
    #
    url(r'^user', views.UserDetailsView.as_view(), name='rest_user_details'),
    #
    # Projects
    #
    url(r'^project', views.ProjectListView.as_view(), name='rest_user_projects')
)


