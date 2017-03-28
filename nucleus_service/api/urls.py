from django.conf.urls import include, url
from rest_framework.routers import Route, DynamicDetailRoute
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter

import views

class ClusterRouter(SimpleRouter):
    routes = [
        Route(
            url=r'^{prefix}/$',
            mapping={'get': 'list',
                     'put': 'create'},
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


class FrontendConsoleRouter(NestedSimpleRouter):
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
                     'post': 'poweron'},
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
        Route(
            url=r'^{prefix}/$',
            mapping={'get': 'retrieve'},
            name='{basename}-detail',
            initkwargs={'suffix': 'Detail'}
        ),
        DynamicDetailRoute(
            url=r'^{prefix}/{methodname}$',
            name='{basename}-{methodname}',
            initkwargs={}
        )
    ]

router = ClusterRouter()
router.register(r'^', views.ClusterViewSet, base_name='cluster')

compute_router = ComputeRouter(router, r"^", lookup="compute_name")
compute_router.register(
    r'compute', views.ComputeViewSet, base_name='cluster-compute')

compute_console_router = ConsoleRouter(
    compute_router, r"compute", lookup="console")
compute_console_router.register(
    r'console', views.ConsoleViewSet, base_name='cluster-compute-console')

computeset_router = ComputeSetRouter()
computeset_router.register(
    r'^', views.ComputeSetViewSet, base_name='computeset')

frontend_router = FrontendRouter(router, r'^', lookup="frontend")
frontend_router.register(
    r'frontend', views.FrontendViewSet, base_name='cluster-frontend')

frontend_console_router = FrontendConsoleRouter(router, r"^", lookup="console")
frontend_console_router.register(
    r'frontend/console', views.FrontendConsoleViewSet, base_name='cluster-console')

urlpatterns = [
    url(r'^accounts', include('django.contrib.auth.urls')),
    url(r'^cluster', include(router.urls)),
    url(r'^cluster', include(compute_router.urls)),
    url(r'^cluster', include(frontend_router.urls)),
    url(r'^cluster', include(compute_console_router.urls)),
    url(r'^cluster', include(frontend_console_router.urls)),

    url(r'^computeset', include(computeset_router.urls)),
    #
    # Users
    #
    url(r'^user', views.UserDetailsView.as_view(), name='rest_user_details'),
    #
    # Projects
    #
    url(r'^project', views.ProjectListView.as_view(), name='rest_user_projects'),
    url(r'^image', views.ImageUploadView.as_view(), name='rest_images')
]
