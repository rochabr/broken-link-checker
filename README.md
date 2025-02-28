# Broken Link Checker

[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A robust Python utility for crawling websites and identifying broken links. This tool helps maintain website quality by detecting and reporting broken links, including internal links, external resources, images, and other media.

## 🚀 Features

- **Full Website Crawling**: Automatically traverses your entire website
- **Concurrent Processing**: Configurable multi-threading for faster scanning
- **Comprehensive Link Detection**: Checks `<a>` tags, images, scripts, iframes, and stylesheets
- **Smart Error Handling**: Multiple retry attempts with detailed error reporting
- **Domain Control**: Check only specific domains, the starting domain, or all domains
- **URL Ignoring**: Exclude specific URL patterns from being checked using regex
- **Markdown Support**: Smart handling of Markdown files that might be rendered as HTML
- **Report Generation**: Save results to a text file or view in the console
- **Detailed Reporting**: Clear summary of broken links with their respective HTTP status codes

## 📋 Requirements

- Python 3.6 or higher
- Required packages:
  - `requests`
  - `beautifulsoup4`

## 🔧 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/rochabr/broken-link-checker.git
   cd broken-link-checker
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Or install them directly:
   ```bash
   pip install requests beautifulsoup4
   ```

## 📖 Usage

### Basic Usage

```bash
python broken_link_checker.py https://your-website.com
```

### Command Line Options

```
usage: broken_link_checker.py [-h] [--threads THREADS] [--timeout TIMEOUT]
                             [--user-agent USER_AGENT] [--retries RETRIES]
                             [--all-domains | --allowed-domains ALLOWED_DOMAINS]
                             [--ignore PATTERN] [--output OUTPUT]
                             url

Crawl a website and check for broken links.

positional arguments:
  url                   The URL to start crawling from

optional arguments:
  -h, --help            show this help message and exit
  --threads THREADS     Maximum number of concurrent requests (default: 5)
  --timeout TIMEOUT     Request timeout in seconds (default: 10)
  --user-agent USER_AGENT
                        Custom user agent string (default: BrokenLinkChecker/1.0)
  --retries RETRIES     Number of times to retry failed requests (default: 2)
  --all-domains         Check links on all domains, not just the starting domain
  --allowed-domains ALLOWED_DOMAINS
                        List of domains to check. Can be used multiple times.
  --ignore PATTERN      Regex pattern for URLs to ignore. Can be used multiple times.
  --output OUTPUT, -o OUTPUT
                        Save the report to a file instead of printing to console
```

### Examples

Check only your domain with increased concurrency:
```bash
python broken_link_checker.py https://example.com --threads 10
```

Check external links as well:
```bash
python broken_link_checker.py https://example.com --all-domains
```

Increase timeout for slow servers:
```bash
python broken_link_checker.py https://example.com --timeout 20
```

Ignore specific URL patterns:
```bash
# Ignore admin pages and PDF files
python broken_link_checker.py https://example.com --ignore "\/admin" --ignore "\.pdf$"
```

Save the report to a file:
```bash
# Save results to a text file
python broken_link_checker.py https://example.com -o broken-links-report.txt
```

Combine multiple options:
```bash
# Comprehensive scan with report saving
python broken_link_checker.py https://example.com --threads 10 --all-domains --ignore "googletagmanager\.com" -o report.txt
```

Check only specific domains:
```bash
# Only check links on example.com and api.example.com
python broken_link_checker.py https://example.com --allowed-domains example.com --allowed-domains api.example.com
```

### Domain Control Options

The script offers three different ways to control which domains are crawled:

1. **Default Mode (No Flags)**: Only checks links on the same domain as the starting URL.
   ```bash
   python broken_link_checker.py https://example.com
   ```
   This will only check links within example.com.

2. **All Domains Mode**: Checks links on all domains encountered.
   ```bash
   python broken_link_checker.py https://example.com --all-domains
   ```
   This will check all links, regardless of domain.

3. **Allowed Domains Mode**: Only checks links on domains you specifically allow.
   ```bash
   python broken_link_checker.py https://example.com --allowed-domains example.com --allowed-domains docs.example.com
   ```
   This will only check links on example.com and docs.example.com.

Note: `--all-domains` and `--allowed-domains` are mutually exclusive and cannot be used together.

### Markdown File Handling

The script has special handling for Markdown (.md) files, which are commonly used in GitHub repositories but may be processed differently when served on websites. When encountering a Markdown file, the script will:

1. Try the original URL with `.md` extension
2. Try the URL with the `.md` extension removed
3. Try the URL with `.md` replaced by `.html`

This handles various ways websites might render Markdown:
- Serving the raw `.md` file directly
- Processing Markdown into HTML without changing the URL (common in static site generators)
- Converting `.md` files to `.html` files with the same base name

This prevents false positives when checking sites that use Markdown files.

## 📊 Sample Output

```
===================================================================
BROKEN LINK REPORT
===================================================================
Found 3 broken links across 2 pages.

Page: https://example.com/blog
  - https://example.com/missing-page (Status: 404)
  - https://example.com/images/deleted-image.jpg (Status: 404)

Page: https://example.com/contact
  - https://external-site.com/broken-link (Status: 500)

-------------------------------------------------------------------
Total URLs crawled: 42
External links found: 15
Only checked domain: example.com
-------------------------------------------------------------------
```

## 🧰 Advanced Usage

### As a Module

You can also import and use the `LinkChecker` class in your own Python scripts:

```python
from broken_link_checker import LinkChecker

checker = LinkChecker(
    start_url="https://example.com",
    max_threads=8,
    same_domain_only=True,
    ignore_patterns=[r"\/admin", r"\/login", r"\.pdf$"]
)

checker.crawl()
checker.print_report()

# Access the results programmatically
for page, links in checker.broken_links.items():
    print(f"Found {len(links)} broken links on {page}")
```

## 🛠️ Customization

### Creating a requirements.txt file

Create a `requirements.txt` file with the following content:

```
requests>=2.28.0
beautifulsoup4>=4.11.0
```

### Adding as a Scheduled Task

#### On Linux (using cron)

```bash
# Run daily at 1 AM
0 1 * * * cd /path/to/broken-link-checker && /path/to/python broken_link_checker.py https://your-website.com >> /path/to/logfile.log 2>&1
```

#### On Windows (using Task Scheduler)

Create a batch file `run_checker.bat`:

```batch
@echo off
cd /d "C:\path\to\broken-link-checker"
call venv\Scripts\activate
python broken_link_checker.py https://your-website.com > report.log
```

Then add this batch file to Windows Task Scheduler.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

⭐ Star this repo if you find it useful! ⭐