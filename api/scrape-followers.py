from http.server import BaseHTTPRequestHandler
import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def parse_substack_url(url):
    """Extract handle or subdomain from a Substack URL."""
    if not url.startswith('http'):
        url = 'https://' + url

    parsed = urlparse(url)
    hostname = parsed.hostname or ''
    path = parsed.path.strip('/')

    # Format: substack.com/@handle or substack.com/@handle/followers
    if hostname in ('substack.com', 'www.substack.com'):
        if path.startswith('@'):
            handle = path.split('/')[0].lstrip('@')
            return {'handle': handle, 'subdomain': None}

    # Format: example.substack.com
    if hostname.endswith('.substack.com'):
        subdomain = hostname.replace('.substack.com', '')
        return {'handle': None, 'subdomain': subdomain}

    # Custom domain - try to resolve via the page
    return {'handle': None, 'subdomain': None, 'custom_url': url}


def resolve_handle_from_subdomain(subdomain):
    """Fetch a publication page and find the author's @handle."""
    try:
        resp = requests.get(
            f'https://{subdomain}.substack.com',
            headers=HEADERS,
            timeout=8,
            allow_redirects=True,
        )
        resp.raise_for_status()
        preloads = extract_preloads(resp.text)
        if preloads:
            # Look for author handle in preloads
            for key in ('profile', 'user', 'author'):
                if key in preloads and isinstance(preloads[key], dict):
                    handle = preloads[key].get('handle')
                    if handle:
                        return handle
            # Try to find in publication users
            if 'publicationUsers' in preloads:
                for pu in preloads['publicationUsers']:
                    user = pu.get('user', {})
                    if user.get('handle'):
                        return user['handle']
            # Search recursively for any handle field
            handle = find_handle_in_dict(preloads)
            if handle:
                return handle
        # Fallback: look for @handle link in the HTML
        soup = BeautifulSoup(resp.text, 'html.parser')
        link = soup.find('a', href=re.compile(r'substack\.com/@\w+'))
        if link:
            match = re.search(r'@(\w+)', link['href'])
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


def find_handle_in_dict(d, depth=0):
    """Recursively search for a 'handle' key in nested dicts/lists."""
    if depth > 5:
        return None
    if isinstance(d, dict):
        if 'handle' in d and isinstance(d['handle'], str) and d['handle']:
            return d['handle']
        for v in d.values():
            result = find_handle_in_dict(v, depth + 1)
            if result:
                return result
    elif isinstance(d, list):
        for item in d[:10]:  # limit iteration
            result = find_handle_in_dict(item, depth + 1)
            if result:
                return result
    return None


