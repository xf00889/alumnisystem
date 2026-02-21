from django import template
import os
import re

register = template.Library()

@register.filter
def filename(value):
    """Returns the filename from a file path."""
    return os.path.basename(str(value))

@register.filter
def is_hr_or_admin(user):
    """Check if user is HR, admin, or alumni coordinator"""
    if not user.is_authenticated:
        return False
    
    # Superusers and staff always have access
    if user.is_superuser or user.is_staff:
        return True
    
    # Check HR status or alumni coordinator status
    try:
        return user.profile.is_hr or user.profile.is_alumni_coordinator
    except:
        return False

@register.filter
def get_item(dictionary, key):
    """Gets an item from a dictionary by key."""
    return dictionary.get(key)

@register.filter
def status_color(status):
    """Maps job application status to a Bootstrap color class."""
    status_colors = {
        'PENDING': 'secondary',
        'REVIEWING': 'info',
        'SHORTLISTED': 'primary',
        'INTERVIEWED': 'warning',
        'ACCEPTED': 'success',
        'REJECTED': 'danger'
    }
    return status_colors.get(status, 'secondary')

@register.filter
def format_job_title(job_title):
    """
    Formats job titles for display.
    - Preserves complete job titles when possible
    - Cleans up salary and experience info
    - Removes special characters
    - Handles multilingual titles
    """
    if not job_title:
        return ""
    
    # Store the original title for fallback
    original_title = job_title.strip()
    
    # First, clean up common patterns that add noise to titles
    
    # Remove salary patterns: $50-70K, ＄3-5K, $65K+, etc.
    clean_title = re.sub(r'[\$＄]\s*\d+(?:[\-\.]\d+)?[KMB]?(?:\+|\s|\/|$)', ' ', original_title)
    
    # Remove experience patterns: 1-3 Yrs Exp, 3+ years, etc.
    clean_title = re.sub(r'\b\d+(?:[\-\+]\d+)?\s*(?:years?|yrs?)\b.*?(?=\s|$)', ' ', clean_title, flags=re.IGNORECASE)
    
    # Remove date/time patterns: 2nd Shift, Night Shift, etc.
    clean_title = re.sub(r'\b(?:\d+(?:st|nd|rd|th)?\s+shift|night\s+shift|day\s+shift)\b', ' ', clean_title, flags=re.IGNORECASE)
    
    # Remove blocky items in brackets: [Monthly], [Remote], [Full-time], [Part-time], etc.
    clean_title = re.sub(r'\[.*?\]', ' ', clean_title)
    
    # Remove special star characters and other decorative symbols
    clean_title = re.sub(r'[★☆♥♦♣♠✓✔➤➢➥❖◆◇◈◉]+', ' ', clean_title)
    
    # Remove currency/compensation markers
    clean_title = re.sub(r'\$\$[A-Z]+\$\$', ' ', clean_title)  # $$COMPETITIVE$$
    clean_title = re.sub(r'(?:\d+\-\d+K|\d+K)(?:\s*Monthly|\s*\+\s*Benefits|\s*\/\s*year|\s*DOE)?', ' ', clean_title, flags=re.IGNORECASE)
    
    # Replace common non-letter separators with spaces while preserving important ones
    clean_title = re.sub(r'[\/\|\(\)\[\]\{\}\<\>]', ' ', clean_title)
    
    # Keep hyphens within words but replace standalone hyphens with spaces
    clean_title = re.sub(r'(?<!\w)\-(?!\w)', ' ', clean_title)
    
    # Special handling for Japanese/Chinese characters - try to find English part
    if re.search(r'[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\u3400-\u4dbf]', clean_title):
        # Look for the English part that often follows
        english_part_match = re.search(r'[-\s\(]+([A-Za-z].*?)(?:\s*[\)\s]|$)', clean_title)
        if english_part_match:
            english_part = english_part_match.group(1).strip()
            if len(english_part) > 10:  # If we have a substantial English part, use it
                return english_part
    
    # Clean up whitespace thoroughly
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    
    # If the cleaning removed too much (less than 60% of original non-space content remains),
    # or the title became very short, revert to the original
    original_content_len = len(re.sub(r'\s+', '', original_title))
    cleaned_content_len = len(re.sub(r'\s+', '', clean_title))
    
    if cleaned_content_len < 10 or (original_content_len > 0 and cleaned_content_len / original_content_len < 0.6):
        # For very long titles, truncate to reasonable length
        if len(original_title) > 70:
            # Try to find a good cutoff point (space) near 60 characters
            cutoff = 60
            while cutoff < min(70, len(original_title)) and original_title[cutoff] != ' ':
                cutoff += 1
            return original_title[:cutoff].strip() + "..."
        return original_title
    
    # Check final title doesn't end abruptly with partial words
    # Try to find complete words until we have enough characters
    words = clean_title.split()
    if len(words) >= 2:  # Ensure we have at least 2 words
        return clean_title
    else:
        # If we're down to just one word, the cleaning was too aggressive
        # Return original with potential truncation for very long titles
        if len(original_title) > 70:
            return original_title[:60].strip() + "..."
        return original_title