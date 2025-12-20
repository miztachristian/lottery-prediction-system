#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Orchestrator: Tie together data, model, constraints, and backtest.

Usage:
    python main.py --csv nl_lotto_xl_history.csv --game xl --predict
    python main.py --csv nl_lotto_xl_history.csv --game xl --backtest --start_tail 100
"""

import argparse
import os
import sys
import random
import numpy as np
import tensorflow as tf

from data_pipeline import LottoData, build_sequence_dataset
from ml_model import build_model, train_model, predict_probs
from constraint_generator import TicketGenerator, TicketConfig
from backtest_engine import BacktestEngine


def set_seeds(seed: int = 7):
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


class LottoSystem:
    """Complete lottery prediction system."""

    def __init__(self, csv_path: str, game: str = "xl", seed: int = 7):
        """
        Args:
            csv_path: Path to history CSV
            game: "xl" or "lotto"
            seed: Random seed
        """
        self.csv_path = csv_path
        self.game = game
        self.seed = seed
        set_seeds(seed)

        # Load data
        self.data = LottoData(csv_path, game)
        print(f"\n✓ Loaded {len(self.data)} draws")

        # Initialize generator
        self.ticket_gen = TicketGenerator(config=TicketConfig(game=game, random_seed=seed))
        self.model = None
        self.history = None

    def train(
        self,
        lookback: int = 20,
        epochs: int = 40,
        batch_size: int = 64,
        val_size: int = 24,
        verbose: int = 1,
    ):
        """Train the model."""
        print(f"\n{'='*70}")
        print(f"TRAINING MODEL")
        print(f"{'='*70}")

        df = self.data.get_df()
        X, y_main, y_res, dates = build_sequence_dataset(df, lookback=lookback)

        print(f"Dataset shape: X={X.shape}, y_main={y_main.shape}, y_res={y_res.shape}")

        # Split
        val_size_eff = min(val_size, max(1, len(X) // 4))
        i_split = max(1, len(X) - val_size_eff)

        X_train, X_val = X[:i_split], X[i_split:]
        y_main_train, y_main_val = y_main[:i_split], y_main[i_split:]
        y_res_train, y_res_val = y_res[:i_split], y_res[i_split:]

        print(f"Train: {len(X_train)}, Val: {len(X_val)}")

        # Build & train model
        self.model = build_model(lookback=X.shape[1])

        self.history = train_model(
            self.model,
            X_train,
            y_main_train,
            y_res_train,
            X_val,
            y_main_val,
            y_res_val,
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose,
        )

        print(f"\n✓ Training complete")

    def predict(self, num_coverage: int = 16, num_convergence: int = 8):
        """Generate tickets using trained model."""
        if self.model is None:
            raise ValueError("Must train model first with .train()")

        print(f"\n{'='*70}")
        print(f"GENERATING TICKETS")
        print(f"{'='*70}")

        df = self.data.get_df()
        X, y_main, y_res, _ = build_sequence_dataset(df, lookback=self.model.input_shape[1])

        # Get last sequence
        X_last = X[-1:, :, :]

        # Predict
        main_probs, reserve_probs = predict_probs(self.model, X_last, verbose=0)
        main_probs = main_probs[0]  # (45,)

        # Compute hot/cold numbers
        hot_nums, cold_nums = self.data.compute_hot_cold(recent_window=20)

        print(f"Hot numbers: {sorted(hot_nums)}")
        print(f"Cold (overdue) numbers: {sorted(cold_nums)}")

        # Generate tickets
        tickets_dict = self.ticket_gen.generate(
            main_probs,
            num_coverage=num_coverage,
            num_convergence=num_convergence,
            hot_numbers=hot_nums,
            cold_numbers=cold_nums,
        )

        self._print_tickets(tickets_dict, main_probs)
        return tickets_dict, main_probs, reserve_probs

    def backtest(self, lookback: int = 20, epochs: int = 20, batch_size: int = 64,
                 val_size: int = 24, start_tail: int = None, num_coverage: int = 16,
                 num_convergence: int = 8):
        """Run rolling backtest."""
        print(f"\n{'='*70}")
        print(f"BACKTEST")
        print(f"{'='*70}")

        df = self.data.get_df()

        if start_tail and start_tail > 0 and start_tail < len(df):
            df = df.iloc[-start_tail:].reset_index(drop=True)
            print(f"Using last {len(df)} draws")

        engine = BacktestEngine(game=self.game)

        # Rolling evaluation
        for t in range(max(lookback + 1, 10), len(df)):
            df_train = df.iloc[:t]
            df_eval = df.iloc[t]

            print(f"\n[{t}/{len(df)}] Evaluating {df_eval.get('date', t)}...", end=" ")

            try:
                # Train on history up to t
                X, y_main, y_res, _ = build_sequence_dataset(df_train, lookback=lookback)

                if len(X) < 2:
                    print("SKIP (insufficient data)")
                    continue

                # Quick training
                val_size_eff = min(val_size, max(1, len(X) // 4))
                i_split = max(1, len(X) - val_size_eff)

                X_train, X_val = X[:i_split], X[i_split:]
                y_main_train, y_main_val = y_main[:i_split], y_main[i_split:]
                y_res_train, y_res_val = y_res[:i_split], y_res[i_split:]

                model = build_model(lookback=X.shape[1])
                train_model(
                    model, X_train, y_main_train, y_res_train,
                    X_val, y_main_val, y_res_val,
                    epochs=epochs, batch_size=batch_size, verbose=0
                )

                # Predict
                main_probs, _ = predict_probs(model, X[-1:], verbose=0)
                main_probs = main_probs[0]

                # Generate tickets
                hot_nums, cold_nums = self.data.compute_hot_cold(recent_window=20)
                tickets_dict = self.ticket_gen.generate(
                    main_probs, num_coverage, num_convergence, hot_nums, cold_nums
                )
                all_tickets = tickets_dict["coverage"] + tickets_dict["convergence"]

                # Evaluate
                actual_draw = {
                    "date": str(df_eval.get("date", t)),
                    "main": self.data.extract_main_numbers(df_eval),
                    "reserve": self.data.extract_reserve(df_eval),
                }

                result = engine.evaluate_set(all_tickets, actual_draw)
                print(f"Best: {result.best_match}, 3-hits: {result.hits_3}, 4+: {result.hits_4}")

            except Exception as e:
                print(f"ERROR: {e}")
                continue

        # Summary
        engine.compute_metrics()
        engine.print_summary()
        return engine

    def _print_tickets(self, tickets_dict: dict, main_probs: np.ndarray):
        """Pretty-print tickets."""
        print(f"\nGame: {self.game.upper()}")
        print(f"\nCOVERAGE TICKETS (broad statistical coverage):")
        for i, ticket in enumerate(tickets_dict["coverage"], 1):
            prob_str = ", ".join(f"{n}:{main_probs[n-1]:.3f}" for n in ticket)
            print(f"  {i:02d}) {ticket} → {prob_str}")

        print(f"\nCONVERGENCE TICKETS (aggressive, high-variance):")
        for i, ticket in enumerate(tickets_dict["convergence"], 1):
            prob_str = ", ".join(f"{n}:{main_probs[n-1]:.3f}" for n in ticket)
            print(f"  {i:02d}) {ticket} → {prob_str}")

        # Show top-15 by probability
        top_idx = np.argsort(-main_probs)[:15] + 1
        print(f"\nTop 15 Balls by Model Probability:")
        print(", ".join(f"{int(b)}:{main_probs[b-1]:.3f}" for b in top_idx))


def main():
    parser = argparse.ArgumentParser(
        description="Netherlands Lottery Prediction System (Lotto / Lotto XL)"
    )
    parser.add_argument("--csv", required=True, help="Path to history CSV")
    parser.add_argument("--game", choices=["lotto", "xl"], default="xl", help="Game type")
    parser.add_argument("--lookback", type=int, default=20, help="History window (K)")
    parser.add_argument("--epochs", type=int, default=40, help="Training epochs")
    parser.add_argument("--batch", type=int, default=64, help="Batch size")
    parser.add_argument("--val_size", type=int, default=24, help="Validation window")
    parser.add_argument("--seed", type=int, default=7, help="Random seed")

    # Modes
    parser.add_argument("--predict", action="store_true", help="Train & predict (default)")
    parser.add_argument("--backtest", action="store_true", help="Run rolling backtest")
    parser.add_argument("--update-data", action="store_true", help="Fetch additional data from web")
    parser.add_argument("--scrape-pages", type=int, default=5, help="Pages/months to scrape when updating data")
    parser.add_argument("--source", choices=["lotteryguru", "lotteryextreme", "both"], 
                       default="both", help="Data source for scraping")
    parser.add_argument("--start-year", type=int, help="Starting year for date range scraping")
    parser.add_argument("--start-month", type=int, help="Starting month for date range scraping")
    parser.add_argument("--end-year", type=int, help="Ending year for date range scraping")
    parser.add_argument("--end-month", type=int, help="Ending month for date range scraping")
    parser.add_argument("--start_tail", type=int, default=None,
                        help="Use only last N draws for backtest (speed)")

    # Ticket generation
    parser.add_argument("--num_coverage", type=int, default=16, help="Coverage tickets")
    parser.add_argument("--num_convergence", type=int, default=8, help="Convergence tickets")

    args = parser.parse_args()

    # Handle data update mode
    if args.update_data:
        print(f"\n{'='*70}")
        print(f"UPDATING DATA: {args.csv}")
        print(f"{'='*70}")
        print(f"Source: {args.source}")
        print(f"Max pages/months: {args.scrape_pages}")
        if args.start_year and args.start_month:
            print(f"Date range: {args.start_year}-{args.start_month:02d} to {args.end_year or 'now'}-{args.end_month or 'now'}")
        print(f"{'='*70}\n")
        
        data = LottoData(args.csv, game=args.game)
        success = data.update_with_scraped_data(
            max_pages=args.scrape_pages,
            source=args.source,
            start_year=args.start_year,
            start_month=args.start_month,
            end_year=args.end_year,
            end_month=args.end_month
        )
        
        if success:
            print(f"\n{'='*70}")
            print("✅ DATA UPDATE COMPLETED SUCCESSFULLY")
            print(f"{'='*70}")
        else:
            print(f"\n{'='*70}")
            print("❌ DATA UPDATE FAILED")
            print(f"{'='*70}")
        return

    # Check file exists
    if not os.path.isfile(args.csv):
        print(f"ERROR: File not found: {args.csv}")
        sys.exit(1)

    # Initialize system
    system = LottoSystem(args.csv, game=args.game, seed=args.seed)

    # Run
    if args.backtest:
        system.train(lookback=args.lookback, epochs=args.epochs, batch_size=args.batch,
                    val_size=args.val_size, verbose=0)
        system.backtest(lookback=args.lookback, epochs=args.epochs, batch_size=args.batch,
                       val_size=args.val_size, start_tail=args.start_tail,
                       num_coverage=args.num_coverage, num_convergence=args.num_convergence)
    else:  # Predict
        system.train(lookback=args.lookback, epochs=args.epochs, batch_size=args.batch,
                    val_size=args.val_size, verbose=1)
        system.predict(num_coverage=args.num_coverage, num_convergence=args.num_convergence)


if __name__ == "__main__":
    main()
