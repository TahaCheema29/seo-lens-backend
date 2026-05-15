"""
Security Audit Script for SEO Lens

Run this to verify all data access is properly filtered by user_id
"""

import re
from pathlib import Path

def check_repository_security():
    """Check that all repository methods filter by user_id when needed"""
    backend_path = Path("/home/office/UNI/FYP/seo-lens-backend/src")
    
    issues = []
    
    # Check repository files
    for repo_file in backend_path.rglob("*repository*.py"):
        content = repo_file.read_text()
        
        # Look for get_all or list methods that don't filter by user
        if "def get_all" in content or "def list" in content or "def get_by_user" in content:
            if "user_id" not in content and "User" not in str(repo_file):
                issues.append(f"{repo_file}: May be missing user_id filtering")
    
    # Check router files
    for router_file in backend_path.rglob("*router*.py"):
        content = router_file.read_text()
        
        # Check if endpoints use get_current_user
        if "@router.get" in content or "@router.post" in content:
            if "get_current_user" not in content and "admin" not in str(router_file):
                # Check if it's a public endpoint (like website tools)
                if "(website)" not in str(router_file):
                    issues.append(f"{router_file}: Endpoint may be missing authentication")
    
    return issues

if __name__ == "__main__":
    issues = check_repository_security()
    if issues:
        print("Potential security issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("No obvious security issues found in repositories and routers.")
