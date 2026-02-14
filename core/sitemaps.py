"""
Sitemap classes for SEO optimization.
Provides XML sitemap generation for static pages, events, and job postings.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from core.models.seo import PageSEO


class StaticPageSitemap(Sitemap):
    """
    Sitemap for static high-priority pages configured in PageSEO model.
    Includes pages like Home, About Us, Contact Us, Events Landing, and Careers.
    """
    protocol = 'https'
    
    def items(self):
        """
        Returns all active PageSEO objects.
        """
        return PageSEO.objects.filter(is_active=True)
    
    def location(self, obj):
        """
        Returns the URL path for the page.
        """
        return obj.page_path
    
    def lastmod(self, obj):
        """
        Returns the last modification date from the PageSEO updated_at field.
        """
        return obj.updated_at
    
    def changefreq(self, obj):
        """
        Returns the change frequency from the PageSEO sitemap_changefreq field.
        """
        return obj.sitemap_changefreq
    
    def priority(self, obj):
        """
        Returns the priority from the PageSEO sitemap_priority field.
        """
        return float(obj.sitemap_priority)


class EventSitemap(Sitemap):
    """
    Sitemap for public events.
    Includes all published and public events.
    """
    changefreq = 'daily'
    priority = 0.7
    protocol = 'https'
    
    def items(self):
        """
        Returns all public and published events.
        """
        from events.models import Event
        return Event.objects.filter(
            visibility='public',
            status='published'
        ).order_by('-start_date')
    
    def location(self, obj):
        """
        Returns the URL for the event detail page.
        Uses the public event detail URL pattern.
        """
        return reverse('events:public_event_detail', kwargs={'pk': obj.pk})
    
    def lastmod(self, obj):
        """
        Returns the last modification date from the Event updated_at field.
        """
        return obj.updated_at


class JobSitemap(Sitemap):
    """
    Sitemap for active job postings.
    Includes all active and published job postings.
    """
    changefreq = 'daily'
    priority = 0.8
    protocol = 'https'
    
    def items(self):
        """
        Returns all active job postings.
        """
        from jobs.models import JobPosting
        return JobPosting.objects.filter(
            is_active=True
        ).order_by('-posted_date')
    
    def location(self, obj):
        """
        Returns the URL for the job detail page.
        Uses the slug-based job detail URL pattern.
        """
        return reverse('jobs:job_detail', kwargs={'slug': obj.slug})
    
    def lastmod(self, obj):
        """
        Returns the last modification date.
        Since JobPosting doesn't have updated_at, uses posted_date.
        """
        return obj.posted_date
