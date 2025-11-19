/**
 * Documentation Viewer JavaScript
 * Handles sidebar toggle, scroll behavior, and interactive features
 */

(function() {
    'use strict';
    
    console.log('Documentation JS: File loaded successfully');

    // ============================================
    // DOM Elements
    // ============================================
    const sidebar = document.getElementById('docsSidebar');
    const sidebarToggle = document.getElementById('docsSidebarToggle');
    const sidebarClose = document.getElementById('docsSidebarClose');
    const sidebarOverlay = document.getElementById('docsSidebarOverlay');
    const scrollToTopBtn = document.getElementById('scrollToTop');

    // ============================================
    // Sidebar Toggle Functionality
    // ============================================
    
    /**
     * Open the sidebar (mobile)
     * Requirements: 8.1, 8.2
     */
    function openSidebar() {
        if (sidebar) {
            sidebar.classList.add('active');
            sidebar.setAttribute('aria-hidden', 'false');
        }
        if (sidebarOverlay) {
            sidebarOverlay.classList.add('active');
            sidebarOverlay.setAttribute('aria-hidden', 'false');
        }
        if (sidebarToggle) {
            sidebarToggle.setAttribute('aria-expanded', 'true');
        }
        
        // Prevent body scroll when sidebar is open
        document.body.style.overflow = 'hidden';
        document.body.classList.add('sidebar-open');
        
        // Set focus to first focusable element in sidebar for accessibility
        setTimeout(function() {
            const firstFocusable = sidebar.querySelector('a, button, input');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        }, 100);
    }

    /**
     * Close the sidebar (mobile)
     * Requirements: 8.1, 8.2
     */
    function closeSidebar() {
        if (sidebar) {
            sidebar.classList.remove('active');
            sidebar.setAttribute('aria-hidden', 'true');
        }
        if (sidebarOverlay) {
            sidebarOverlay.classList.remove('active');
            sidebarOverlay.setAttribute('aria-hidden', 'true');
        }
        if (sidebarToggle) {
            sidebarToggle.setAttribute('aria-expanded', 'false');
        }
        
        // Restore body scroll
        document.body.style.overflow = '';
        document.body.classList.remove('sidebar-open');
        
        // Return focus to toggle button for accessibility
        if (sidebarToggle) {
            sidebarToggle.focus();
        }
    }

    // Event listeners for sidebar toggle
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', openSidebar);
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    // Close sidebar on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });

    // Close sidebar when clicking on a link (mobile)
    if (sidebar) {
        const sidebarLinks = sidebar.querySelectorAll('a');
        sidebarLinks.forEach(function(link) {
            link.addEventListener('click', function() {
                // Only close on mobile
                if (window.innerWidth < 992) {
                    closeSidebar();
                }
            });
        });
    }

    // ============================================
    // Scroll to Top Button
    // ============================================
    
    /**
     * Show/hide scroll to top button based on scroll position
     */
    function handleScrollToTop() {
        if (scrollToTopBtn) {
            if (window.pageYOffset > 300) {
                scrollToTopBtn.classList.add('visible');
            } else {
                scrollToTopBtn.classList.remove('visible');
            }
        }
    }

    // Listen for scroll events
    window.addEventListener('scroll', handleScrollToTop);

    // Scroll to top when button is clicked
    if (scrollToTopBtn) {
        scrollToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // ============================================
    // Table of Contents Expand/Collapse
    // ============================================
    
    /**
     * Initialize TOC folder expand/collapse functionality
     */
    function initTOCFolders() {
        const tocFolders = document.querySelectorAll('.docs-toc-folder');
        console.log('Documentation JS: Found ' + tocFolders.length + ' TOC folders');
        
        if (tocFolders.length === 0) {
            console.warn('Documentation JS: No TOC folders found. TOC may not be loaded yet.');
            return;
        }
        
        tocFolders.forEach(function(folder) {
            const toggle = folder.querySelector('.docs-toc-folder-toggle');
            const content = folder.querySelector('.docs-toc-folder-content');
            
            if (!toggle) {
                console.warn('Documentation JS: Toggle button not found for folder:', folder);
                return;
            }
            
            if (!content) {
                console.warn('Documentation JS: Content element not found for folder:', folder);
                return;
            }
            
            // Check if listeners are already attached to prevent duplicates
            if (toggle.hasAttribute('data-toc-initialized')) {
                console.log('Documentation JS: Toggle already initialized, skipping:', folder);
                return;
            }
            
            // Mark as initialized
            toggle.setAttribute('data-toc-initialized', 'true');
            
            console.log('Documentation JS: Attaching click handler to folder:', folder);
            
            // Add click handler for toggle
            toggle.addEventListener('click', function(e) {
                console.log('Documentation JS: Folder clicked!');
                e.preventDefault();
                e.stopPropagation();
                
                const isExpanded = folder.classList.contains('expanded');
                
                if (isExpanded) {
                    // Collapse folder
                    folder.classList.remove('expanded');
                    toggle.setAttribute('aria-expanded', 'false');
                    
                    // Update folder icon
                    const folderIcon = toggle.querySelector('.fa-folder, .fa-folder-open');
                    if (folderIcon) {
                        folderIcon.classList.remove('fa-folder-open');
                        folderIcon.classList.add('fa-folder');
                    }
                } else {
                    // Expand folder
                    folder.classList.add('expanded');
                    toggle.setAttribute('aria-expanded', 'true');
                    
                    // Update folder icon
                    const folderIcon = toggle.querySelector('.fa-folder, .fa-folder-open');
                    if (folderIcon) {
                        folderIcon.classList.remove('fa-folder');
                        folderIcon.classList.add('fa-folder-open');
                    }
                }
            });
            
            // Also handle keyboard activation
            toggle.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    e.stopPropagation();
                    toggle.click();
                }
            });
        });
    }

    // ============================================
    // Smooth Scrolling for Anchor Links
    // ============================================
    
    /**
     * Add smooth scrolling to anchor links within the document
     */
    function initSmoothScrolling() {
        const anchorLinks = document.querySelectorAll('.docs-content a[href^="#"]');
        
        anchorLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                const targetId = this.getAttribute('href');
                
                if (targetId === '#') return;
                
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    e.preventDefault();
                    
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    
                    // Update URL without jumping
                    history.pushState(null, null, targetId);
                }
            });
        });
    }

    // ============================================
    // Active Item Highlighting
    // ============================================
    
    /**
     * Highlight the active document in the TOC and expand parent folders
     */
    function highlightActiveTOCItem() {
        const currentPath = window.location.pathname;
        const tocLinks = document.querySelectorAll('.docs-toc-link');
        
        tocLinks.forEach(function(link) {
            const linkHref = link.getAttribute('href');
            
            // Check if this link matches the current path
            if (linkHref === currentPath) {
                link.classList.add('active');
                
                // Expand all parent folders
                let parent = link.closest('.docs-toc-folder');
                while (parent) {
                    parent.classList.add('expanded');
                    const content = parent.querySelector('.docs-toc-folder-content');
                    if (content) {
                        // Set max-height to allow content to show
                        content.style.maxHeight = content.scrollHeight + 'px';
                    }
                    // Move up to the next parent folder
                    parent = parent.parentElement.closest('.docs-toc-folder');
                }
                
                // Scroll the active item into view in the sidebar
                setTimeout(function() {
                    if (sidebar) {
                        const linkRect = link.getBoundingClientRect();
                        const sidebarRect = sidebar.getBoundingClientRect();
                        
                        // Check if link is outside visible area
                        if (linkRect.top < sidebarRect.top || linkRect.bottom > sidebarRect.bottom) {
                            link.scrollIntoView({
                                behavior: 'smooth',
                                block: 'center'
                            });
                        }
                    }
                }, 300); // Wait for folder expansion animations
            }
        });
    }

    // ============================================
    // Responsive Handling
    // ============================================
    
    /**
     * Handle window resize events
     * Requirements: 8.1, 8.2, 8.3
     */
    function handleResize() {
        // Close sidebar on desktop
        if (window.innerWidth >= 992) {
            closeSidebar();
        }
        
        // Recalculate TOC folder heights on resize
        const expandedFolders = document.querySelectorAll('.docs-toc-folder.expanded');
        expandedFolders.forEach(function(folder) {
            const content = folder.querySelector('.docs-toc-folder-content');
            if (content) {
                content.style.maxHeight = content.scrollHeight + 'px';
            }
        });
    }
    
    // Debounce resize handler for better performance
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(handleResize, 150);
    });
    
    /**
     * Handle orientation change on mobile devices
     * Requirements: 8.1, 8.3
     */
    function handleOrientationChange() {
        // Close sidebar on orientation change to prevent layout issues
        if (window.innerWidth < 992) {
            closeSidebar();
        }
        
        // Recalculate layout after orientation change
        setTimeout(handleResize, 300);
    }
    
    window.addEventListener('orientationchange', handleOrientationChange);

    // ============================================
    // Touch Gesture Support for Mobile
    // ============================================
    
    /**
     * Add swipe gesture support for sidebar on mobile
     * Requirements: 8.2, 8.4
     */
    function initTouchGestures() {
        if (!sidebar) return;
        
        let touchStartX = 0;
        let touchStartY = 0;
        let touchEndX = 0;
        let touchEndY = 0;
        
        // Detect swipe from left edge to open sidebar
        document.addEventListener('touchstart', function(e) {
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
        }, { passive: true });
        
        document.addEventListener('touchend', function(e) {
            touchEndX = e.changedTouches[0].screenX;
            touchEndY = e.changedTouches[0].screenY;
            handleSwipeGesture();
        }, { passive: true });
        
        function handleSwipeGesture() {
            const swipeThreshold = 50;
            const swipeDistanceX = touchEndX - touchStartX;
            const swipeDistanceY = Math.abs(touchEndY - touchStartY);
            
            // Only on mobile
            if (window.innerWidth >= 992) return;
            
            // Swipe right from left edge to open sidebar
            if (touchStartX < 50 && swipeDistanceX > swipeThreshold && swipeDistanceY < 100) {
                if (!sidebar.classList.contains('active')) {
                    openSidebar();
                }
            }
            
            // Swipe left to close sidebar
            if (sidebar.classList.contains('active') && swipeDistanceX < -swipeThreshold && swipeDistanceY < 100) {
                closeSidebar();
            }
        }
    }
    
    /**
     * Improve touch scrolling performance
     * Requirements: 8.3, 8.4
     */
    function optimizeTouchScrolling() {
        // Add momentum scrolling to sidebar
        if (sidebar) {
            sidebar.style.webkitOverflowScrolling = 'touch';
        }
        
        // Prevent overscroll on iOS
        const scrollableElements = document.querySelectorAll('.docs-sidebar, .docs-main');
        scrollableElements.forEach(function(element) {
            let startY = 0;
            
            element.addEventListener('touchstart', function(e) {
                startY = e.touches[0].pageY;
            }, { passive: true });
            
            element.addEventListener('touchmove', function(e) {
                const currentY = e.touches[0].pageY;
                const scrollTop = element.scrollTop;
                const scrollHeight = element.scrollHeight;
                const clientHeight = element.clientHeight;
                
                // Prevent overscroll at top
                if (scrollTop === 0 && currentY > startY) {
                    e.preventDefault();
                }
                
                // Prevent overscroll at bottom
                if (scrollTop + clientHeight >= scrollHeight && currentY < startY) {
                    e.preventDefault();
                }
            }, { passive: false });
        });
    }

    // ============================================
    // Code Block Copy Functionality (Optional Enhancement)
    // ============================================
    
    /**
     * Add copy buttons to code blocks
     */
    function initCodeBlockCopy() {
        const codeBlocks = document.querySelectorAll('.docs-content pre code');
        
        codeBlocks.forEach(function(codeBlock) {
            const pre = codeBlock.parentElement;
            
            // Create copy button
            const copyBtn = document.createElement('button');
            copyBtn.className = 'docs-code-copy';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
            copyBtn.setAttribute('aria-label', 'Copy code');
            copyBtn.setAttribute('title', 'Copy to clipboard');
            
            // Add button to pre element
            pre.style.position = 'relative';
            pre.appendChild(copyBtn);
            
            // Copy functionality
            copyBtn.addEventListener('click', function() {
                const code = codeBlock.textContent;
                
                navigator.clipboard.writeText(code).then(function() {
                    copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                    copyBtn.classList.add('copied');
                    
                    setTimeout(function() {
                        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                        copyBtn.classList.remove('copied');
                    }, 2000);
                }).catch(function(err) {
                    console.error('Failed to copy code:', err);
                });
            });
        });
    }

    // ============================================
    // Search Form Enhancement
    // ============================================
    
    /**
     * Add keyboard shortcut for search (Ctrl/Cmd + K)
     */
    function initSearchShortcut() {
        const searchInput = document.querySelector('.docs-search-form input[type="text"]');
        
        if (searchInput) {
            document.addEventListener('keydown', function(e) {
                // Ctrl+K or Cmd+K
                if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                    e.preventDefault();
                    searchInput.focus();
                    
                    // Open sidebar on mobile if closed
                    if (window.innerWidth < 992 && sidebar && !sidebar.classList.contains('active')) {
                        openSidebar();
                    }
                }
            });
        }
    }
    
    // ============================================
    // Keyboard Navigation for TOC
    // ============================================
    
    /**
     * Add keyboard navigation support for TOC
     */
    function initTOCKeyboardNavigation() {
        const tocLinks = document.querySelectorAll('.docs-toc-link, .docs-toc-folder-toggle');
        
        tocLinks.forEach(function(link, index) {
            link.addEventListener('keydown', function(e) {
                let targetIndex = -1;
                
                switch(e.key) {
                    case 'ArrowDown':
                        // Move to next item
                        e.preventDefault();
                        targetIndex = index + 1;
                        break;
                    case 'ArrowUp':
                        // Move to previous item
                        e.preventDefault();
                        targetIndex = index - 1;
                        break;
                    case 'Home':
                        // Move to first item
                        e.preventDefault();
                        targetIndex = 0;
                        break;
                    case 'End':
                        // Move to last item
                        e.preventDefault();
                        targetIndex = tocLinks.length - 1;
                        break;
                    case 'Enter':
                    case ' ':
                        // Activate link or toggle folder
                        if (link.classList.contains('docs-toc-folder-toggle')) {
                            e.preventDefault();
                            link.click();
                        }
                        break;
                }
                
                // Focus target element
                if (targetIndex >= 0 && targetIndex < tocLinks.length) {
                    tocLinks[targetIndex].focus();
                }
            });
        });
    }

    // ============================================
    // Browser Navigation Support
    // ============================================
    
    /**
     * Handle browser back/forward navigation
     * Ensures proper state restoration when using browser navigation
     * Requirements: 4.5
     */
    function initBrowserNavigation() {
        // Store current scroll position before navigation
        window.addEventListener('beforeunload', function() {
            sessionStorage.setItem('docs_scroll_position', window.pageYOffset.toString());
        });
        
        // Restore scroll position on page load (for back/forward navigation)
        const savedScrollPosition = sessionStorage.getItem('docs_scroll_position');
        if (savedScrollPosition) {
            window.scrollTo(0, parseInt(savedScrollPosition, 10));
            sessionStorage.removeItem('docs_scroll_position');
        }
        
        // Handle popstate event (back/forward buttons)
        window.addEventListener('popstate', function(event) {
            // The page will reload automatically, but we can add custom handling here
            // For now, just ensure the TOC is properly highlighted
            setTimeout(function() {
                highlightActiveTOCItem();
            }, 100);
        });
    }
    
    /**
     * Store last viewed page in sessionStorage
     * This provides client-side tracking in addition to server-side session
     * Requirements: 4.6
     */
    function storeLastViewedPage() {
        const currentPath = window.location.pathname + window.location.search;
        sessionStorage.setItem('docs_last_viewed_page', currentPath);
        sessionStorage.setItem('docs_last_viewed_time', new Date().toISOString());
    }
    
    /**
     * Get last viewed page from sessionStorage
     * Requirements: 4.6
     */
    function getLastViewedPage() {
        return {
            path: sessionStorage.getItem('docs_last_viewed_page'),
            time: sessionStorage.getItem('docs_last_viewed_time')
        };
    }

    // ============================================
    // Initialization
    // ============================================
    
    /**
     * Initialize all documentation features
     */
    function init() {
        console.log('Documentation JS: Initializing...');
        
        // Initialize TOC folders
        console.log('Documentation JS: Initializing TOC folders...');
        initTOCFolders();
        
        // Initialize smooth scrolling
        initSmoothScrolling();
        
        // Highlight active TOC item
        highlightActiveTOCItem();
        
        // Initialize code block copy buttons
        initCodeBlockCopy();
        
        // Initialize search shortcut
        initSearchShortcut();
        
        // Initialize keyboard navigation for TOC
        initTOCKeyboardNavigation();
        
        // Initialize browser navigation support
        initBrowserNavigation();
        
        // Store current page as last viewed
        storeLastViewedPage();
        
        // Initial scroll to top button state
        handleScrollToTop();
        
        // Initialize touch gestures for mobile (Requirements: 8.2, 8.4)
        initTouchGestures();
        
        // Optimize touch scrolling (Requirements: 8.3, 8.4)
        optimizeTouchScrolling();
        
        // Add viewport meta tag check for mobile
        ensureViewportMeta();
    }
    
    /**
     * Ensure proper viewport meta tag for mobile responsiveness
     * Requirements: 8.5
     */
    function ensureViewportMeta() {
        const viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            const meta = document.createElement('meta');
            meta.name = 'viewport';
            meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
            document.head.appendChild(meta);
        }
    }

    // Run initialization when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
