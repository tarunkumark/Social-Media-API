from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.http import JsonResponse
import jwt
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate

from .models import User,Post,Comment

@csrf_exempt
@require_http_methods(['POST'])
def authenticate_user(request):
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    if username is None or password is None:
        return JsonResponse({'error': 'Please provide both username and password'}, status=400)
    user = authenticate(username=username, password=password)
    if user is None:
        return JsonResponse({'error': 'Invalid email or password'}, status=401)
    token = jwt.encode({'user_id':user.id, 'username': username}, 'secret_key', algorithm='HS256')
    return JsonResponse({'token': token})

@csrf_exempt
@require_http_methods(['GET'])
def user_profile(request):
    
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        decoded_token = jwt.decode(token, 'secret_key', algorithms=['HS256'])
    except:
        return JsonResponse({'error': 'Please provide a valid token'}, status=400)
    user_id = decoded_token['user_id']
    user = User.objects.get(id=user_id)
    followers_count = user.followers.count()
    following_count = user.following.count()
    return JsonResponse({
        'username': user.username,
        'followers_count': followers_count,
        'following_count': following_count
    })

@csrf_exempt
@require_http_methods(['POST'])
def follow_user(request, id):
    # Retrieve the JWT token from the request headers
   
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        decoded_token = jwt.decode(token, 'secret_key', algorithms=['HS256'])
    except:
        return JsonResponse({'error': 'Please provide a valid token'}, status=400)
    user_id = decoded_token['user_id']


    try:
        follower = User.objects.get(id=user_id)
        following = User.objects.get(id=id)
    except:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    if follower == None or following == None:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    # Check if the follower is already following the user
    if follower.following.filter(id=id).exists():
        return JsonResponse({'error': 'Already following this user'}, status=400)

    # Follow the user and save the follower object
    follower.following.add(following)
    follower.save()

    return JsonResponse({'success': f'You are now following {following.username}!'})

@csrf_exempt
@require_http_methods(['POST'])
def unfollow_user(request, id):
    # Retrieve the JWT token from the request headers
   
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        decoded_token = jwt.decode(token, 'secret_key', algorithms=['HS256'])
    except:
        return JsonResponse({'error': 'Please provide a valid token'}, status=400)
    user_id = decoded_token['user_id']

    # Retrieve the user who is unfollowing and the user who is being unfollowed
    unfollower = User.objects.get(id=user_id)
    unfollowing = User.objects.get(id=id)

    # Check if the unfollower is not following the user
    if not unfollower.following.filter(id=id).exists():
        return JsonResponse({'error': 'You are not following this user'}, status=400)

    # Unfollow the user and save the unfollower object
    unfollower.following.remove(unfollowing)
    unfollower.save()

    return JsonResponse({'success': f'You have unfollowed {unfollowing.username}!'})

@csrf_exempt
@require_http_methods(['POST'])
def create_post(request):
    # Retrieve the JWT token from the request headers
    
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        decoded_token = jwt.decode(token, 'secret_key', algorithms=['HS256'])
    except:
        return JsonResponse({'error': 'Please provide a valid token'}, status=400)
    user_id = decoded_token['user_id']

    # Retrieve the authenticated user
    try:
        author = User.objects.get(id=user_id)
    except:
        return JsonResponse({'error': 'User does not exist'}, status=404)

    # Retrieve the post data from the request body
    data = json.loads(request.body)
    title = data.get('title')
    content = data.get('description')
    if title is None or content is None:
        return JsonResponse({'error': 'Please provide both title and description'}, status=400)
    # Create the post and save it
    post = Post.objects.create(title=title, content=content, author=author)

    # Return the post data
    response_data = {
        'id': post.id,
        'title': post.title,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
    }
    return JsonResponse(response_data)

