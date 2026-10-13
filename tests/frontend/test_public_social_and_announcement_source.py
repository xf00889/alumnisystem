"""Offline source and isolated HTTP tests for public page enhancement (no Django DB)."""
import importlib.util
import json
import sys
import types
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
def read(relative): return (ROOT/relative).read_text(encoding='utf8')

class PublicSocialSourceTests(unittest.TestCase):
    def test_facebook_section_only_uses_configured_cms_url_and_actual_posts(self):
        home=read('templates/home.html')
        self.assertIn('{% if site_config.facebook_url %}',home)
        self.assertIn('{% if facebook_posts %}',home)
        self.assertIn('fb_post.image',home)
        self.assertIn('fb_post.permalink',home)
        self.assertNotIn('FACEBOOK_PAGE_ACCESS_TOKEN',home)
        self.assertIn('noopener noreferrer',home)
        self.assertIn('referrerpolicy="no-referrer"',home)

    def test_secure_server_configuration(self):
        service=read('core/services/facebook_page_feed.py')
        settings=read('norsu_alumni/settings.py')
        self.assertIn('Authorization\': \'Bearer ',service)
        self.assertIn('FEED_CACHE_SECONDS',service)
        self.assertIn('len(cards) == 5',service)
        self.assertIn("os.environ.get('FACEBOOK_PAGE_ACCESS_TOKEN'",settings)
        self.assertNotIn('access_token\':',service)

    def test_announcement_empty_state_and_auth_flow_preserved(self):
        page=read('templates/landing/announcements.html')
        self.assertIn('public-announcements-empty',page)
        self.assertIn('public_announcements_experience.css',page)
        self.assertIn('{% if announcements %}',page)
        self.assertIn('announcements.has_other_pages',page)
        self.assertIn("{% url 'account_login' %}",page)
        self.assertIn("{% url 'core:home' %}",page)

    def test_staff_emails_open_mail_composer_and_manual_carousel(self):
        page=read('templates/home.html')
        self.assertIn('href="mailto:{{ staff.email }}?',page)
        self.assertIn('class="home-team-email"',page)
        self.assertIn('data-gallery-autoplay="false"',page)
        self.assertNotIn('data-team-gallery data-home-gallery data-gallery-interval',page)

    def test_facebook_parser_rejects_unsafe_remote_urls(self):
        django=types.ModuleType('django')
        conf=types.ModuleType('django.conf');conf.settings=types.SimpleNamespace(FACEBOOK_PAGE_ID='12345',FACEBOOK_PAGE_ACCESS_TOKEN='fake_secret')
        core=types.ModuleType('django.core');cache_mod=types.ModuleType('django.core.cache')
        class FakeCache:
            data={}
            def get(self,key):return self.data.get(key)
            def set(self,key,value,ttl):self.data[key]=value
        cache_mod.cache=FakeCache()
        with patch.dict(sys.modules,{'django':django,'django.conf':conf,'django.core':core,'django.core.cache':cache_mod}):
            module_path=ROOT/'core/services/facebook_page_feed.py'
            spec=importlib.util.spec_from_file_location('_test_fbfeed',module_path)
            mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
            bad={'full_picture':'javascript:alert(1)','permalink_url':'https://www.facebook.com/post/123'}
            self.assertIsNone(mod._post_card(bad))
            bad2={'full_picture':'https://attacker.fbcdn.net.evil.example/photo.jpg','permalink_url':'https://www.facebook.com/post/123'}
            self.assertIsNone(mod._post_card(bad2))
            good={'full_picture':'https://scontent.fbcdn.net/photo.jpg','permalink_url':'https://www.facebook.com/post/123','message':'Real post','created_time':'2026-10-13T00:01:00+0000'}
            self.assertEqual(mod._post_card(good)['text'],'Real post')

            class Response:
                def __init__(self):self.buffer=BytesIO(json.dumps({'data':[good]*8}).encode())
                def __enter__(self):return self
                def __exit__(self,*args):return False
                def read(self,*args):return self.buffer.read(*args)
            calls=[]
            def fetch(req,timeout=None):
                calls.append(req)
                self.assertNotIn('fake_secret',req.full_url)
                self.assertEqual(req.headers['Authorization'],'Bearer fake_secret')
                self.assertEqual(timeout,4)
                return Response()
            with patch.object(mod,'urlopen',fetch):
                self.assertEqual(len(mod.get_latest_facebook_image_posts()),5)
                self.assertEqual(len(mod.get_latest_facebook_image_posts()),5)
            self.assertEqual(len(calls),1,'second request must use cached response')

if __name__=='__main__':unittest.main()
