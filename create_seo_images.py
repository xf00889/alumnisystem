"""
Script to create default SEO social media images for NORSU Alumni System.
Creates optimized images for Open Graph and Twitter Cards.
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_default_social_card():
    """Create default Open Graph image (1200x630)"""
    # Create image with NORSU brand colors
    img = Image.new('RGB', (1200, 630), color='#1a472a')  # NORSU green
    draw = ImageDraw.Draw(img)
    
    # Try to use a system font, fallback to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 72)
        subtitle_font = ImageFont.truetype("arial.ttf", 36)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Add text
    title = "NORSU Alumni System"
    subtitle = "Connect, Network, Grow"
    
    # Calculate text positions (centered)
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (1200 - title_width) // 2
    
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (1200 - subtitle_width) // 2
    
    # Draw text with white color
    draw.text((title_x, 220), title, fill='white', font=title_font)
    draw.text((subtitle_x, 340), subtitle, fill='#f0f0f0', font=subtitle_font)
    
    # Add decorative elements
    draw.rectangle([100, 180, 1100, 185], fill='#ffd700')  # Gold line
    draw.rectangle([100, 445, 1100, 450], fill='#ffd700')  # Gold line
    
    # Ensure directory exists
    os.makedirs('static/images/seo', exist_ok=True)
    
    # Save with optimization
    img.save('static/images/seo/default-social-card.jpg', 'JPEG', quality=85, optimize=True)
    print(f"Created default-social-card.jpg ({os.path.getsize('static/images/seo/default-social-card.jpg')} bytes)")

def create_default_twitter_card():
    """Create default Twitter Card image (800x418)"""
    # Create image with NORSU brand colors
    img = Image.new('RGB', (800, 418), color='#1a472a')  # NORSU green
    draw = ImageDraw.Draw(img)
    
    # Try to use a system font, fallback to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        subtitle_font = ImageFont.truetype("arial.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Add text
    title = "NORSU Alumni"
    subtitle = "Connect, Network, Grow"
    
    # Calculate text positions (centered)
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (800 - title_width) // 2
    
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (800 - subtitle_width) // 2
    
    # Draw text with white color
    draw.text((title_x, 150), title, fill='white', font=title_font)
    draw.text((subtitle_x, 230), subtitle, fill='#f0f0f0', font=subtitle_font)
    
    # Add decorative elements
    draw.rectangle([80, 120, 720, 123], fill='#ffd700')  # Gold line
    draw.rectangle([80, 295, 720, 298], fill='#ffd700')  # Gold line
    
    # Ensure directory exists
    os.makedirs('static/images/seo', exist_ok=True)
    
    # Save with optimization
    img.save('static/images/seo/default-twitter-card.jpg', 'JPEG', quality=85, optimize=True)
    print(f"Created default-twitter-card.jpg ({os.path.getsize('static/images/seo/default-twitter-card.jpg')} bytes)")

if __name__ == '__main__':
    print("Creating default SEO social media images...")
    create_default_social_card()
    create_default_twitter_card()
    print("Done! Images created in static/images/seo/")
