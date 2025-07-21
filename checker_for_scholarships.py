import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin


class ScholarshipCollector:
    def __init__(self):
        self.base_url = "put-your-url.here" #put your url here, Make sure to respect the websites Terms of Sevice and robot.txt
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def get_page(self, url):
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response
        except requests.RequestException:
            return None

    def is_relevant(self, element):
        text = element.get_text().strip().lower()
        skip = [
            'skip to content', 'your source for job',
            'bachelor\'s degree (', 'scholarship (',
            'filter', 'sort by', 'results per page'
        ]
        if any(s in text for s in skip) or len(text) < 10:
            return False
        return any(k in text for k in ['scholarship', 'grant', 'fellowship', 'award', 'financial aid'])

    def extract_details(self, detail_url):
        details = {"type": "", "field": "", "location": "", "salary": "", "description": ""}
        response = self.get_page(detail_url)
        if not response:
            return details

        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('div', {'id': 'scholarship-details'}) or soup.find('div', class_='content')
        if content:
            paragraphs = content.find_all('p')
            if paragraphs:
                details['description'] = ' '.join(p.get_text().strip() for p in paragraphs[:2])

        text = soup.get_text()

        amount_patterns = [
            r'\$[\d,]+(?:\.\d{2})?(?:\s*-\s*\$[\d,]+(?:\.\d{2})?)?',
            r'up to \$[\d,]+', r'maximum of \$[\d,]+', r'award of \$[\d,]+'
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                details['salary'] = match.group().strip()
                break

        for field in ['engineering', 'computer science', 'business', 'nursing', 'education', 'science', 'technology', 'math', 'stem']:
            if field in details['description'].lower():
                details['field'] = field.title()
                break

        location_patterns = [
            r'residents? of ([A-Z][a-z]+ [A-Z][a-z]+|[A-Z][a-z]+)',
            r'([A-Z]{2}) residents?',
            r'students? in ([A-Z][a-z]+)'
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                details['location'] = match.group(1).strip()
                break

        desc = details['description'].lower()
        if 'fellowship' in desc:
            details['type'] = 'Fellowship'
        elif 'grant' in desc:
            details['type'] = 'Grant'
        else:
            details['type'] = 'Scholarship'

        return details

    def parse_element(self, element):
        scholarship = {
            "title": "", "type": "", "field": "",
            "location": "", "salary": "", "link": "",
            "note": "From website"
        }
        try:
            title_link = element.find('a', href=re.compile(r'scholarshipId=\d+'))
            if title_link:
                scholarship['title'] = title_link.get_text().strip()
                scholarship['link'] = urljoin(self.base_url, title_link.get('href'))
                details = self.extract_details(scholarship['link'])
                scholarship.update({
                    'type': details['type'], 'field': details['field'],
                    'location': details['location'], 'salary': details['salary']
                })
                time.sleep(1)
        except:
            pass
        return scholarship

    def collect(self, url, max_pages=2):
        results = []
        for page in range(1, max_pages + 1):
            if page == 1:
                page_url = url
            else:
                page_url = re.sub(r'curPage=\d+', f'curPage={page}', url) \
                    if 'curPage=' in url else f"{url}&curPage={page}" if '?' in url else f"{url}?curPage={page}"

            response = self.get_page(page_url)
            if not response:
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'scholarshipId=\d+'))
            if not links:
                break

            seen = {}
            for link in links:
                href = link.get('href')
                if href and href not in seen:
                    seen[href] = link

            for element_html in seen.values():
                element = BeautifulSoup(str(element_html), 'html.parser')
                scholarship = self.parse_element(element)
                if scholarship['title'] and scholarship['link']:
                    results.append(scholarship)

            time.sleep(3)
        return results

    def deduplicate(self, scholarships):
        seen, unique = set(), []
        for s in scholarships:
            key = s['title'].strip().lower()
            if key and key not in seen:
                seen.add(key)
                for k, v in s.items():
                    if isinstance(v, str):
                        s[k] = v.strip()
                unique.append(s)
        return unique

    def save(self, scholarships, filename="opportunities.json"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(scholarships, f, indent=2, ensure_ascii=False)
        except:
            pass


def main():
    collector = ScholarshipCollector()
    url = "put-your-url.here" #put your url here, Make sure to respect the websites Terms of Sevice and robot.txt
    raw = collector.collect(url, max_pages=3)
    if raw:
        clean = collector.deduplicate(raw)
        collector.save(clean)
        return clean
    return []
