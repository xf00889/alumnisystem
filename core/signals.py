"""
Core app signals
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.sites.models import Site
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='announcements.Announcement')
def schedule_web_push_for_published_announcement(sender, instance, created, **kwargs):
    if not created or not instance.is_active:
        return
    from django.db import transaction
    from core.web_push import queue_published_announcement
    transaction.on_commit(lambda: queue_published_announcement(instance.pk), robust=True)


@receiver(post_save, sender='core.Notification')
def schedule_browser_push_for_new_notification(sender, instance, created, **kwargs):
    if not created:
        return
    from django.db import transaction
    from core.web_push import queue_web_push
    # Transaction commits before queuing so no rolled-back alert can be pushed.
    transaction.on_commit(lambda: queue_web_push(instance.pk), robust=True)



@receiver(post_save, sender='core.SSOConfig')
def sync_sso_to_socialapp(sender, instance, created, **kwargs):
    """
    Automatically create or update SocialApp when SSOConfig is saved.
    This ensures django-allauth has the necessary SocialApp entries.
    """
    try:
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site
        from core.sso_utils import clear_sso_cache
        
        # Clear SSO cache
        clear_sso_cache()
        
        # Only sync if the config is active and enabled
        if not instance.is_active or not instance.enabled:
            # If config is disabled, remove the SocialApp
            try:
                social_app = SocialApp.objects.get(provider=instance.provider)
                social_app.delete()
                logger.info(f"Removed SocialApp for disabled provider: {instance.provider}")
            except SocialApp.DoesNotExist:
                pass
            return
        
        # Get or create SocialApp
        social_app, app_created = SocialApp.objects.get_or_create(
            provider=instance.provider,
            defaults={
                'name': instance.name,
                'client_id': instance.client_id,
                'secret': instance.secret_key,
            }
        )
        
        # Update if it already exists
        if not app_created:
            social_app.name = instance.name
            social_app.client_id = instance.client_id
            social_app.secret = instance.secret_key
            social_app.save()
        
        # Ensure all sites are added
        try:
            # Get current site
            current_site = Site.objects.get_current()
            
            # Clear existing sites and add current site
            social_app.sites.clear()
            social_app.sites.add(current_site)
            
            logger.info(f"Added site {current_site.domain} to SocialApp {instance.provider}")
        except Exception as site_error:
            logger.error(f"Error adding site to SocialApp: {str(site_error)}")
            # Try to add all sites as fallback
            try:
                all_sites = Site.objects.all()
                for site in all_sites:
                    social_app.sites.add(site)
                logger.info(f"Added all sites to SocialApp {instance.provider}")
            except Exception as fallback_error:
                logger.error(f"Error adding all sites to SocialApp: {str(fallback_error)}")
        
        action = "Created" if app_created else "Updated"
        logger.info(f"{action} SocialApp for {instance.provider}: {instance.name}")
        
    except Exception as e:
        logger.error(f"Error syncing SSOConfig to SocialApp: {str(e)}", exc_info=True)


@receiver(post_delete, sender='core.SSOConfig')
def remove_socialapp_on_delete(sender, instance, **kwargs):
    """
    Remove SocialApp when SSOConfig is deleted.
    """
    try:
        from allauth.socialaccount.models import SocialApp
        from core.sso_utils import clear_sso_cache
        
        # Clear SSO cache
        clear_sso_cache()
        
        # Check if there are any other active configs for this provider
        from core.models import SSOConfig
        other_active = SSOConfig.objects.filter(
            provider=instance.provider,
            is_active=True,
            enabled=True
        ).exists()
        
        # Only delete SocialApp if no other active configs exist
        if not other_active:
            try:
                social_app = SocialApp.objects.get(provider=instance.provider)
                social_app.delete()
                logger.info(f"Removed SocialApp for deleted provider: {instance.provider}")
            except SocialApp.DoesNotExist:
                pass
        
    except Exception as e:
        logger.error(f"Error removing SocialApp on delete: {str(e)}", exc_info=True)
