#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Pipeline: Load, normalize, compute stats (hot/overdue/frequency)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from collections import defaultdict

BALLS = 45


class LottoData:
    """Handles CSV loading, cleaning, normalization, and statistical feature computation."""

    def __init__(self, csv_path: str, game: str = "xl"):
        """
        Args:
            csv_path: Path to history CSV
            game: "xl" (6+reserve) or "lotto" (5 or 6)
        """
        self.csv_path = csv_path
        self.game = game
        self.df = self._load_and_clean()

    def _load_and_clean(self) -> pd.DataFrame:
        """Load CSV and enforce validity."""
        df = pd.read_csv(self.csv_path)

        # Ensure date column
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.sort_values("date").reset_index(drop=True)

        # Ensure columns exist
        required = ["n1", "n2", "n3", "n4", "n5", "reserve"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column '{col}' in {self.csv_path}")

        # Convert to numeric
        for col in required + (["n6"] if "n6" in df.columns else []):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Drop invalid rows
        df = df.dropna(subset=required).reset_index(drop=True)

        # Validate ranges
        for col in required + (["n6"] if "n6" in df.columns else []):
            df = df[(df[col] >= 1) & (df[col] <= BALLS)].reset_index(drop=True)

        if len(df) < 2:
            raise ValueError(f"Not enough valid rows (got {len(df)})")

        # Ensure n6 exists (for XL games)
        if "n6" not in df.columns:
            df["n6"] = df["n5"]  # fallback: copy n5

        return df

    def get_df(self) -> pd.DataFrame:
        """Return cleaned DataFrame."""
        return self.df.copy()

    def extract_main_numbers(self, row: pd.Series) -> set:
        """Extract 6 main numbers from a draw row."""
        return {int(row[c]) for c in ["n1", "n2", "n3", "n4", "n5", "n6"] if c in row.index}

    def extract_reserve(self, row: pd.Series) -> int:
        """Extract reserve number from a draw row."""
        return int(row["reserve"])

    def compute_frequency_stats(self, window_size: int = None) -> Dict[str, float]:
        """
        Compute frequency of each ball in history (or recent window).

        Args:
            window_size: If set, only use last N draws. If None, use all.

        Returns:
            Dict: ball_number -> frequency (0.0 to 1.0)
        """
        df = self.df if window_size is None else self.df.tail(window_size)

        freq = defaultdict(int)
        total_appearances = 0

        for _, row in df.iterrows():
            for ball in self.extract_main_numbers(row):
                freq[ball] += 1
                total_appearances += 1

        # Normalize
        if total_appearances == 0:
            return {i: 1.0 / BALLS for i in range(1, BALLS + 1)}

        return {ball: count / total_appearances for ball, count in freq.items()}

    def compute_gap_stats(self, window_size: int = None) -> Dict[str, int]:
        """
        Compute gaps (draws since last appearance) for each ball.

        Args:
            window_size: If set, only use last N draws.

        Returns:
            Dict: ball_number -> gap (draws since last appearance)
        """
        df = self.df if window_size is None else self.df.tail(window_size)
        n = len(df)

        gaps = {i: n for i in range(1, BALLS + 1)}  # default: never appeared

        for idx in range(n - 1, -1, -1):
            row = df.iloc[idx]
            for ball in self.extract_main_numbers(row):
                gaps[ball] = n - idx - 1  # distance from latest

        return gaps

    def compute_hot_cold(
        self, recent_window: int = 20, threshold_hot: int = None, threshold_cold: int = None
    ) -> Tuple[set, set]:
        """
        Classify balls as hot (frequent recently) or cold (rare/overdue).

        Args:
            recent_window: Number of recent draws to consider
            threshold_hot: Frequency to classify as hot. If None, auto-calculate.
            threshold_cold: Gap to classify as cold. If None, auto-calculate.

        Returns:
            Tuple[hot_set, cold_set]
        """
        freq = self.compute_frequency_stats(window_size=recent_window)
        gaps = self.compute_gap_stats(window_size=recent_window)

        freq_vals = list(freq.values())
        gap_vals = list(gaps.values())

        if threshold_hot is None:
            threshold_hot = np.mean(freq_vals) + 0.5 * np.std(freq_vals) if len(freq_vals) > 1 else 0.15
        if threshold_cold is None:
            threshold_cold = np.mean(gap_vals) - 0.5 * np.std(gap_vals) if len(gap_vals) > 1 else 5

        hot = {ball for ball, f in freq.items() if f >= threshold_hot}
        cold = {ball for ball, g in gaps.items() if g >= threshold_cold}

        return hot, cold

    def get_last_draw(self) -> Dict[str, int]:
        """Return the most recent draw."""
        row = self.df.iloc[-1]
        return {
            "date": row.get("date", None),
            "main": self.extract_main_numbers(row),
            "reserve": self.extract_reserve(row),
        }

    def update_with_scraped_data(self, max_pages: int = 5, backup: bool = True,
                                source: str = "both", start_year: int = None,
                                start_month: int = None, end_year: int = None,
                                end_month: int = None) -> bool:
        """
        Fetch additional historical data from web and merge with existing CSV.
        
        Args:
            max_pages: Maximum pages/months to scrape from website
            backup: Whether to backup existing CSV before updating
            source: "lotteryguru", "lotteryextreme", or "both"
            start_year: Starting year for date range (optional)
            start_month: Starting month for date range (optional)
            end_year: Ending year for date range (optional)
            end_month: Ending month for date range (optional)
            
        Returns:
            True if data was updated successfully
        """
        try:
            # Import here to avoid circular dependency
            from web_scraper import scrape_and_update_data
            
            # Scrape new data from specified sources
            print(f"Scraping additional {self.game} data from {source}...")
            success = scrape_and_update_data(
                csv_path=self.csv_path,
                game=self.game,
                max_pages=max_pages,
                source=source,
                start_year=start_year,
                start_month=start_month,
                end_year=end_year,
                end_month=end_month
            )
            
            if success:
                # Reload our internal dataframe
                self.df = self._load_and_clean()
                print(f"✅ Data pipeline updated: {len(self.df)} total draws")
                return True
            else:
                print("❌ Failed to scrape data")
                return False
            
        except Exception as e:
            print(f"Error updating with scraped data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean a dataframe (similar to _load_and_clean but for external data)."""
        # Ensure date column
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])
            df = df.sort_values("date").reset_index(drop=True)

        # Ensure columns exist
        required = ["n1", "n2", "n3", "n4", "n5", "reserve"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column '{col}'")

        # Convert to numeric
        for col in required + (["n6"] if "n6" in df.columns else []):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Drop invalid rows
        df = df.dropna(subset=required).reset_index(drop=True)

        # Validate ranges
        for col in required + (["n6"] if "n6" in df.columns else []):
            df = df[(df[col] >= 1) & (df[col] <= BALLS)].reset_index(drop=True)

        # Ensure n6 exists (for XL games)
        if "n6" not in df.columns:
            df["n6"] = df["n5"]  # fallback

        return df

    def __len__(self) -> int:
        return len(self.df)


def onehot_draw(row: pd.Series, balls: int = BALLS) -> np.ndarray:
    """Encode a draw row as one-hot vector (6 main numbers)."""
    arr = np.zeros(balls, dtype=np.float32)
    cols = ["n1", "n2", "n3", "n4", "n5", "n6"]
    for col in cols:
        if col in row.index:
            val = int(row[col])
            if 1 <= val <= balls:
                arr[val - 1] = 1.0
    return arr


def onehot_reserve(row: pd.Series, balls: int = BALLS) -> np.ndarray:
    """Encode reserve number as one-hot vector."""
    arr = np.zeros(balls, dtype=np.float32)
    val = int(row["reserve"])
    if 1 <= val <= balls:
        arr[val - 1] = 1.0
    return arr


def build_sequence_dataset(
    df: pd.DataFrame, lookback: int = 20
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List]:
    """
    Create sequence dataset for time-series prediction.

    Args:
        df: DataFrame with draws
        lookback: Number of historical draws per sequence

    Returns:
        Tuple[X, y_main, y_reserve, dates]
            X: (n_sequences, lookback, 45) - one-hot sequences
            y_main: (n_sequences, 45) - target main draw
            y_reserve: (n_sequences, 45) - target reserve (one-hot)
            dates: list of target dates (for tracking)
    """
    lookback_eff = min(lookback, max(1, len(df) - 1))

    X_list, y_main_list, y_res_list, dates = [], [], [], []

    for i in range(lookback_eff, len(df)):
        window = df.iloc[i - lookback_eff : i]
        X_list.append(np.stack([onehot_draw(r) for _, r in window.iterrows()], axis=0))
        y_main_list.append(onehot_draw(df.iloc[i]))
        y_res_list.append(onehot_reserve(df.iloc[i]))
        dates.append(df.iloc[i].get("date", i))

    if not X_list:
        raise ValueError(
            f"Cannot build sequences. df length={len(df)}, lookback={lookback}, "
            f"lookback_eff={lookback_eff}"
        )

    return np.stack(X_list), np.stack(y_main_list), np.stack(y_res_list), dates
