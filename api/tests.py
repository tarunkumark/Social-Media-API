from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json, jwt
from datetime import datetime, timedelta
from .models import User, Post, Comment
class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpassword'
        )

    def test_valid_authentication(self):
        # create valid login data
        login_data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post(reverse('authenticate_user'), data=json.dumps(login_data), content_type='application/json')
        # check that response status code is 200 OK
        self.assertEqual(response.status_code, 200)
        # check that the response contains a token
        self.assertIn('token', response.json())

    def test_invalid_authentication(self):
        # create invalid login data
        login_data = {'username': 'testuser', 'password': 'wrongpassword'}
        response = self.client.post(reverse('authenticate_user'), data=json.dumps(login_data), content_type='application/json')
        self.assertEqual(response.status_code, 401)
        # check that the response contains an error message
        self.assertIn('error', response.json())
    


class AllPostsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test1@test.com')
        self.token = jwt.encode({'user_id': self.user.id, 'exp': datetime.utcnow() + timedelta(minutes=30)}, 'secret_key', algorithm='HS256')

    def test_all_posts_positive(self):
        # create some posts for the authenticated user
        post1 = Post.objects.create(title='Test post 1', content='This is test post 1', author=self.user)
        post2 = Post.objects.create(title='Test post 2', content='This is test post 2', author=self.user)

        # make GET request to all_posts endpoint with valid JWT token
        url = reverse('all_posts')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # assert that response status code is 201
        self.assertEqual(response.status_code, 201)

        # assert that response data contains correct number of posts
        self.assertEqual(len(response.json().get('posts')), 2)

        # assert that response data contains correct post data
        self.assertEqual(response.json().get('posts')[1]['id'], post1.id)
        self.assertEqual(response.json().get('posts')[1]['title'], 'Test post 1')
        self.assertEqual(response.json().get('posts')[1]['description'], 'This is test post 1')
        self.assertEqual(response.json().get('posts')[1]['created_at'], post1.created_at.isoformat()[:-9] + 'Z')
        self.assertEqual(response.json().get('posts')[0]['id'], post2.id)
        self.assertEqual(response.json().get('posts')[0]['title'], 'Test post 2')
        self.assertEqual(response.json().get('posts')[0]['description'], 'This is test post 2')
        self.assertEqual(response.json().get('posts')[0]['created_at'], post2.created_at.isoformat()[:-9] + 'Z')

    def test_all_posts_unauthorized(self):
        # make GET request to all_posts endpoint without JWT token
        url = reverse('all_posts')
        response = self.client.get(url)

        # assert that response status code is 401
        self.assertEqual(response.status_code, 401)

        # assert that response data contains error message
        self.assertEqual(response.json().get('error'), 'Unauthorized')

    def test_all_posts_expired_token(self):
        # create expired JWT token
        expired_token = jwt.encode({'user_id': self.user.id, 'exp': datetime.utcnow() - timedelta(minutes=30)}, 'secret_key', algorithm='HS256')

        # make GET request to all_posts endpoint with expired JWT token
        url = reverse('all_posts')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {expired_token}')

        # assert that response status code is 401
        self.assertEqual(response.status_code, 401)



class AddCommentViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test12@test.com')

        # Create a test post
        self.post = Post.objects.create(title='Test Post', content='This is a test post.', author=self.user)

        # Generate JWT token
        self.token = jwt.encode({'user_id': self.user.id}, 'secret_key', algorithm='HS256')

    def test_add_comment_valid(self):
        # Submit a valid comment
        comment_data = {'comment': 'This is a test comment.'}
        response = self.client.post(reverse('add_comment', kwargs={'id': self.post.id}), comment_data, HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Check that the comment was created and the response is valid
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(content='This is a test comment.').exists())

    def test_add_comment_empty(self):
        # Submit an empty comment
        comment_data = {'comment': ''}
        response = self.client.post(reverse('add_comment', kwargs={'id': self.post.id}), comment_data, HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Check that the comment was not created and the response is invalid
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Comment.objects.filter(content='').exists())

    def test_add_comment_unauthenticated(self):
        # Submit a comment without authentication
        comment_data = {'comment': 'This is a test comment.'}
        response = self.client.post(reverse('add_comment', kwargs={'id': self.post.id}), comment_data)

        # Check that the comment was not created and the response is invalid
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Comment.objects.filter(content='This is a test comment.').exists())




class UnlikePostViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test123@test.com')
        self.post = Post.objects.create(author=self.user, title='Test post', content='Test content')
        self.jwt_token = jwt.encode({'user_id': self.user.id}, 'secret_key', algorithm='HS256')
        
    def test_unlike_post_success(self):
        # Like the post first
        self.post.likes.add(self.user)

        # Send the request to unlike the post
        response = self.client.post(reverse('unlike_post', args=[self.post.id]), HTTP_AUTHORIZATION='Bearer ' + self.jwt_token)

        # Check that the response is successful and the post is no longer liked by the user
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.post.likes.filter(id=self.user.id).exists())

    def test_unlike_post_not_liked(self):
        # Send the request to unlike the post without liking it first
        response = self.client.post(reverse('unlike_post', args=[self.post.id]), HTTP_AUTHORIZATION='Bearer ' + self.jwt_token)

        self.assertEqual(response.status_code, 400)


    def test_unlike_post_invalid_token(self):
        # Send the request to unlike the post with an invalid token
        response = self.client.post(reverse('unlike_post', args=[self.post.id]), HTTP_AUTHORIZATION='Bearer invalid_token')

        self.assertEqual(response.status_code, 401)




class LikePostViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test1234@test.com')
        self.post = Post.objects.create(author=self.user, title='Test Post', content='This is a test post.')
        self.jwt_token = jwt.encode({'user_id': self.user.id}, 'secret_key', algorithm='HS256')

    def test_like_post(self):
        url = reverse('like_post', args=[self.post.id])
        response = self.client.post(url, HTTP_AUTHORIZATION=f'Bearer {self.jwt_token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post.likes.count(), 1)

    def test_like_post_already_liked(self):
        self.post.likes.add(self.user)
        url = reverse('like_post', args=[self.post.id])
        response = self.client.post(url, HTTP_AUTHORIZATION=f'Bearer {self.jwt_token}')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.post.likes.count(), 1)

    def test_like_post_invalid_token(self):
        url = reverse('like_post', args=[self.post.id])
        response = self.client.post(url, HTTP_AUTHORIZATION='Bearer invalid_token')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.post.likes.count(), 0)

class DeletePostViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test12345@test.com')
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post',
            author=self.user
        )

    def test_delete_post_by_author(self):
        payload = {
            'user_id': self.user.id
        }
        token = jwt.encode(payload, 'secret_key', algorithm='HS256')
       
        response = self.client.delete(reverse('delete_post', args=[self.post.id]), HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, 200)

    def test_delete_post_by_non_author(self):
        other_user = User.objects.create_user(username='otheruser', password='otherpass',email="test123456@test.com")
        payload = {
            'user_id': other_user.id
        }
        token = jwt.encode(payload, 'secret_key', algorithm='HS256')
       
        response = self.client.delete(reverse('delete_post', args=[self.post.id]), HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, 403)


    def test_delete_nonexistent_post(self):
        payload = {
            'user_id': self.user.id
        }
        token = jwt.encode(payload, 'secret_key', algorithm='HS256')
       
        response = self.client.delete(reverse('delete_post', args=[self.post.id + 1]), HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, 404)



class CreatePostTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test1234567@test.com')
        self.token = jwt.encode({'user_id': self.user.id, 'exp': datetime.utcnow() + timedelta(minutes=60)}, 'secret_key', algorithm='HS256')
        self.headers = {'Authorization': f'Bearer {self.token}'}
        self.url = reverse('create_post')
    
    def test_create_post_success(self):
        post_data = {
            'title': 'Test Post',
            'description': 'This is a test post'
        }
        response = self.client.post(self.url, data=json.dumps(post_data), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('title'), post_data['title'])
        self.assertEqual(response.json().get('created_at'), Post.objects.first().created_at.strftime('%Y-%m-%d %H:%M:%S UTC'))
    
    def test_create_post_unauthorized(self):
        self.token = jwt.encode({'user_id': self.user.id + 1, 'exp': datetime.utcnow() + timedelta(minutes=60)}, 'secret_key', algorithm='HS256')
        self.headers = {'Authorization': f'Bearer {self.token}'}
        post_data = {
            'title': 'Test Post',
            'description': 'This is a test post'
        }
        response = self.client.post(self.url, data=json.dumps(post_data), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get('error'), 'User does not exist')
    
    def test_create_post_missing_data(self):
        post_data = {
            'description': 'This is a test post'
        }
        response = self.client.post(self.url, data=json.dumps(post_data), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('error'), 'Please provide both title and description')



class UnfollowUserTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # create two users for testing
        self.user1 = User.objects.create_user(
            username='testuser1', password='testpass1',email='test1@test.com')
        self.user2 = User.objects.create_user(
            username='testuser2', password='testpass2',email='test2@test.com')

        # user1 follows user2
        self.user1.following.add(self.user2)

        # create a JWT token for user1
        payload = {'user_id': self.user1.id}
        self.token = jwt.encode(payload, 'secret_key', algorithm='HS256')

    def test_unfollow_user_success(self):
        url = reverse('unfollow_user', args=[self.user2.id])
        headers = {'Authorization': f'Bearer {self.token}'}

        response = self.client.post(url, headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': f'You have unfollowed {self.user2.username}!'})

        # check that user1 is not following user2 anymore
        self.assertFalse(self.user1.following.filter(id=self.user2.id).exists())

    def test_unfollow_user_not_following(self):
        url = reverse('unfollow_user', args=[self.user2.id])
        headers = {'Authorization': f'Bearer {self.token}'}

        # user1 already unfollowed user2
        self.user1.following.remove(self.user2)

        response = self.client.post(url, headers=headers)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'You are not following this user'})

        # check that user1 is not following user2
        self.assertFalse(self.user1.following.filter(id=self.user2.id).exists())

    def test_unfollow_user_invalid_token(self):
        url = reverse('unfollow_user', args=[self.user2.id])
        headers = {'Authorization': 'Bearer invalid_token'}

        response = self.client.post(url, headers=headers)

        self.assertEqual(response.status_code, 400)


class FollowUserTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='testuser1', password='testpass',email='test1@test.com')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass',email='test2@test.com')
        self.token = jwt.encode({'user_id': self.user1.id}, 'secret_key', algorithm='HS256')

    def test_follow_user_success(self):
        response = self.client.post(reverse('follow_user',args=[self.user2.id]), HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': f'You are now following {self.user2.username}!'})

    def test_follow_already_following_user(self):
        self.user1.following.add(self.user2)
        response = self.client.post(reverse('follow_user',args=[self.user2.id]), HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Already following this user'})

    def test_follow_nonexistent_user(self):
        response = self.client.post(reverse('follow_user',args=[9999]), HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 404)