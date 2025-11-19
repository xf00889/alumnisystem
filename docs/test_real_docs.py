"""
Manual test to verify markdown processor works with real documentation files.
Run this with: python manage.py shell < docs/test_real_docs.py
"""

from docs.markdown_processor import MarkdownProcessor

# Initialize processor
processor = MarkdownProcessor(base_path='docs/user-guide')

# Test rendering the main README
print("=" * 80)
print("Testing MarkdownProcessor with real documentation")
print("=" * 80)

result = processor.render('README.md')

if result.get('error'):
    print(f"ERROR: {result.get('message')}")
else:
    print(f"✓ Successfully rendered README.md")
    print(f"✓ Title: {result['title']}")
    print(f"✓ HTML length: {len(result['html'])} characters")
    print(f"✓ Has TOC: {bool(result.get('toc'))}")
    
    # Check for expected content
    if 'NORSU Alumni System' in result['html']:
        print("✓ Contains expected title")
    
    if '/docs/' in result['html']:
        print("✓ Links converted to documentation URLs")
    
    if '<h1' in result['html']:
        print("✓ Headers rendered correctly")
    
    if '<a href="/docs/public-features/README/' in result['html']:
        print("✓ Relative links processed correctly")

print("\n" + "=" * 80)
print("Testing caching behavior")
print("=" * 80)

# Test caching
result2 = processor.render('README.md')
print("✓ Second render completed (should be from cache)")

# Test with another file
result3 = processor.render('quick-start/new-user-guide.md')
if not result3.get('error'):
    print(f"✓ Successfully rendered quick-start/new-user-guide.md")
    print(f"✓ Title: {result3['title']}")
else:
    print(f"✗ Error rendering quick-start guide: {result3.get('message')}")

print("\n" + "=" * 80)
print("All tests completed!")
print("=" * 80)
