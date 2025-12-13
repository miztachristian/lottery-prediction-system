#!/bin/bash
# Quick Start Script for Netherlands Lottery Prediction System
# 
# Usage:
#   bash quickstart.sh predict          # Generate tickets
#   bash quickstart.sh backtest         # Run backtest
#   bash quickstart.sh demo             # Quick demo (short training)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Netherlands Lottery Prediction System - Quick Start${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️ Python 3 not found. Please install Python 3.8+ and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python found:${NC}"
python3 --version

# Check CSV
if [ ! -f "nl_lotto_xl_history.csv" ]; then
    echo -e "${YELLOW}⚠️ nl_lotto_xl_history.csv not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Data files found${NC}\n"

# Parse command
MODE="${1:-demo}"

case "$MODE" in
    predict)
        echo -e "${BLUE}Mode: PREDICT (Generate Tickets)${NC}"
        echo "Command: python3 main.py --csv nl_lotto_xl_history.csv --game xl --predict --epochs 30"
        echo ""
        python3 main.py --csv nl_lotto_xl_history.csv --game xl --predict --epochs 30
        ;;
        
    backtest)
        echo -e "${BLUE}Mode: BACKTEST (Evaluate Strategy)${NC}"
        echo "Command: python3 main.py --csv nl_lotto_xl_history.csv --game xl --backtest --start_tail 50"
        echo ""
        python3 main.py --csv nl_lotto_xl_history.csv --game xl --backtest --start_tail 50
        ;;
        
    demo)
        echo -e "${BLUE}Mode: DEMO (Quick Test, 5 epochs)${NC}"
        echo "Command: python3 main.py --csv nl_lotto_xl_history.csv --game xl --predict --epochs 5 --batch 32"
        echo ""
        python3 main.py --csv nl_lotto_xl_history.csv --game xl --predict --epochs 5 --batch 32
        ;;
        
    *)
        echo -e "${YELLOW}Usage:${NC}"
        echo "  bash quickstart.sh [MODE]"
        echo ""
        echo -e "${YELLOW}Modes:${NC}"
        echo "  predict   - Generate tickets for play (30 epochs)"
        echo "  backtest  - Run strategy backtest (50 recent draws)"
        echo "  demo      - Quick test (5 epochs, for verification)"
        echo ""
        echo -e "${YELLOW}Examples:${NC}"
        echo "  bash quickstart.sh predict"
        echo "  bash quickstart.sh backtest"
        echo "  bash quickstart.sh demo"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Complete${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
