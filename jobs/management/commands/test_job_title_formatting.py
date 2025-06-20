import logging
from django.core.management.base import BaseCommand
from django.template import Template, Context
from jobs.templatetags.jobs_extras import format_job_title

class Command(BaseCommand):
    help = 'Test the job title formatting filter with various example titles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Testing Job Title Formatting"))
        self.stdout.write("=" * 80)
        
        # Job titles from various industries
        test_titles = [
            # Technology jobs
            "Senior Software Engineer - Python/Django",
            "Software Developer＄3-5K[Monthly]Remote · 1-3 Yrs Exp",
            "データエンジニア（Python、AWS）- Data Engineer (Python, AWS)",
            
            # Healthcare jobs
            "Registered Nurse - ICU - 3+ years experience",
            "Medical Doctor / Physician - General Practice",
            "Healthcare Administration Manager [Full-time]",
            
            # Finance jobs
            "Senior Accountant · 财务会计 · 5-7 Yrs",
            "Financial Analyst $50-70K/year DOE",
            "Bank Teller - Entry Level - No Experience Required",
            
            # Education jobs
            "University Professor - Computer Science Department",
            "Elementary School Teacher - Grade 3",
            "Early Childhood Educator - Preschool [Part-time]",
            
            # Hospitality jobs
            "Chef de Cuisine - 5 Star Hotel - 8+ years",
            "Restaurant Manager ★★★★★ $4-6K Monthly + Benefits",
            "Hotel Front Desk Receptionist - Night Shift",
            
            # Manufacturing jobs
            "Factory Production Line Supervisor · 工厂生产线主管",
            "Quality Control Inspector - Electronics Manufacturing",
            "CNC Machine Operator - 2nd Shift - $18-22/hr",
            
            # Administrative jobs
            "Executive Assistant to CEO - Confidential - $65K+",
            "Office Manager - Immediate Start - Central Location",
            "Administrative Support Specialist [Entry Level]",
            
            # Sales jobs
            "Senior Sales Representative - B2B Software Sales",
            "Retail Sales Associate - Fashion - PT/FT Available",
            "Territory Sales Manager - Medical Devices $$COMPETITIVE$$",
            
            # Creative jobs 
            "Graphic Designer - Branding Agency - Portfolio Required",
            "Content Writer & SEO Specialist - Digital Marketing Team",
            "Video Editor - Remote - Contract - 6 months", 
            
            # Construction jobs
            "Construction Project Manager - Commercial Buildings - 10+ years",
            "Electrician Apprentice - Training Provided - No Experience Necessary",
            "Civil Engineer - Infrastructure Projects - PE License Required"
        ]
        
        # Test each title
        for i, title in enumerate(test_titles, 1):
            formatted_title = format_job_title(title)
            self.stdout.write(f"\nExample #{i}:")
            self.stdout.write(f"Original: {title}")
            self.stdout.write(f"Formatted: {formatted_title}")
            self.stdout.write("-" * 80)
        
        self.stdout.write(self.style.SUCCESS("\nJob Title Formatting Test Complete")) 