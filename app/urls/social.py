from django.urls import path
from app.views.social import (
    social_home, upload_post, like_post,
    add_comment, edit_comment, delete_comment,
    edit_post, delete_post
)

urlpatterns = [
    path("social/", social_home, name="social_home"),
    path("social/upload/", upload_post, name="upload_post"),

    path("social/like/<uuid:id>/", like_post, name="like_post"),

    path("social/comment/<uuid:post_id>/", add_comment, name="add_comment"),
    path("social/comment/edit/<int:comment_id>/", edit_comment, name="edit_comment"),
    path("social/comment/delete/<int:comment_id>/", delete_comment, name="delete_comment"),

    path("social/post/edit/<uuid:post_id>/", edit_post, name="edit_post"),
    path("social/post/delete/<uuid:post_id>/", delete_post, name="delete_post"),
]
