"""
URL configuration for routing project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from django.conf.urls import url
from app import views
# from rest_framework.documentation import include_docs_urls
from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

schema_view = get_schema_view(
   openapi.Info(
      title="测试工程API",
      default_version='v1.0',
      description="测试工程接口文档",
      terms_of_service="https://www.cnblogs.com/jinjiangongzuoshi/",
      contact=openapi.Contact(email="狂师"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('getnewgesture/', views.getLatestsGesture, name='getnewgesture'),
    path('postgestures/', views.postgestures, name='postgestures'),
    path('checkUserValid/', views.checkUserValid, name='checkUserValid'),
    path('checkUserStatus/', views.checkUserStatus, name='checkUserStatus'),
    path('loginUser/', views.loginUser, name='loginUser'),
    path('logoutUser/',views.logoutUser, name='logoutUser'),
    path('postUser/', views.postUser, name='postUser'),
    path('createRoom/', views.createRoom, name='createRoom'),
    path('joinRoom/', views.joinRoom, name='joinRoom'),
    path('quitRoom/', views.quitRoom,name='quitRoom'),
    path('checkRoomNum/',views.checkRoomNum,name='checkRoomNum'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    path('^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # path('swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
]
