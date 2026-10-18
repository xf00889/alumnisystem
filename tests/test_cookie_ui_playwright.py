"""Optional standalone browser checks (requires Python playwright and Chromium)."""
from pathlib import Path
from tempfile import TemporaryDirectory
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def fixture(saved=False):
    template = (ROOT / 'templates/components/privacy/cookie_consent.html').read_text()
    css = (ROOT / 'static/css/privacy/cookie-consent.css').read_text()
    js = (ROOT / 'static/js/privacy/cookie-consent.js').read_text()
    template = template.replace('{% load static %}', '')
    template = template.replace('{% url \'core:cookie_consent\' %}', '/api/privacy/cookie-consent/')
    template = template.replace("<link rel=\"stylesheet\" href=\"{% static 'css/privacy/cookie-consent.css' %}\">", '<style>' + css + '</style>')
    template = template.replace("<script defer src=\"{% static 'js/privacy/cookie-consent.js' %}\"></script>", '<script>' + js + '</script>')
    template = template.replace("{% static 'images/alumni_logo.webp' %}", 'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=')
    template = template.replace("{% if cookie_consent_choice != 'unset' %}hidden{% endif %}", 'hidden' if saved else '')
    return """<!DOCTYPE html><html lang='en'><meta name='viewport' content='width=device-width,initial-scale=1'><body>
    <main><h1>Sample NORSU page</h1></main>
    <footer><a href='/legal/cookie-policy/?cookie-settings=1' data-norsu-cookie-preferences>Cookie choices</a></footer>
    """ + template + '</body></html>'


def run():
    with TemporaryDirectory() as directory:
        directory = Path(directory)
        (directory / 'cookie-consent.js').write_bytes((ROOT / 'static/js/privacy/cookie-consent.js').read_bytes())
        (directory / 'cookie-consent.css').write_bytes((ROOT / 'static/css/privacy/cookie-consent.css').read_bytes())
        (directory / 'fresh.html').write_text(fixture())
        (directory / 'saved.html').write_text(fixture(saved=True))
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            for width in (320, 393, 1440):
                page = browser.new_page(viewport={'width': width, 'height': 800})
                # Simulate a normal HTTPS origin cookie jar (about:blank otherwise blocks it).
                page.evaluate("Object.defineProperty(document, 'cookie', {configurable:true, get(){return ''}})")
                # Simulate the Django GET CSRF bootstrap and POST cookie save.
                page.evaluate('''window.fetch = async (url, opts = {}) => {
                  if (opts.method === 'POST') {
                    const choice = new URLSearchParams(opts.body).get('choice');
                    window.lastConsentChoice = choice;
                    return {ok:true,status:200,json:async()=>({choice:choice})};
                  }
                  return {ok:true,status:200,json:async()=>({csrfToken:'testtoken'})};
                };''')
                page.set_content(fixture())
                page.get_by_role('button', name='Yes, allow optional visit statistics').click()
                page.wait_for_function("window.lastConsentChoice === 'analytics'")
                assert not page.locator('#norsuCookieConsent').is_visible()
                assert page.locator('#norsuCookieSettings').count() == 0
                page.get_by_text('Cookie choices').click()
                assert page.locator('#norsuCookieConsent').is_visible()
                page.get_by_role('button', name='No, do not allow optional visit statistics').click()
                page.wait_for_function("window.lastConsentChoice === 'necessary'")
                assert not page.locator('#norsuCookieConsent').is_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                page.set_content(fixture(saved=True))
                assert not page.locator('#norsuCookieConsent').is_visible()
                page.get_by_text('Cookie choices').click()
                assert page.locator('#norsuCookieConsent').is_visible()
                page.get_by_role('button', name='Close cookie preferences').click()
                assert not page.locator('#norsuCookieConsent').is_visible()
                page.close()
            browser.close()
    print('PASS: yes/no mapping, dismissal, footer re-open, saved preference, close, no overflow (320/393/1440).')


if __name__ == '__main__':
    run()
