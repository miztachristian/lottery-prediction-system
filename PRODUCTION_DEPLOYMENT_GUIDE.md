# Production Deployment Guide
# Netherlands Lottery Prediction System

## System Overview

This production-ready system automatically:
- Updates lottery data from web sources
- Trains ML model on historical patterns
- Generates 24 optimized tickets (16 coverage + 8 convergence)
- Sends predictions via email
- Targets €100k+ wins (Tier 1: 6+1, Tier 2: 6+0)

## Directory Structure

```
data/
├── config.yaml                 # Production configuration
├── production_app.py           # Main production script
├── scheduler.py                # Automated scheduling
├── email_notifier.py           # Email delivery system
├── web_scraper.py              # Multi-source data scraper
├── data_pipeline.py            # Data processing
├── ml_model.py                 # ML model (Transformer)
├── constraint_generator.py     # Ticket generation
├── backtest_engine.py          # Backtesting
├── main.py                     # Original CLI tool
├── nl_lotto_xl_history.csv     # Historical data
├── logs/                       # Application logs
├── predictions/                # Generated predictions
└── backups/                    # Data backups
```

## Prerequisites

### Python Requirements
```bash
pip install tensorflow pandas numpy scikit-learn pyyaml croniter requests beautifulsoup4
```

### Email Setup
You need an email account with SMTP access. Recommended options:

**Gmail:**
1. Enable 2-factor authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use App Password in config.yaml (NOT your regular password)

**Outlook/Hotmail:**
- SMTP: smtp.office365.com
- Port: 587
- Use your regular password (App Passwords not required)

**Other providers:**
- Check your email provider's SMTP settings
- May require enabling "Less secure apps" or generating App Password

## Configuration

Edit `config.yaml`:

```yaml
email:
  enabled: true
  smtp_server: "smtp.gmail.com"      # Your SMTP server
  smtp_port: 587
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-password"  # Use App Password!
  recipient_email: "your-email@gmail.com"
  use_tls: true

lottery:
  game: "xl"                          # "xl" or "standard"
  csv_path: "nl_lotto_xl_history.csv"
  tickets:
    coverage: 16                      # Diversity tickets
    convergence: 8                    # Confidence tickets
  target_prize: 100000                # €100k minimum
  focus_tiers: [1, 2]                 # Tier 1: 6+1, Tier 2: 6+0

model:
  lookback: 20                        # Historical draws to consider
  epochs: 50                          # Training iterations
  batch_size: 8
  val_size: 0.2

data_update:
  auto_update: true                   # Fetch latest data automatically
  sources: ["lotteryguru", "lotteryextreme"]
  max_pages: 15                       # Scrape up to 15 pages
  min_draws: 50                       # Minimum draws required

scheduling:
  enabled: false                      # Enable for automation
  cron_schedule: "0 8 * * 3,6"        # 8 AM on Wed & Sat

logging:
  level: "INFO"
  file: "logs/lottery_predictions.log"
  console: true
```

## Usage

### 1. Test Email Configuration

Before running predictions, test your email setup:

```bash
python production_app.py --test-email
```

This sends 3 sample tickets to verify email delivery.

### 2. Run Manual Predictions

Generate and send predictions immediately:

```bash
python production_app.py
```

This will:
1. ✓ Update data from lotteryguru + lotteryextreme
2. ✓ Train ML model on latest data
3. ✓ Generate 24 optimized tickets
4. ✓ Save predictions to CSV/JSON
5. ✓ Send email with predictions

Output files:
- `predictions/predictions_lotto_xl_YYYYMMDD_HHMMSS.csv`
- `predictions/predictions_lotto_xl_YYYYMMDD_HHMMSS.json`

### 3. Automated Scheduling

For automatic predictions on draw days (Wednesday & Saturday):

**A. Edit config.yaml:**
```yaml
scheduling:
  enabled: true
  cron_schedule: "0 8 * * 3,6"  # 8 AM on Wed & Sat
```

**B. Run scheduler:**
```bash
python scheduler.py
```

**Cron Schedule Examples:**
- `"0 8 * * 3,6"` - 8 AM every Wednesday & Saturday
- `"30 7 * * 2,5"` - 7:30 AM every Tuesday & Friday
- `"0 20 * * *"` - 8 PM every day
- `"0 9 * * 1-5"` - 9 AM on weekdays

**C. Check next run time:**
```bash
python scheduler.py --next-run
```

**D. Run immediately (bypass schedule):**
```bash
python scheduler.py --run-now
```

### 4. Run as Background Service

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create New Task
3. Trigger: Weekly on Wed & Sat at 8 AM
4. Action: Start Program
   - Program: `python.exe`
   - Arguments: `C:\Users\chris\Desktop\data\production_app.py`
   - Start in: `C:\Users\chris\Desktop\data`

**Linux/Mac (crontab):**
```bash
crontab -e
```

Add line:
```
0 8 * * 3,6 cd /path/to/data && python3 production_app.py >> logs/cron.log 2>&1
```

## Email Format

Emails include:
- **Subject:** Netherlands Lottery Predictions - YYYY-MM-DD
- **Body:** 
  - Styled HTML with ticket grid
  - Total, Coverage, Convergence counts
  - Prize focus: €100k+ target
  - Individual tickets with main numbers + reserve
- **Attachment:** CSV file with all tickets

## Monitoring

### Check Logs
```bash
# View recent logs
Get-Content logs/lottery_predictions.log -Tail 50

# Search for errors
Select-String -Path logs/lottery_predictions.log -Pattern "ERROR"
```

### Test Components

**Test data scraping:**
```bash
python main.py --update-data --source both --scrape-pages 5
```

