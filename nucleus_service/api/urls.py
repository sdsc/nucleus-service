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

class ComputeRouter(NestedSimpleRouter):
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

class ConsoleRouter(NestedSimpleRouter):
    routes = [
        Route(
           url=r'^{prefix}/$',
           mapping={'get': 'retrieve'},
           name='{basename}-detail',
           initkwargs={'suffix': 'Detail'}
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


router = ClusterRouter()
router.register(r'^', views.ClusterViewSet, base_name='cluster')

compute_router = ComputeRouter(router, r"^", lookup="compute_id")
compute_router.register(r'compute', views.ComputeViewSet, base_name='cluster-compute')

compute_console_router = ConsoleRouter(compute_router, r"compute", lookup="console")
compute_console_router.register(r'console', views.ConsoleViewSet, base_name='cluster-compute-console')

computeset_router = ComputeSetRouter()
computeset_router.register(r'^', views.ComputeSetViewSet, base_name='computeset')

frontend_router = FrontendRouter(router, r'^', lookup="frontend")
frontend_router.register(r'frontend', views.FrontendViewSet, base_name='cluster-frontend')

urlpatterns = patterns(
    'api.views',
    url(r'^accounts', include('django.contrib.auth.urls')),
    url(r'^cluster', include(router.urls)),
    url(r'^cluster', include(compute_router.urls)),
    url(r'^cluster', include(frontend_router.urls)),
    url(r'^cluster', include(compute_console_router.urls)),

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


