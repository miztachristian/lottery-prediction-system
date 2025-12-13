#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website Inspector: Analyze lotteryextreme.com structure
"""

import requests
from bs4 import BeautifulSoup
import re


def inspect_lotteryextreme():
    """Inspect lotteryextreme.com for lottery data."""
    urls = [
        "https://www.lotteryextreme.com/netherlands/lotto-results",
        "https://www.lotteryextreme.com/netherlands/lotto-xl-results"
    ]

    for url in urls:
        print("=" * 80)
        print(f"ANALYZING: {url}")
        print("=" * 80)

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            print(f"Title: {soup.title.text if soup.title else 'No title'}")
            print(f"Status: {response.status_code}")
            print()

            # Look for tables
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables:")
            for i, table in enumerate(tables[:2]):  # First 2 tables
                rows = table.find_all('tr')
                print(f"\n  Table {i+1}: {len(rows)} rows")
                
                # Check first few rows
                for j, row in enumerate(rows[:5]):
                    cells = row.find_all(['td', 'th'])
                    cell_text = [c.get_text().strip() for c in cells]
                    print(f"    Row {j+1}: {cell_text}")

            # Look for result divs
            result_divs = soup.find_all('div', class_=lambda x: x and ('result' in str(x).lower() or 'draw' in str(x).lower()))
            print(f"\nFound {len(result_divs)} result-related divs")
            for i, div in enumerate(result_divs[:3]):
                print(f"  Div {i+1}: classes={div.get('class')}")
                print(f"    Text: {div.get_text()[:100]}")

            # Look for pagination
            pagination = soup.find_all(['a', 'div'], class_=lambda x: x and 'pag' in str(x).lower())
            print(f"\nFound {len(pagination)} pagination elements")
            for i, elem in enumerate(pagination[:5]):
                print(f"  {i+1}: {elem.name} - {elem.get('class')} - href={elem.get('href')}")

            print()

        except Exception as e:
            print(f"Error: {e}")
            print()


if __name__ == "__main__":
    inspect_lotteryextreme()
