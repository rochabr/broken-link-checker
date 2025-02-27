#!/usr/bin/env python3
"""
Webpage Crawler and Broken Link Checker

This script crawls a website starting from a given URL and checks for broken links.
It reports all broken links found along with their HTTP status codes.
"""

import argparse
import concurrent.futures
import re
import time
from collections import defaultdict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class LinkChecker:
    def __init__(self, start_url, max_threads=5, user_agent=None, timeout=10, 
                 max_retries=2, same_domain_only=True, ignore_patterns=None):
        """
        Initialize the link checker with configuration parameters.
        
        Args:
            start_url (str): The URL to start crawling from
            max_threads (int): Maximum number of concurrent requests
            user_agent (str): Custom user agent string
            timeout (int): Request timeout in seconds
            max_retries (int): Number of times to retry failed requests
            same_domain_only (bool): Whether to only check links on the same domain
            ignore_patterns (list): List of regex patterns for URLs to ignore
        """
        self.start_url = start_url
        self.max_threads = max_threads
        self.timeout = timeout
        self.max_retries = max_retries
        self.same_domain_only = same_domain_only
        
        # Extract the domain from the start URL
        self.domain = urlparse(start_url).netloc
        
        # Set up headers with a user agent
        self.headers = {
            'User-Agent': user_agent or 'BrokenLinkChecker/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        # Initialize collections
        self.visited_urls = set()
        self.to_visit = set([start_url])
        self.broken_links = defaultdict(list)
        self.external_links = set()
        
        # Compile regex patterns for URLs to ignore
        self.ignore_patterns = []
        if ignore_patterns:
            for pattern in ignore_patterns:
                self.ignore_patterns.append(re.compile(pattern))

    def should_visit(self, url):
        """
        Determine if a URL should be visited based on domain rules.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if the URL should be visited, False otherwise
        """
        # Skip non-HTTP URLs (like mailto:, tel:, javascript:)
        if not url.startswith(('http://', 'https://')):
            return False
            
        # Skip already visited URLs
        if url in self.visited_urls:
            return False
            
        # Skip URLs matching ignore patterns
        for pattern in self.ignore_patterns:
            if pattern.search(url):
                return False
            
        # If we're checking same domain only, verify the domain
        if self.same_domain_only:
            url_domain = urlparse(url).netloc
            if url_domain != self.domain:
                self.external_links.add(url)
                return False
                
        return True

    def extract_links(self, url, html_content):
        """
        Extract all links from the HTML content.
        
        Args:
            url (str): The base URL for resolving relative links
            html_content (str): HTML content to parse
            
        Returns:
            set: Set of absolute URLs found in the content
        """
        links = set()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all <a> tags with href attributes
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            # Remove fragment identifiers
            absolute_url = re.sub(r'#.*$', '', absolute_url)
            
            if absolute_url:
                links.add(absolute_url)
                
        # Also check other elements that might have links
        for tag in soup.find_all(['img', 'script', 'link', 'iframe']):
            src = tag.get('src') or tag.get('href')
            if src:
                absolute_url = urljoin(url, src)
                links.add(absolute_url)
                
        return links

    def check_url(self, url):
        """
        Check if a URL is valid (returns a 200-level status code).
        
        Args:
            url (str): URL to check
            
        Returns:
            tuple: (URL, status_code or exception message)
        """
        # Special handling for Markdown files that might be converted to HTML
        is_markdown = url.lower().endswith('.md')
        if is_markdown:
            # Try alternative URL without .md extension
            alt_url = url[:-3]  # Remove .md
            html_url = url[:-3] + '.html'  # Replace .md with .html
            
            urls_to_try = [url, alt_url, html_url]
        else:
            urls_to_try = [url]
            
        for attempt in range(self.max_retries + 1):
            for try_url in urls_to_try:
                try:
                    response = requests.head(try_url, headers=self.headers, 
                                            timeout=self.timeout, allow_redirects=True)
                    
                    # If head request fails, try a GET request
                    if response.status_code >= 400:
                        response = requests.get(try_url, headers=self.headers, 
                                               timeout=self.timeout, allow_redirects=True,
                                               stream=True)
                        # Close the connection immediately to save bandwidth
                        response.close()
                    
                    # If any URL version succeeds, consider it a success
                    if response.status_code < 400:
                        return url, response.status_code, None
                        
                except requests.RequestException:
                    # Try the next URL version
                    continue
            
            # If we've tried all URL versions and none worked, wait and retry
            if attempt < self.max_retries:
                time.sleep(1)
        
        # If we get here, all attempts failed
        try:
            # Make a final attempt to get a status code for reporting
            response = requests.head(url, headers=self.headers, 
                                    timeout=self.timeout, allow_redirects=True)
            return url, response.status_code, None
        except requests.RequestException as e:
            return url, None, str(e)

    def crawl(self):
        """
        Start crawling the website and checking for broken links.
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            while self.to_visit:
                current_url = self.to_visit.pop()
                self.visited_urls.add(current_url)
                
                print(f"Checking: {current_url}")
                
                # Get page content
                try:
                    response = requests.get(current_url, headers=self.headers, 
                                           timeout=self.timeout)
                    
                    # Skip non-HTML responses
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' not in content_type.lower():
                        continue
                        
                    # Extract links
                    links = self.extract_links(current_url, response.text)
                    
                    # Filter links to visit
                    new_links = set()
                    to_check = set()
                    
                    for link in links:
                        # Add to visit queue if it's on the same domain
                        if self.should_visit(link):
                            new_links.add(link)
                            
                        # Still check the link even if we won't crawl it
                        # (for external links or already visited ones)
                        if link not in self.visited_urls:
                            to_check.add(link)
                    
                    # Add new links to visit
                    self.to_visit.update(new_links)
                    
                    # Check links in parallel
                    future_to_url = {executor.submit(self.check_url, url): url for url in to_check}
                    for future in concurrent.futures.as_completed(future_to_url):
                        url, status_code, error = future.result()
                        
                        # Record broken links
                        if (status_code and status_code >= 400) or error:
                            self.broken_links[current_url].append((url, status_code, error))
                
                except Exception as e:
                    print(f"Error crawling {current_url}: {e}")
                    # Record as broken
                    self.broken_links["script_error"].append((current_url, None, str(e)))

    def print_report(self, output_file=None):
        """
        Print a report of broken links found.
        
        Args:
            output_file (str, optional): Path to file where the report should be saved
        """
        # Prepare the report as a list of strings
        report_lines = []
        report_lines.append("="*80)
        report_lines.append("BROKEN LINK REPORT")
        report_lines.append("="*80)
        
        if not self.broken_links:
            report_lines.append("No broken links found! 🎉")
        else:
            total_broken = sum(len(links) for links in self.broken_links.values())
            report_lines.append(f"Found {total_broken} broken links across {len(self.broken_links)} pages.")
            report_lines.append("")
            
            for page, links in self.broken_links.items():
                report_lines.append(f"Page: {page}")
                for link, status_code, error in links:
                    if status_code:
                        report_lines.append(f"  - {link} (Status: {status_code})")
                    else:
                        report_lines.append(f"  - {link} (Error: {error})")
                report_lines.append("")
                
            # Print some statistics
            report_lines.append("-"*80)
            report_lines.append(f"Total URLs crawled: {len(self.visited_urls)}")
            report_lines.append(f"External links found: {len(self.external_links)}")
            report_lines.append("-"*80)
        
        # Join all lines with newlines
        report_text = "\n".join(report_lines)
        
        # Either print to console or save to file
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_text)
                print(f"Report saved to {output_file}")
            except Exception as e:
                print(f"Error saving report to {output_file}: {e}")
                print(report_text)
        else:
            print(report_text)


def main():
    """
    Main function to parse arguments and run the link checker.
    """
    parser = argparse.ArgumentParser(description="Crawl a website and check for broken links.")
    
    parser.add_argument("url", help="The URL to start crawling from")
    parser.add_argument("--threads", type=int, default=5, 
                        help="Maximum number of concurrent requests (default: 5)")
    parser.add_argument("--timeout", type=int, default=10, 
                        help="Request timeout in seconds (default: 10)")
    parser.add_argument("--user-agent", 
                        help="Custom user agent string (default: BrokenLinkChecker/1.0)")
    parser.add_argument("--retries", type=int, default=2, 
                        help="Number of times to retry failed requests (default: 2)")
    parser.add_argument("--all-domains", action="store_true", 
                        help="Check links on all domains, not just the starting domain")
    parser.add_argument("--ignore", action="append", default=[], 
                        help="Regex pattern for URLs to ignore. Can be used multiple times.")
    parser.add_argument("--output", "-o", 
                        help="Save the report to a file instead of printing to console")
    
    args = parser.parse_args()
    
    print(f"Starting link check from: {args.url}")
    
    checker = LinkChecker(
        args.url,
        max_threads=args.threads,
        user_agent=args.user_agent,
        timeout=args.timeout,
        max_retries=args.retries,
        same_domain_only=not args.all_domains,
        ignore_patterns=args.ignore
    )
    
    try:
        print("Crawling website...")
        checker.crawl()
        checker.print_report(args.output)
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user.")
        checker.print_report(args.output)
    
    return 0


if __name__ == "__main__":
    main()