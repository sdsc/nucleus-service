from django.conf.urls import patterns, include, url
import views
from rest_framework.routers import Route, DynamicDetailRoute
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter

class MainRouter(SimpleRouter):
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
        ),
        DynamicDetailRoute(
            url=r'^{prefix}/{methodname}$',
            name='{basename}-{methodname}',
            initkwargs={}
        )
    ]

class ComputeRouter(NestedSimpleRouter):
    routes = MainRouter.routes

class GroupRouter(NestedSimpleRouter):
    routes = MainRouter.routes

class StorageRouter(NestedSimpleRouter):
    routes = MainRouter.routes

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


router = MainRouter()
router.register(r'^', views.ClusterViewSet, base_name='cluster')

compute_router = ComputeRouter(router, r'^', lookup='compute_id')
compute_router.register(r'compute', views.ComputeViewSet, base_name='cluster-compute')

frontend_router = FrontendRouter(router, r'^')
frontend_router.register(r'frontend', views.FrontendViewSet, base_name='cluster-frontend')

group_router = GroupRouter(router, r'^', lookup='group_id')
group_router.register(r'group', views.GroupViewSet, base_name='cluster-group')

storage_router = StorageRouter(compute_router, r'compute', lookup='storage_id')
storage_router.register(r'storage', views.StorageViewSet, base_name='cluster-compute-storage')

project_router = MainRouter()
project_router.register(r'^', views.ProjectViewSet, base_name='project')

user_router = MainRouter()
user_router.register(r'^', views.UserViewSet, base_name='user')

call_router = CallRouter()
call_router.register(r'^', views.CallViewSet, base_name='call')

urlpatterns = patterns(
    'api.views',
    url(r'^accounts', include('django.contrib.auth.urls')),
    url(r'^cluster', include(router.urls)),
    url(r'^cluster', include(compute_router.urls)),
    url(r'^cluster', include(frontend_router.urls)),
    url(r'^cluster', include(group_router.urls)),
    url(r'^cluster', include(storage_router.urls)),

    url(r'^call', include(call_router.urls)),
    #
    # Users
    #
    url(r'^user', include(user_router.urls)),
    #
    # Projects
    #
    url(r'^project', include(project_router.urls)),
)


