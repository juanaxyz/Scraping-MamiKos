#!/usr/bin/env python3
import sys


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "scrape":
            from src.scraper import run_main
            run_main()
        elif command == "retry":
            from src.retry_poi import run_retry
            run_retry()
        else:
            print("Usage: python run.py [scrape|retry]")
            print("")
            print("Commands:")
            print("  scrape  - Run main scraper for Mamikos data")
            print("  retry   - Retry failed POI enrichment")
            sys.exit(1)
    else:
        from src.scraper import run_main
        run_main()


if __name__ == "__main__":
    main()