**Test model training:**
```bash
python main.py --generate
```

**Test email only:**
```bash
python production_app.py --test-email
```

## Ticket Strategy

The system generates 24 tickets optimized for €100k+ wins:

**16 Coverage Tickets (Diversity):**
- Explore different number combinations
- Mix hot, cold, and ML predictions
- Maximize winning space coverage

**8 Convergence Tickets (Confidence):**
- Focus on highest probability numbers
- ML model's top predictions
- Hot numbers from recent draws

**Prize Optimization:**
- Targets Tier 1 (6+1 match): ~€1M+
- Targets Tier 2 (6+0 match): ~€100k+
- `focus_tiers: [1, 2]` in config.yaml

## Data Sources

**Lotteryguru.com:**
- Pagination support (10+ draws per page)
- Fetches up to `max_pages` pages
- Reliable historical data

**Lotteryextreme.com:**
- Last 20 recent draws
- Quick updates

Data automatically deduplicates across sources.

## Troubleshooting

### Email Not Sending

**Gmail users:**
```
Error: Authentication failed
Solution: Use App Password, not regular password
  1. Enable 2FA on Google account
  2. Generate App Password: myaccount.google.com/apppasswords
  3. Use App Password in config.yaml
```

**Port blocked:**
```
Error: Connection refused on port 587
Solution: Try port 465 with SSL
  smtp_port: 465
  use_tls: false (will use SSL instead)
```

### Insufficient Data

```
Error: Insufficient data: 20 draws (minimum 50)
Solution: Increase scraping pages
  data_update:
    max_pages: 20  # Increase from 15
```

### Model Training Fails

```
Error: Not enough data for training
Solution: 
  1. Lower lookback window
     model:
       lookback: 10  # Reduce from 20
  
  2. Scrape more historical data
     data_update:
       max_pages: 25
```

### Scheduler Not Working

```
Error: croniter not installed
Solution:
  pip install croniter
```

## Security Best Practices

1. **Never commit config.yaml to Git:**
   ```bash
   echo "config.yaml" >> .gitignore
   ```

2. **Use environment variables for passwords:**
   ```python
   sender_password: ${SMTP_PASSWORD}
   ```
   
   Set in shell:
   ```bash
   $env:SMTP_PASSWORD = "your-app-password"
   ```

3. **Restrict file permissions:**
   ```bash
   # Linux/Mac
   chmod 600 config.yaml
   ```

4. **Use App Passwords (never regular passwords)**

5. **Enable logging for audit trail**

## Performance Tips

1. **Data Update Frequency:**
   - Update before each prediction run
   - No need to update multiple times per day

2. **Model Training:**
   - `epochs: 50` is good balance (speed vs accuracy)
   - Increase `lookback` if you have 100+ draws

3. **Email Size:**
   - CSV attachment is small (<10 KB)
   - HTML email renders well on all devices

4. **Scheduling:**
   - Run 1-2 hours before draw time
   - Wednesday & Saturday for Netherlands Lotto

## Advanced Features

### Custom Ticket Count
Edit `config.yaml`:
```yaml
lottery:
  tickets:
    coverage: 20    # More diversity
    convergence: 10  # More confidence
```

### Multi-Game Support
Run for both Lotto and Lotto XL:

**Config for Lotto XL:**
```yaml
lottery:
  game: "xl"
  csv_path: "nl_lotto_xl_history.csv"
```

**Config for Standard Lotto:**
```yaml
lottery:
  game: "standard"
  csv_path: "nl_lotto_history.csv"
```

Run separate configs:
```bash
python production_app.py --config config_xl.yaml
python production_app.py --config config_standard.yaml
```

### Backup Configuration
Automatic backups enabled in `config.yaml`:
```yaml
backup:
  enabled: true
  keep_days: 30
```

Backups saved to `backups/` directory.

## Expected Output

Successful run produces:

```
======================================================================
NETHERLANDS LOTTERY PREDICTION SYSTEM
======================================================================
INFO - Updating lottery data from web sources...
INFO - Scraping from lotteryguru...
INFO - Scraping from lotteryextreme...
INFO - ✓ Data updated: 98 draws available
======================================================================
GENERATING PREDICTIONS
======================================================================
INFO - Loading data from nl_lotto_xl_history.csv...
INFO - Loaded 98 historical draws
INFO - Training ML model...
INFO - ✓ Model trained successfully
INFO - Hot numbers: [3, 12, 18, 23, 31, 39, 42]
INFO - Cold numbers: [5, 14, 20, 27, 35, 41]
INFO - Generating optimized tickets...
INFO - ✓ Generated 24 tickets
INFO -   - Coverage: 16
INFO -   - Convergence: 8
INFO - ✓ Predictions saved:
INFO -   - JSON: predictions/predictions_lotto_xl_20250608_080000.json
INFO -   - CSV: predictions/predictions_lotto_xl_20250608_080000.csv
INFO - Sending predictions via email...
INFO - ✓ Email sent successfully
======================================================================
PREDICTION PIPELINE COMPLETED
======================================================================
INFO - ✓ Generated 24 tickets
INFO - ✓ Saved to: predictions/predictions_lotto_xl_20250608_080000.csv
INFO - ✓ Email sent: Yes
======================================================================
```

## Support

For issues or questions:
1. Check logs: `logs/lottery_predictions.log`
2. Test components individually
3. Verify configuration in `config.yaml`
4. Review this guide's Troubleshooting section

## Disclaimer

This system is for entertainment and educational purposes only. Lottery outcomes are random, and no system can guarantee wins. Play responsibly within your means.

---

**Good luck! 🍀**
