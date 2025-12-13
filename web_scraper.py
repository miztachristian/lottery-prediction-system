#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Scraper: Fetch historical lottery data from multiple sources
Supports: lotteryguru.com, lotteryextreme.com
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os

BALLS = 45


class LotteryScraper:
    """Scrape historical lottery data from multiple sources"""

    def __init__(self, game: str = "xl", delay: float = 1.0, source: str = "lotteryguru"):
        """
        Args:
            game: "xl" or "lotto"
            delay: Seconds to wait between requests (be respectful)
            source: "lotteryguru" or "lotteryextreme"
        """
        self.game = game
        self.delay = delay
        self.source = source.lower()
        self.session = requests.Session()

        # Set user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_url(self, page: int = None, year: int = None, month: int = None) -> str:
        """Get the appropriate URL for the game with pagination/date range support."""
        if self.source == "lotteryguru":
            base = "https://lotteryguru.com/netherlands-lottery-results"
            if self.game == "xl":
                url = f"{base}/nl-lotto-xl/nl-lotto-xl-results-history"
            else:
                url = f"{base}/nl-lotto/nl-lotto-results-history"
            
            # Add page parameter if specified
            if page and page > 1:
                url += f"?page={page}"
            return url
            
        elif self.source == "lotteryextreme":
            # LotteryExtreme uses date-based URLs
            base = "https://www.lotteryextreme.com/netherlands/lotto-results"
            
            # Date range support for pagination
            if year and month:
                url = f"{base}?month={year}-{month:02d}"
            else:
                url = base
            return url
        
        else:
            raise ValueError(f"Unknown source: {self.source}")

    def scrape_page(self, url: str) -> Optional[str]:
        """Fetch and return HTML content from a page."""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            time.sleep(self.delay)  # Be respectful
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_draws_from_html(self, html: str) -> List[Dict]:
        """Parse lottery draws from HTML content based on source."""
        if self.source == "lotteryguru":
            return self._parse_lotteryguru(html)
        elif self.source == "lotteryextreme":
            return self._parse_lotteryextreme(html)
        else:
            return []

    def _parse_lotteryguru(self, html: str) -> List[Dict]:
        """
        Parse lottery draws from lotteryguru.com HTML.
        
        Format: Saturday\n06 Dec\n2025\n9\n10\n14\n19\n22\n30\n37\n...
        """
        soup = BeautifulSoup(html, 'html.parser')
        draws = []

        # Find the historical results container
        history_container = soup.find('div', class_='lg-lottery-older-results')
        if not history_container:
            print("No history container found")
            return draws

        # Get all text and split into lines
        text_content = history_container.get_text()
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]

            # Look for day of week (Saturday, etc.)
            if line in ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                # Next lines should be the date (split across lines)
                if i + 2 < len(lines):
                    date_part1 = lines[i + 1]  # "06 Dec"
                    date_part2 = lines[i + 2]  # "2025"
                    date_str = f"{date_part1} {date_part2}"
                    date = self._parse_date(date_str)

                    if date:
                        # Next lines should contain the numbers (7 numbers: 6 main + 1 reserve)
                        if i + 9 < len(lines):
                            number_lines = lines[i + 3:i + 10]  # 7 number lines
                            numbers = []

                            for num_line in number_lines:
                                try:
                                    num = int(num_line)
                                    if 1 <= num <= BALLS:
                                        numbers.append(num)
                                except ValueError:
                                    break

                            if len(numbers) == 7:  # 6 main + 1 reserve
                                draw = {
                                    'date': date.strftime('%Y-%m-%d'),
                                    'n1': numbers[0],
                                    'n2': numbers[1],
                                    'n3': numbers[2],
                                    'n4': numbers[3],
                                    'n5': numbers[4],
                                    'n6': numbers[5],
                                    'reserve': numbers[6],
                                    'game': 'Lotto XL' if self.game == 'xl' else 'Lotto',
                                    'source': 'lotteryguru.com'
                                }
                                draws.append(draw)
                                i += 9  # Skip all lines we processed
                            else:
                                i += 1  # Skip day line if numbers invalid
                        else:
                            i += 1
                    else:
                        i += 1  # Skip day line if date invalid
                else:
                    i += 1
            else:
                i += 1

        return draws

    def _parse_lotteryextreme(self, html: str) -> List[Dict]:
        """
        Parse lottery draws from lotteryextreme.com HTML.
        
        Format: "06-12-2025 Lotto112028313639 13Lotto XL91014192230 37"
        """
        soup = BeautifulSoup(html, 'html.parser')
        draws = []
        seen_keys = set()  # Track date+game to avoid duplicates

        # Find all table rows
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                for cell in cells:
                    text = cell.get_text().strip()
                    
                    # Find all dates in the text
                    date_matches = re.findall(r'(\d{2}-\d{2}-\d{4})', text)
                    if not date_matches:
                        continue
                    
                    for date_str in date_matches:
                        date = self._parse_date(date_str)
                        if not date:
                            continue
                        
                        date_key = date.strftime('%Y-%m-%d')
                        
                        # Find text segment after this date
                        date_pos = text.find(date_str)
                        segment = text[date_pos:]
                        
                        # Extract Lotto data (if game is lotto)
                        if self.game == "lotto":
                            lotto_match = re.search(r'Lotto(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\s+(\d{1,2})', segment)
                            if lotto_match:
                                dup_key = f"{date_key}-lotto"
                                if dup_key in seen_keys:
                                    continue
                                    
                                numbers = [int(lotto_match.group(i)) for i in range(1, 7)]
                                reserve = int(lotto_match.group(7))
                                
                                if all(1 <= n <= BALLS for n in numbers + [reserve]):
                                    draw = {
                                        'date': date_key,
                                        'n1': numbers[0],
                                        'n2': numbers[1],
                                        'n3': numbers[2],
                                        'n4': numbers[3],
                                        'n5': numbers[4],
                                        'n6': numbers[5],
                                        'reserve': reserve,
                                        'game': 'Lotto',
                                        'source': 'lotteryextreme.com'
                                    }
                                    draws.append(draw)
                                    seen_keys.add(dup_key)
                        
                        # Extract Lotto XL data (if game is xl)
                        if self.game == "xl":
                            xl_match = re.search(r'Lotto XL([\d\s]+)', segment)
                            if xl_match:
                                dup_key = f"{date_key}-xl"
                                if dup_key in seen_keys:
                                    continue
                                    
                                numbers_text = xl_match.group(1)
                                numbers = [int(n) for n in re.findall(r'\d+', numbers_text)]
                                
                                if len(numbers) >= 7:
                                    main_numbers = numbers[:6]
                                    reserve = numbers[6]
                                    
                                    if all(1 <= n <= BALLS for n in main_numbers + [reserve]):
                                        draw = {
                                            'date': date_key,
                                            'n1': main_numbers[0],
                                            'n2': main_numbers[1],
                                            'n3': main_numbers[2],
                                            'n4': main_numbers[3],
                                            'n5': main_numbers[4],
                                            'n6': main_numbers[5],
                                            'reserve': reserve,
                                            'game': 'Lotto XL',
                                            'source': 'lotteryextreme.com'
                                        }
                                        draws.append(draw)
                                        seen_keys.add(dup_key)

        return draws

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from various formats."""
        date_text = date_text.strip()

        # Try different date formats
        formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',   # DD-MM-YYYY (lotteryextreme format)
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d %b %Y',   # 06 Dec 2025 (abbreviated month)
            '%B %d, %Y',  # January 15, 2023
            '%d %B %Y',   # 15 January 2023
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue

        # Try relative dates
        if 'today' in date_text.lower():
            return datetime.now()
        elif 'yesterday' in date_text.lower():
            return datetime.now() - timedelta(days=1)

        return None

    def _extract_number(self, text: str) -> Optional[int]:
        """Extract number from text, handling various formats."""
        # Remove non-numeric characters except spaces and parentheses
        text = re.sub(r'[^\d\s\(\)]', '', text)

        # Look for the first number
        match = re.search(r'\d+', text)
        if match:
            num = int(match.group())
            if 1 <= num <= BALLS:
                return num

        return None

    def _is_date_line(self, line: str) -> bool:
        """Check if a line contains a date."""
        line = line.lower().strip()
        
        # Look for day names
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if any(day in line for day in days):
            return True
            
        # Look for date patterns like "06 Dec 2025" or "Dec 06, 2025"
        if re.search(r'\d{1,2}\s+\w{3}\s+\d{4}', line) or re.search(r'\w{3}\s+\d{1,2},?\s+\d{4}', line):
            return True
            
        return False

    def _is_number_line(self, line: str) -> bool:
        """Check if a line contains lottery numbers."""
        # Look for sequences of numbers that could be lottery balls
        numbers = re.findall(r'\b\d{1,2}\b', line)
        valid_numbers = [int(n) for n in numbers if 1 <= int(n) <= BALLS]
        return len(valid_numbers) >= 1

    def _extract_numbers_from_line(self, line: str) -> List[int]:
        """Extract lottery numbers from a line."""
        numbers = re.findall(r'\b\d{1,2}\b', line)
        return [int(n) for n in numbers if 1 <= int(n) <= BALLS]

    def _extract_reserve_from_line(self, line: str) -> Optional[int]:
        """Extract reserve number from a line."""
        numbers = self._extract_numbers_from_line(line)
        if numbers:
            return numbers[0]  # Assume first number is reserve
        return None

    def _is_complete_draw(self, draw: Dict) -> bool:
        """Check if a draw has all required components."""
        required = ['date', 'numbers', 'reserve']
        if not all(key in draw for key in required):
            return False
        if len(draw.get('numbers', [])) != 6:
            return False
        return True

    def scrape_historical_data(self, max_pages: int = 10, start_year: int = None, 
                              start_month: int = None, end_year: int = None, 
                              end_month: int = None) -> pd.DataFrame:
        """
        Scrape historical data with pagination and date range support.

        Args:
            max_pages: Maximum number of pages/months to scrape
            start_year: Starting year for date range (optional)
            start_month: Starting month for date range (optional)
            end_year: Ending year for date range (optional)
            end_month: Ending month for date range (optional)

        Returns:
            DataFrame with historical draws
        """
        all_draws = []

        if self.source == "lotteryguru":
            # Page-based pagination for lotteryguru
            for page in range(1, max_pages + 1):
                url = self.get_url(page=page)
                html = self.scrape_page(url)

                if html:
                    draws = self.parse_draws_from_html(html)
                    if not draws:
                        print(f"No more draws found on page {page}, stopping")
                        break
                    
                    all_draws.extend(draws)
                    print(f"Found {len(draws)} draws on page {page}")
                else:
                    print(f"Failed to fetch page {page}")
                    break

        elif self.source == "lotteryextreme":
            # LotteryExtreme only shows last 20 draws on main page (no pagination)
            url = self.get_url()
            html = self.scrape_page(url)

            if html:
                draws = self.parse_draws_from_html(html)
                all_draws.extend(draws)
                print(f"Found {len(draws)} draws from lotteryextreme (last 20 available)")

        # Convert to DataFrame
        if all_draws:
            df = pd.DataFrame(all_draws)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
            df = df.sort_values('date').reset_index(drop=True)
            df = df.drop_duplicates(subset=['date'], keep='first')
            return df

        return pd.DataFrame()

    def update_csv_with_scraped_data(self, csv_path: str, backup: bool = True) -> bool:
        """
        Update existing CSV with newly scraped data.

        Args:
            csv_path: Path to existing CSV
            backup: Whether to backup existing file

        Returns:
            True if successful
        """
        try:
            # Backup existing file
            if backup and os.path.exists(csv_path):
                backup_path = csv_path.replace('.csv', '_backup.csv')
                os.rename(csv_path, backup_path)
                print(f"Backed up {csv_path} to {backup_path}")

            # Scrape new data
            print("Scraping historical data...")
            scraped_df = self.scrape_historical_data()

            if scraped_df.empty:
                print("No data scraped")
                return False

            print(f"Scraped {len(scraped_df)} draws")

            # Load existing data if available
            existing_df = pd.DataFrame()
            if os.path.exists(csv_path):
                try:
                    existing_df = pd.read_csv(csv_path)
                    existing_df['date'] = pd.to_datetime(existing_df['date'], errors='coerce')
                    print(f"Loaded {len(existing_df)} existing draws")
                except Exception as e:
                    print(f"Error loading existing CSV: {e}")

            # Combine and deduplicate
            combined_df = pd.concat([existing_df, scraped_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
            combined_df = combined_df.sort_values('date').reset_index(drop=True)

            # Validate data
            combined_df = self._validate_and_clean_data(combined_df)

            # Save
            combined_df.to_csv(csv_path, index=False)
            print(f"Saved {len(combined_df)} draws to {csv_path}")

            return True

        except Exception as e:
            print(f"Error updating CSV: {e}")
            return False

    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean the scraped data."""
        # Ensure required columns exist
        required_cols = ['date', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'reserve', 'game', 'source']
        for col in required_cols:
            if col not in df.columns:
                if col == 'source':
                    df[col] = self.get_url()
                elif col == 'game':
                    df[col] = 'Lotto XL' if self.game == 'xl' else 'Lotto'
                else:
                    print(f"Missing required column: {col}")
                    return pd.DataFrame()

        # Convert number columns to int
        num_cols = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'reserve']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Drop rows with invalid data
        df = df.dropna(subset=num_cols + ['date'])

        # Validate ranges
        for col in num_cols:
            df = df[(df[col] >= 1) & (df[col] <= BALLS)]

        # Ensure n1-n6 are unique within each draw
        num_cols_main = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']
        df = df[df[num_cols_main].apply(lambda x: len(set(x)) == 6, axis=1)]

        return df.reset_index(drop=True)