def extract_preloads(html):
    """Extract window._preloads JSON from a Substack page."""
    match = re.search(r'window\._preloads\s*=\s*JSON\.parse\((".*?")\)', html, re.DOTALL)
    if match:
        try:
            json_str = json.loads(match.group(1))  # unescape the string
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            pass

    match = re.search(r'window\._preloads\s*=\s*(\{.*?\});?\s*</script>', html, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def scrape_followers(handle):
    """Scrape the public followers list for a Substack handle."""
    url = f'https://substack.com/@{handle}/followers'
    resp = requests.get(url, headers=HEADERS, timeout=8)
    resp.raise_for_status()

    followers = []
    preloads = extract_preloads(resp.text)

    if preloads:
        # Strategy 1: Look for followers in preloads JSON
        for key in ('followers', 'profileFollowers', 'initialFollowers', 'followedBy'):
            data = preloads.get(key)
            if isinstance(data, list) and len(data) > 0:
                followers = parse_followers_list(data)
                if followers:
                    return followers
            elif isinstance(data, dict):
                items = data.get('items') or data.get('results') or data.get('data') or []
                if items:
                    followers = parse_followers_list(items)
                    if followers:
                        return followers

        # Strategy 2: Search all top-level keys for arrays of user-like objects
        for key, val in preloads.items():
            if isinstance(val, list) and len(val) > 0:
                if is_user_list(val):
                    followers = parse_followers_list(val)
                    if followers:
                        return followers
            elif isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    if isinstance(sub_val, list) and len(sub_val) > 0:
                        if is_user_list(sub_val):
                            followers = parse_followers_list(sub_val)
                            if followers:
                                return followers

    # Strategy 3: Parse HTML directly
    soup = BeautifulSoup(resp.text, 'html.parser')
    followers = parse_followers_from_html(soup)
    if followers:
        return followers

    # Strategy 4: Try the API endpoint directly
    try:
        user_id = None
        if preloads:
            profile = preloads.get('profile', {})
            user_id = profile.get('id')
        if user_id:
            api_url = f'https://substack.com/api/v1/user/{user_id}/public_followers'
            api_resp = requests.get(api_url, headers=HEADERS, timeout=8)
            if api_resp.ok:
                api_data = api_resp.json()
                items = api_data if isinstance(api_data, list) else api_data.get('items', api_data.get('followers', []))
                followers = parse_followers_list(items)
                if followers:
                    return followers
    except Exception:
        pass

    return followers


def is_user_list(items):
    """Check if a list looks like a list of user/subscriber objects."""
    if not items:
        return False
    sample = items[0]
    if not isinstance(sample, dict):
        return False
    user_keys = {'name', 'handle', 'photo_url', 'profile_photo_url', 'bio', 'username'}
    return len(user_keys & set(sample.keys())) >= 2


def parse_followers_list(items):
    """Parse a list of user-like dicts into a normalized followers list."""
    followers = []
    for item in items:
        if not isinstance(item, dict):
            continue

        # The item might have a nested user object
        user = item.get('user', item)
        if not isinstance(user, dict):
            continue

        name = (
            user.get('name') or
            user.get('display_name') or
            user.get('username') or
            ''
        )
        handle = user.get('handle') or user.get('username') or ''
        photo = (
            user.get('photo_url') or
            user.get('profile_photo_url') or
            user.get('avatar_url') or
            user.get('image_url') or
            ''
        )
        bio = user.get('bio') or user.get('about') or ''

        if not name and not handle:
            continue

        profile_url = f'https://substack.com/@{handle}' if handle else ''

        # Check if they have a publication/newsletter
        publication_url = ''
        publication_name = ''
        pub = user.get('primary_publication') or user.get('publication') or {}
        if isinstance(pub, dict):
            subdomain = pub.get('subdomain', '')
            custom_domain = pub.get('custom_domain', '')
            if custom_domain:
                publication_url = f'https://{custom_domain}'
            elif subdomain:
                publication_url = f'https://{subdomain}.substack.com'
            publication_name = pub.get('name', '')

        followers.append({
            'name': name,
            'handle': handle,
            'photo_url': photo,
            'bio': bio[:200] if bio else '',
            'profile_url': profile_url,
            'publication_url': publication_url,
            'publication_name': publication_name,
        })

    return followers


def parse_followers_from_html(soup):
    """Fallback: parse followers from HTML elements."""
    followers = []

    # Look for profile cards / follower links
    profile_links = soup.find_all('a', href=re.compile(r'substack\.com/@\w+'))
    seen_handles = set()

    for link in profile_links:
        href = link.get('href', '')
        match = re.search(r'@(\w+)', href)
        if not match:
            continue
        handle = match.group(1)
        if handle in seen_handles:
            continue
        seen_handles.add(handle)

        # Try to find name and image near this link
        name = ''
        photo = ''

        # Check for text content
        name_el = link.find(['span', 'div', 'p', 'h3', 'h4'])
        if name_el:
            name = name_el.get_text(strip=True)
        elif link.get_text(strip=True):
            name = link.get_text(strip=True)

        # Check for image
        img = link.find('img')
        if not img:
            parent = link.parent
            if parent:
                img = parent.find('img')
        if img:
            photo = img.get('src', '')

        if name or handle:
            followers.append({
                'name': name or handle,
                'handle': handle,
                'photo_url': photo,
                'bio': '',
                'profile_url': f'https://substack.com/@{handle}',
                'publication_url': '',
                'publication_name': '',
            })

    return followers


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}
        except (json.JSONDecodeError, ValueError):
            self._respond(400, {'error': 'Invalid JSON body'})
            return

        url = body.get('url', '').strip()
        if not url:
            self._respond(400, {'error': 'Missing "url" field'})
            return

        parsed = parse_substack_url(url)
        handle = parsed.get('handle')

        # If we got a subdomain, resolve it to a handle
        if not handle and parsed.get('subdomain'):
            handle = resolve_handle_from_subdomain(parsed['subdomain'])
            if not handle:
                # Try using the subdomain as handle directly
                handle = parsed['subdomain']

        if not handle and parsed.get('custom_url'):
            self._respond(400, {'error': 'Could not resolve Substack handle from custom domain. Try using a substack.com URL instead.'})
            return

        if not handle:
            self._respond(400, {'error': 'Could not parse Substack URL. Try format: substack.com/@handle or example.substack.com'})
            return

        try:
            followers = scrape_followers(handle)
            self._respond(200, {
                'handle': handle,
                'followers': followers,
                'count': len(followers),
            })
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 500
            if status == 404:
                self._respond(404, {'error': f'Profile @{handle} not found on Substack'})
            else:
                self._respond(502, {'error': f'Substack returned HTTP {status}'})
        except requests.exceptions.Timeout:
            self._respond(504, {'error': 'Request to Substack timed out'})
        except Exception as e:
            self._respond(500, {'error': f'Scraping failed: {str(e)}'})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
