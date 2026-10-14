import pathlib,unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]

def contents(path): return (ROOT/path).read_text()

class TwoFactorSourceContractTests(unittest.TestCase):
    def test_allauth_mfa_enabled(self):
        self.assertIn("'allauth.mfa'",contents('norsu_alumni/settings.py'))
        self.assertIn('MFA_SUPPORTED_TYPES',contents('norsu_alumni/settings.py'))
        self.assertIn('django-allauth[mfa]==0.61.1',contents('requirements.txt'))
    def test_encrypted_totp(self):
        content=contents('accounts/mfa_adapter.py')
        self.assertIn('Fernet',content)
        self.assertIn("'v1:'",content)
    def test_signup_verification_kept(self):
        content=contents('accounts/security_views.py')
        self.assertIn('SecurityCodeManager.verify_code',content)
        self.assertIn('EmailAddress.objects.update_or_create',content)
    def test_account_dashboard_links(self):
        self.assertIn("{% url 'mfa_index' %}",contents('templates/accounts/security_dashboard.html'))
    def test_otp_mfa_templates(self):
        for p in ['templates/mfa/authenticate.html','templates/mfa/totp/activate_form.html','templates/mfa/recovery_codes/index.html']:
            self.assertIn('csrf_token',contents(p)) if 'index' not in p else self.assertIn('unused_codes',contents(p))
    def test_login_css_separator_only(self):
        css=contents('static/css/auth-unified.css')
        self.assertIn('#loginForm .divider',css)

if __name__=='__main__':unittest.main()


class AdapterCryptoTests(unittest.TestCase):
    def test_totp_secrets_encrypt_and_round_trip_without_django(self):
        import importlib.util, sys, types
        from unittest.mock import patch
        django = types.ModuleType('django')
        django_conf = types.ModuleType('django.conf')
        django_conf.settings = types.SimpleNamespace(SECRET_KEY='test-key-not-used-in-production', MFA_ENCRYPTION_KEY='')
        allauth = types.ModuleType('allauth')
        allauth_mfa = types.ModuleType('allauth.mfa')
        allauth_adapter = types.ModuleType('allauth.mfa.adapter')
        allauth_adapter.DefaultMFAAdapter = type('DefaultMFAAdapter', (), {})
        source = ROOT/'accounts/mfa_adapter.py'
        with patch.dict(sys.modules, {
            'django':django, 'django.conf':django_conf,
            'allauth':allauth,'allauth.mfa':allauth_mfa,'allauth.mfa.adapter':allauth_adapter,
        }):
            spec = importlib.util.spec_from_file_location('norsu_mfa_adapter_contract',source)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            adapter = mod.NorsuMFAAdapter()
            encrypted = adapter.encrypt('ABC-SECRET-DO-NOT-EXPOSE')
            self.assertTrue(encrypted.startswith('v1:'))
            self.assertNotIn('ABC-SECRET', encrypted)
            self.assertEqual(adapter.decrypt(encrypted),'ABC-SECRET-DO-NOT-EXPOSE')
            django_conf.settings.MFA_ENCRYPTION_KEY = 'different-rotation-key'
            with self.assertRaises(ValueError):
                adapter.decrypt(encrypted)
            with self.assertRaises(ValueError):
                adapter.decrypt('ABC-SECRET-DO-NOT-EXPOSE')