def scrape_and_update_data(csv_path: str, game: str = "xl", max_pages: int = 10, 
                          source: str = "lotteryguru", start_year: int = None,
                          start_month: int = None, end_year: int = None,
                          end_month: int = None) -> bool:
    """
    Convenience function to scrape and update data from multiple sources.

    Args:
        csv_path: Path to CSV file to update
        game: "xl" or "lotto"
        max_pages: Maximum pages/months to scrape
        source: "lotteryguru" or "lotteryextreme" or "both"
        start_year: Starting year for date range (optional)
        start_month: Starting month for date range (optional)
        end_year: Ending year for date range (optional)
        end_month: Ending month for date range (optional)

    Returns:
        True if successful
    """
    all_draws = []
    
    if source == "both":
        # Scrape from both sources
        sources = ["lotteryguru", "lotteryextreme"]
    else:
        sources = [source]
    
    for src in sources:
        try:
            print(f"\n=== Scraping from {src} ===")
            scraper = LotteryScraper(game=game, source=src)
            
            df = scraper.scrape_historical_data(
                max_pages=max_pages,
                start_year=start_year,
                start_month=start_month,
                end_year=end_year,
                end_month=end_month
            )
            
            if not df.empty:
                all_draws.append(df)
                print(f"Successfully scraped {len(df)} draws from {src}")
            else:
                print(f"No data scraped from {src}")
                
        except Exception as e:
            print(f"Error scraping from {src}: {e}")
    
    if not all_draws:
        print("No data scraped from any source")
        return False
    
    # Combine data from all sources
    combined_df = pd.concat(all_draws, ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=['date'], keep='first')
    combined_df = combined_df.sort_values('date').reset_index(drop=True)
    
    # Load existing data and merge
    try:
        # Backup existing file
        if os.path.exists(csv_path):
            backup_path = csv_path.replace('.csv', '_backup.csv')
            import shutil
            shutil.copy2(csv_path, backup_path)
            print(f"Backed up {csv_path} to {backup_path}")
            
            existing_df = pd.read_csv(csv_path)
            existing_df['date'] = pd.to_datetime(existing_df['date'], errors='coerce')
            
            # Merge with existing data
            final_df = pd.concat([existing_df, combined_df], ignore_index=True)
            final_df = final_df.drop_duplicates(subset=['date'], keep='last')
            final_df = final_df.sort_values('date').reset_index(drop=True)
        else:
            final_df = combined_df
        
        # Save
        final_df.to_csv(csv_path, index=False)
        print(f"\n✅ Saved {len(final_df)} total draws to {csv_path}")
        print(f"Date range: {final_df['date'].min()} to {final_df['date'].max()}")
        return True
        
    except Exception as e:
        print(f"Error updating CSV: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Scrape lottery data from multiple sources")
    parser.add_argument("--csv", required=True, help="CSV file to update")
    parser.add_argument("--game", choices=["xl", "lotto"], default="xl", help="Game type")
    parser.add_argument("--source", choices=["lotteryguru", "lotteryextreme", "both"], 
                       default="both", help="Data source")
    parser.add_argument("--max-pages", type=int, default=10, 
                       help="Maximum pages/months to scrape")
    parser.add_argument("--start-year", type=int, help="Starting year (for date range)")
    parser.add_argument("--start-month", type=int, help="Starting month (for date range)")
    parser.add_argument("--end-year", type=int, help="Ending year (for date range)")
    parser.add_argument("--end-month", type=int, help="Ending month (for date range)")

    args = parser.parse_args()

    success = scrape_and_update_data(
        args.csv, 
        args.game, 
        args.max_pages,
        args.source,
        args.start_year,
        args.start_month,
        args.end_year,
        args.end_month
    )
    
    if success:
        print("\n✅ Data scraping completed successfully")
    else:
        print("\n❌ Data scraping failed")