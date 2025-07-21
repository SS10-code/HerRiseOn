import requests
import json
import re
import time
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class JobCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.jobs: List[Dict] = []
        self.driver = self._init_browser()

    def _init_browser(self) -> webdriver.Chrome:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=options)

    def __del__(self):
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

    def extract_salary(self, text: str) -> Optional[int]:
        if not text:
            return None

        patterns = [
            r'\$(\d+),(\d+)-(\d+),(\d+)',
            r'\$(\d+),(\d+)',
            r'\$(\d+)k-(\d+)k',
            r'\$(\d+)k',
            r'(\d+),(\d+)-(\d+),(\d+)',
            r'(\d+)k-(\d+)k',
            r'(\d+)k',
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                digits = [d for d in match.groups() if d and d.isdigit()]
                if len(digits) >= 2:
                    return int(digits[0] + digits[1]) // 1000
                elif len(digits) == 1:
                    num = int(digits[0])
                    return num if num < 500 else num // 1000
        return None

    def clean_text(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text.strip()) if text else ""

    def determine_field(self, title: str, description: str) -> str:
        content = f"{title} {description}".lower()
        categories = {
            "STEM": ["engineer", "developer", "scientist", "data", "software", "ai", "cloud", "python"],
            "Healthcare": ["nurse", "doctor", "health", "clinical"],
            "Finance": ["finance", "accounting", "analyst"],
            "Education": ["teacher", "education", "professor"],
            "Marketing": ["marketing", "sales", "advertising"],
            "Design": ["designer", "ux", "graphic"],
            "Product": ["product", "scrum"],
            "HR": ["recruiting", "hr"],
            "Operations": ["operations", "logistics"]
        }
        for field, keywords in categories.items():
            if any(keyword in content for keyword in keywords):
                return field
        return "General"

    def _is_valid_link(self, href: str) -> bool:
        if not href:
            return False
        if '/job/' not in href:
            return False
        slug = href.split('/job/')[-1]
        return '-' in slug and len(slug) > 10

    def _is_valid_posting(self, job: Dict) -> bool:
        title = job.get('title', '').lower()
        if not title:
            return False
        if any(forbidden in title for forbidden in ['new jobs', 'sort by', 'save job', 'apply now']):
            return False
        if not self._is_valid_link(job.get('link', '')):
            return False
        return 2 <= len(title.split()) <= 20

    def _parse_posting(self, element) -> Optional[Dict]:
        job = {
            "title": None,
            "type": "Job",
            "field": None,
            "location": None,
            "salary": None,
            "link": None,
            "note": None
        }

        try:
            href = element.get_attribute('href')
            if not self._is_valid_link(href):
                return None
            job["link"] = href

            text = element.text.strip()
            if not text:
                return None

            lines = [line.strip() for line in text.split('\n') if line.strip()]

            for line in lines:
                if len(line) > 5 and not any(word in line.lower() for word in ['save job', 'ago', '•']):
                    job["title"] = line
                    break
            if not job["title"]:
                return None

            for pattern in [
                r'([A-Z][a-z]+,\s*[A-Z]{2}(?:,\s*USA)?)',
                r'(Remote\s*-\s*[^,]+)',
                r'(Hybrid\s*-\s*[^,]+)'
            ]:
                match = re.search(pattern, text)
                if match:
                    job["location"] = match.group(1).strip()
                    break

            if not job["location"]:
                for line in lines:
                    if any(kw in line.lower() for kw in ['remote', 'hybrid', ',']) and len(line) < 50:
                        job["location"] = line
                        break

            job["salary"] = self.extract_salary(text)
            job["field"] = self.determine_field(job["title"], text)

            note_candidates = [
                line for line in lines[:4]
                if len(line) > 10 and line != job["title"] and not any(x in line.lower() for x in ['save job', 'apply'])
            ]
            job["note"] = ' | '.join(note_candidates)[:200] if note_candidates else job["title"]

            return job

        except Exception:
            return None

    def collect_from_site(self, max_results: int = 50) -> List[Dict]:
        url = "put-your-url.here" #put your url here, Make sure to respect the websites Terms of Sevice and robot.txt
        self.driver.get(url)
        time.sleep(5)

        selectors = [
            'a[href*="/job/"]:not([href*="filter"]):not([href*="category"])',
            '.job-card a',
            'article a[href*="/job/"]'
        ]

        elements = []
        for selector in selectors:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) > 3:
                break

        if not elements:
            return []

        seen_links = set()
        collected_jobs = []

        for element in elements[:max_results]:
            job = self._parse_posting(element)
            if job and job["link"] not in seen_links and self._is_valid_posting(job):
                seen_links.add(job["link"])
                collected_jobs.append(job)

        return collected_jobs

    def save_to_json(self, filename: str = "jobs.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, indent=2, ensure_ascii=False)

    def run(self):
        new_jobs = self.collect_from_site(max_results=20)
        if new_jobs:
            self.jobs.extend(new_jobs)
            self.save_to_json("job_opportunities.json")