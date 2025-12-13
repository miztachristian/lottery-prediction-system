#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website Inspector: Analyze lotteryguru.com structure to understand HTML parsing
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List


def inspect_website(url: str) -> Dict:
    """Inspect website structure and return analysis."""
    print(f"Inspecting: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        analysis = {
            'url': url,
            'status_code': response.status_code,
            'title': soup.title.text if soup.title else 'No title',
            'tables': len(soup.find_all('table')),
            'divs_with_data': [],
            'scripts': len(soup.find_all('script')),
            'potential_data_containers': []
        }

        # Look for tables
        tables = soup.find_all('table')
        print(f"\nFound {len(tables)} tables:")

        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            print(f"  Table {i+1}: {len(rows)} rows")

            if rows:
                # Check first row for headers
                headers = rows[0].find_all(['th', 'td'])
                header_text = [h.get_text().strip() for h in headers]
                print(f"    Headers: {header_text}")

                # Check a few data rows
                for j, row in enumerate(rows[1:4]):  # First 3 data rows
                    cells = row.find_all(['td', 'th'])
                    cell_text = [c.get_text().strip() for c in cells]
                    print(f"    Row {j+1}: {cell_text}")

        # Look for divs that might contain lottery data
        divs = soup.find_all('div', class_=True)
        print(f"\nFound {len(divs)} divs with classes")

        data_classes = ['result', 'draw', 'lotto', 'number', 'date', 'history', 'table']
        for div in divs:
            classes = div.get('class', [])
            if any(keyword in ' '.join(classes).lower() for keyword in data_classes):
                analysis['divs_with_data'].append({
                    'classes': classes,
                    'text_preview': div.get_text()[:100]
                })

        # Look for JSON data in scripts
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('lotto' in script.string.lower() or 'result' in script.string.lower()):
                analysis['potential_data_containers'].append({
                    'type': 'script_json',
                    'content_preview': script.string[:200]
                })

        # Look for structured data
        json_scripts = soup.find_all('script', type='application/json')
        if json_scripts:
            print(f"\nFound {len(json_scripts)} JSON scripts")
            analysis['json_scripts'] = len(json_scripts)

        return analysis

    except Exception as e:
        print(f"Error inspecting website: {e}")
        return {'error': str(e)}


def analyze_lotteryguru():
    """Analyze both Lotto and Lotto XL pages."""
    urls = [
        "https://lotteryguru.com/netherlands-lottery-results/nl-lotto/nl-lotto-results-history",
        "https://lotteryguru.com/netherlands-lottery-results/nl-lotto-xl/nl-lotto-xl-results-history"
    ]

    for url in urls:
        print("=" * 80)
        print(f"ANALYZING: {url}")
        print("=" * 80)

        analysis = inspect_website(url)

        if 'error' not in analysis:
            print(f"Title: {analysis['title']}")
            print(f"Tables: {analysis['tables']}")
            print(f"Scripts: {analysis['scripts']}")

            if analysis['divs_with_data']:
                print(f"Potential data divs: {len(analysis['divs_with_data'])}")
                for div in analysis['divs_with_data'][:3]:  # Show first 3
                    print(f"  Classes: {div['classes']}")
                    print(f"  Preview: {div['text_preview'][:100]}...")

            if analysis.get('json_scripts', 0) > 0:
                print(f"JSON scripts: {analysis['json_scripts']}")

        print()


if __name__ == "__main__":
    analyze_lotteryguru()