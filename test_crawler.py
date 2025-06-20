import logging
import sys
from jobs.crawler.bossjobs import BossJobsCrawler

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)

def test_crawler_titles():
    print("Testing BossJobs crawler title extraction...")
    crawler = BossJobsCrawler(max_jobs=3)
    
    # Get jobs from search
    jobs = crawler.search_jobs('software developer', 'Philippines')
    
    if not jobs:
        print("No jobs found")
        return
    
    # Print the first job's details for comparison
    job = jobs[0]
    print(f"\nSearch Results:")
    print(f"Title: '{job.get('title', 'Unknown')}'")
    print(f"Company: '{job.get('company', 'Unknown')}'")
    print(f"URL: {job.get('url', 'Unknown')}")
    
    # Get detailed job info
    print(f"\nFetching detailed job info...")
    details = crawler.get_job_details(job['url'])
    
    print(f"\nDetailed Results:")
    print(f"Title: '{details.get('title', 'Unknown')}'")
    print(f"Company: '{details.get('company', 'Unknown')}'")
    
    # Check if title is the same as company
    if job['title'].strip() == job['company'].strip():
        print("\nISSUE DETECTED: Title is the same as company in search results")
    else:
        print("\nSearch results OK: Title differs from company")
        
    if details['title'].strip() == details['company'].strip():
        print("ISSUE DETECTED: Title is the same as company in detailed view")
    else:
        print("Detailed view OK: Title differs from company")

if __name__ == "__main__":
    test_crawler_titles() 