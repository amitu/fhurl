import json
from django.test import TestCase


LOGIN_WITH_URL = '/login/with/'
LOGIN_WITHOUT_URL = '/login/without/'
WITH_HTTP_URL = '/with/http/'
WITH_VARIABLE_REDIRECT_URL = '/with/variable/redirect/'


class TestFhurl(TestCase):

    def assertFormHasErrorsForFields(self, response, fields, form='form'):
        self.assertIn(form, response.context)
        form = response.context['form']
        self.assertItemsEqual(form.errors.keys(), fields)
    
    # /login/with/
    def test_login_with_get(self):
        response = self.client.get(LOGIN_WITH_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('login.html')
        self.assertFormHasErrorsForFields(response, [])
        form = response.context['form']
        self.assertItemsEqual(form.errors.keys(), [])

    def test_login_with_post_no_data(self):
        response = self.client.post(LOGIN_WITH_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('login.html')
        self.assertFormHasErrorsForFields(response, ['username', 'password'])

    def test_login_with_post_missing_password(self):
        response = self.client.post(LOGIN_WITH_URL, {'username': 'john'})
        self.assertEqual(response.status_code, 200)
        self.assertFormHasErrorsForFields(response, ['password'])

    def test_login_with_post_proper_data(self):
        data = {'username': 'john', 'password': 'asd'}
        response = self.client.post(LOGIN_WITH_URL, data)
        self.assertRedirects(response, '/', target_status_code=404)

    # /login/without/
    def test_login_without_get(self):
        response = self.client.get(LOGIN_WITHOUT_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertFormHasErrorsForFields(response, [])

    def test_login_without_no_data(self):
        response = self.client.post(LOGIN_WITHOUT_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertFormHasErrorsForFields(response, ['username', 'password'])

    def test_login_without_missing_password(self):
        response = self.client.post(LOGIN_WITHOUT_URL, {'username': 'john'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertFormHasErrorsForFields(response, ['password'])

    def test_login_without_proper_data(self):
        data = {'username': 'john', 'password': 'asd'}
        response = self.client.post(LOGIN_WITHOUT_URL, data)
        self.assertRedirects(response, '/', target_status_code=404)

    # /with/http/
    def test_with_http(self):
        response = self.client.get(WITH_HTTP_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_with_http_proper_data(self):
        data = {'username': 'john', 'password': 'asd'}
        response = self.client.post(WITH_HTTP_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'hi john')

    # /with/variable/redirect/
    def test_var_redirect(self):
        response = self.client.get(WITH_VARIABLE_REDIRECT_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_var_redirect_proper_data(self):
        data = {'username': 'john', 'password': 'asd'}
        response = self.client.post(WITH_VARIABLE_REDIRECT_URL, data)
        self.assertRedirects(response, '/john/', target_status_code=404)

    # /with/data/:username/
    def test_with_data_username(self):
        response = self.client.get('/with/data/joe/')
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        username_field = form.fields['username']
        self.assertEqual(username_field.initial, 'joe')

    # /init/returning/jack/
    def test_init_returning_user(self):
        response = self.client.get('/init/returning/jack/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'good boy jack')

    def test_init_raising_404(self):
        response = self.client.get('/init/raising/404/')
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        response = self.client.get('/login/required/')
        location = 'http://testserver/accounts/login/?next=/login/required/'
        self.assertEqual(response['Location'], location)

    def test_login_required_with_url(self):
        response = self.client.get('/login/required/with/url/')
        location = 'http://testserver/mylogin/?next=/login/required/with/url/'
        self.assertEqual(response['Location'], location)

    def test_custom_requirement(self):
        response = self.client.get('/custom/requirement/?foo=bar')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('login.html')

    # AJAX tests
    def test_login_with_json(self):
        response = self.client.get('/login/with/?json=true')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['username']['label'], 'Username')
        self.assertTrue(data['username']['required'])
        self.assertTrue(data['password']['required'])

    def test_login_with_json_post_no_data(self):
        response = self.client.post('/login/with/?json=true')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('username', data['errors'])
        self.assertIn('password', data['errors'])

    def test_login_with_json_post_missing_password(self):
        params = {'username': 'john'}
        response = self.client.post('/login/with/?json=true', params)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('password', data['errors'])

    def test_login_with_json_post_proper_data(self):
        params = {'username': 'john', 'password': 'asd'}
        response = self.client.post('/login/with/?json=true', params)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertNotIn('errors', data)

    def test_ajax_only(self):
        response = self.client.post('/ajax/only/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('username', data['errors'])
        self.assertIn('password', data['errors'])

    def test_ajax_only_proper_data(self):
        params = {'username': 'john', 'password': 'asd'}
        response = self.client.post('/ajax/only/', params)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertNotIn('errors', data)
        self.assertEqual(data['response']['username'], 'john')

    def test_both(self):
        params = {'username': 'john', 'password': 'asd'}
        response = self.client.post('/both/ajax/and/web/', params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'hi john')

    def test_both_json(self):
        params = {'username': 'john', 'password': 'asd'}
        response = self.client.post('/both/ajax/and/web/?json=true', params)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertNotIn('errors', data)
        self.assertEqual(data['response']['username'], 'john')

    def test_both_json_validate_only(self):
        response = self.client.post('/both/ajax/and/web/?validate_only=true', {})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['valid'])
        self.assertIn('username', data['errors'])
        self.assertIn('password', data['errors'])

    def test_both_json_validate_only_validate_only(self):
        params = {'username': 'john', 'password': 'asd'}
        response = self.client.post('/both/ajax/and/web/?validate_only=true',
            params)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['valid'])
        self.assertEqual(data['errors'], {})