@csrf_exempt
@require_http_methods(['DELETE','GET'])
def delete_post(request, id):
    # Retrieve the JWT token from the request headers
    if request.method == 'GET':
        
        post = get_object_or_404(Post, id=id)
        data = {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'author': post.author.username,
        'created_at': post.created_at,
        'updated_at': post.updated_at,
        'likes_count': post.likes.count(),
        'comments': list(post.comments.annotate(like_count=Count('likes')).values('id', 'author__username', 'content', 'created_at', 'like_count')),
    }
        return JsonResponse(data)

    try:
        token = request.headers.get('Authorization').split(' ')[1]
        decoded_token = jwt.decode(token, 'secret_key', algorithms=['HS256'])
    except:
        return JsonResponse({'error': 'Please provide a valid token'}, status=400)

    user_id = decoded_token['user_id']

    # Retrieve the post and check if the authenticated user is the author
    try:
        post = Post.objects.get(id=id)
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post does not exist'}, status=404)

    if post.author.id != user_id:
        return JsonResponse({'error': 'You are not authorized to delete this post'}, status=403)

    # Delete the post and return a success message
    post.delete()
    return JsonResponse({'success': 'Post deleted successfully'})

@csrf_exempt
@require_http_methods(['POST'])
def like_post(request, id):
    # Retrieve the JWT token from the request headers
    
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        decoded_token = jwt.decode(token, 'secret_key', algorithms=['HS256'])
    except:
        return JsonResponse({'error': 'Please provide a valid token'}, status=400)
    user_id = decoded_token['user_id']

    # Retrieve the post to be liked and the user liking the post
    post = Post.objects.get(id=id)
    user = User.objects.get(id=user_id)

    # Check if the user has already liked the post
    if post.likes.filter(id=user_id).exists():
        return JsonResponse({'error': 'Already liked this post'}, status=400)

    # Like the post and save the user object
    post.likes.add(user)
    post.save()

    return JsonResponse({
        'post_id': post.id,
        'title': post.title,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'message': f'{user.username} liked this post!'
    })

@csrf_exempt
@require_http_methods(['POST'])
def unlike_post(request, id):
    # Retrieve the JWT token from the request headers
    
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        decoded_token = jwt.decode(token, 'secret_key', algorithms=['HS256'])
    except:
        return JsonResponse({'error': 'Please provide a valid token'}, status=401)
    user_id = decoded_token['user_id']

    # Retrieve the post and user objects
    post = Post.objects.get(id=id)
    user = User.objects.get(id=user_id)

    # Check if the user has already liked the post
    if not post.likes.filter(id=user_id).exists():
        return JsonResponse({'error': 'You have not liked this post yet'}, status=400)

    # Remove the user from the list of users who liked the post
    post.likes.remove(user)

    return JsonResponse({'success': 'Post unliked successfully'})
@csrf_exempt
@require_http_methods(['POST'])
def add_comment(request, id):
    # Retrieve the JWT token from the request headers
    
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        decoded_token = jwt.decode(token, 'secret_key', algorithms=['HS256'])
    except:
        return JsonResponse({'error': 'Please provide a valid token'}, status=401)
    user_id = decoded_token['user_id']

    # Retrieve the post and authenticated user
    post = Post.objects.get(id=id)
    user = User.objects.get(id=user_id)

    # Retrieve comment from the request body
    comment_content = request.POST.get('comment')
    if len(comment_content) == 0 or comment_content.isspace():
        return JsonResponse({'error': 'Please provide a comment'}, status=400)

    # Create the comment and save it to the database
    comment = Comment(post=post, author=user, content=comment_content)
    comment.save()

    # Return the comment id in the response
    return JsonResponse({'comment_id': comment.id})

@csrf_exempt
@require_http_methods(['GET'])
def all_posts(request):
    # Get the JWT token from the request headers
    
    try:
        token = request.headers.get('Authorization').split(' ')[1]
    except:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    # Decode the JWT token to get the user ID
    try:
        decoded_token = jwt.decode(token, 'secret_key', algorithms=['HS256'])
        user_id = decoded_token['user_id']
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token has expired'}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)

    # Get all posts created by the authenticated user, sorted by post time
    posts = Post.objects.filter(author_id=user_id).order_by('-created_at')

    # Serialize the posts and their associated comments and likes
    serialized_posts = []
    for post in posts:
        serialized_post = {
            'id': post.id,
            'title': post.title,
            'description': post.content,
            'created_at': post.created_at,
            'comments': [{'id': comment.id, 'author': comment.author.username, 'content': comment.content, 'created_at': comment.created_at} for comment in post.comments.all()],
            'likes': [{'id': user.id, 'username': user.username} for user in post.likes.all()],
        }
        serialized_posts.append(serialized_post)

    return JsonResponse({'posts': serialized_posts},status=201)


def index():
    return "hello"