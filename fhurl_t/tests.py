from django.test import TestCase


#FIELD_REQUIRED = 'This field is required.'
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

