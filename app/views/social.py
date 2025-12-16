from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Post, LikePost, Followers, Comment, Profile, User


@login_required
def social_home(request):
    posts = Post.objects.select_related('user').order_by('-created_at')
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, "app/social_home.html", {"posts": posts, "profile": profile})

@login_required
def like_post(request, id):
    post = get_object_or_404(Post, id=id)
    like, created = LikePost.objects.get_or_create(
        post=post, user=request.user
    )

    if not created:
        like.delete()

    post.no_of_likes = LikePost.objects.filter(post=post).count()
    post.save()

    return redirect("social_home")
