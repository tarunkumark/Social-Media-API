from django.urls import path
from .views import index, authenticate_user, user_profile,follow_user, unfollow_user,\
    create_post,delete_post,like_post,unlike_post,add_comment,all_posts
urlpatterns = [
    path('index/',index),
    path('authenticate/', authenticate_user, name='authenticate_user'),
    path('user/', user_profile, name='user'),
    path('follow/<int:id>', follow_user, name='follow_user'),
    path('unfollow/<int:id>', unfollow_user, name='unfollow_user'),
    path('posts/', create_post, name='create_post'),
    path('posts/<int:id>', delete_post, name='delete_post'),
    path('like/<int:id>', like_post, name='like_post'),
    path('unlike/<int:id>', unlike_post, name='unlike_post'),
    path('comment/<int:id>', add_comment, name='add_comment'),
    path('all_posts/', all_posts, name='all_posts')
]