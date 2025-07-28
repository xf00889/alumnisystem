/**
 * NORSU Alumni System - Sidebar Module
 * Handles superuser sidebar navigation and interactions
 */

// Immediately invoked function expression to avoid global scope pollution
(function() {
    'use strict';
    
    // Global app object
    window.app = window.app || {};
    
    // Sidebar module
    const sidebar = {
        sidebar: null,
        toggleBtn: null,
        overlay: null,
        isOpen: false,
        isMobile: false,
        categoryToggles: null,
        navGroups: null,

        /**
         * Initialize sidebar functionality
         */
        init: function() {
            console.log('Initializing sidebar...');
            this.sidebar = document.getElementById('sidebar');
            this.toggleBtn = document.querySelector('.sidebar-toggle');
            
            if (!this.sidebar) {
                console.warn('Sidebar element not found');
                return;
            }
            
            console.log('Found sidebar element:', this.sidebar);
            this.createOverlay();
            this.initializeCollapsibleCategories();
            this.bindEvents();
            this.checkMobileView();
            this.initializeActiveStates();
            this.setupKeyboardNavigation();
            
            console.log('Sidebar initialized successfully');
        },

        /**
         * Create mobile overlay
         */
        createOverlay: function() {
            this.overlay = document.createElement('div');
            this.overlay.className = 'sidebar-overlay';
            this.overlay.setAttribute('aria-hidden', 'true');
            document.body.appendChild(this.overlay);
        },
        
        /**
         * Initialize collapsible categories
         */
        initializeCollapsibleCategories: function() {
            console.log('Setting up collapsible categories');
            this.categoryToggles = this.sidebar.querySelectorAll('.sidebar-category');
            this.navGroups = this.sidebar.querySelectorAll('.nav-group');
            
            console.log('Found', this.categoryToggles.length, 'category toggles');
            console.log('Found', this.navGroups.length, 'navigation groups');
            
            // Keep nav groups expanded by default (they have 'show' class in HTML)
            // Only collapse if user has specifically saved collapsed state
            
            this.categoryToggles.forEach(toggle => {
                console.log('Setting up toggle for:', toggle.textContent.trim());
                
                // Set initial state
                toggle.classList.remove('active');
                toggle.setAttribute('role', 'button');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.setAttribute('tabindex', '0');
                
                // Add click event directly
                toggle.onclick = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const targetId = toggle.getAttribute('data-target');
                    console.log('Toggle clicked:', targetId);
                    this.toggleCategory(targetId);
                };
                
                // Add keyboard support
                toggle.onkeydown = (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        const targetId = toggle.getAttribute('data-target');
                        this.toggleCategory(targetId);
                    }
                };
            });
            
            // Load saved states only after setting up toggles
            this.loadSavedCategoryStates();
        },

        /**
         * Bind event listeners
         */
        bindEvents: function() {
            // Toggle button click
            if (this.toggleBtn) {
                this.toggleBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggle();
                });
            }

            // Overlay click to close
            this.overlay.addEventListener('click', () => {
                this.close();
            });

            // Escape key to close
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen) {
                    this.close();
                }
            });

            // Window resize handler
            window.addEventListener('resize', this.debounce(() => {
                this.checkMobileView();
            }, 250));

            // Navigation link clicks
            const navLinks = this.sidebar.querySelectorAll('.sidebar-nav a');
            navLinks.forEach(link => {
                link.addEventListener('click', () => {
                    if (this.isMobile) {
                        this.close();
                    }
                });
            });

            // Focus management
            this.sidebar.addEventListener('focusin', () => {
                if (!this.isOpen && this.isMobile) {
                    this.open();
                }
            });
        },

        /**
         * Check if we're in mobile view
         */
        checkMobileView: function() {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth < 992; // Bootstrap lg breakpoint

            if (wasMobile !== this.isMobile) {
                if (this.isMobile) {
                    this.close();
                    this.sidebar.setAttribute('aria-hidden', 'true');
                } else {
                    this.sidebar.removeAttribute('aria-hidden');
                    this.overlay.classList.remove('show');
                }
            }
        },

        /**
         * Initialize active states for navigation items
         */
        initializeActiveStates: function() {
            const currentPath = window.location.pathname;
            const navLinks = this.sidebar.querySelectorAll('.sidebar-nav a');

            navLinks.forEach(link => {
                const linkPath = link.pathname;
                
                // Remove existing active states
                link.classList.remove('active');
                
                // Add active state for exact matches or parent paths
                if (linkPath === currentPath || 
                    (currentPath.startsWith(linkPath) && linkPath !== '/')) {
                    link.classList.add('active');
                    link.setAttribute('aria-current', 'page');
                    
                    // Auto-expand parent categories of active links
                    const parentGroup = link.closest('.nav-group');
                    if (parentGroup) {
                        this.expandCategory(parentGroup.id);
                    }
                } else {
                    link.removeAttribute('aria-current');
                }
            });
        },
        
        /**
         * Toggle a category open/closed
         */
        toggleCategory: function(targetId) {
            console.log('Toggling category:', targetId);
            const group = document.getElementById(targetId);
            const toggle = document.querySelector(`.sidebar-category[data-target="${targetId}"]`);
            
            if (!group || !toggle) {
                console.warn('Could not find elements for sidebar category:', targetId);
                return;
            }
            
            const isExpanded = group.classList.contains('show');
            console.log('Current state:', isExpanded ? 'expanded' : 'collapsed');
            
            // Toggle state
            if (isExpanded) {
                this.collapseCategory(targetId);
            } else {
                this.expandCategory(targetId);
            }
        },
        
        /**
         * Expand a category
         */
        expandCategory: function(targetId) {
            console.log('Expanding category:', targetId);
            const group = document.getElementById(targetId);
            const toggle = document.querySelector(`.sidebar-category[data-target="${targetId}"]`);
            
            if (!group || !toggle) {
                console.warn('Could not find elements for sidebar category:', targetId);
                return;
            }
            
            group.classList.add('show');
            toggle.classList.add('active');
            toggle.setAttribute('aria-expanded', 'true');
            
            // Save state
            this.saveCategoryState(targetId, true);
        },
        
        /**
         * Collapse a category
         */
        collapseCategory: function(targetId) {
            console.log('Collapsing category:', targetId);
            const group = document.getElementById(targetId);
            const toggle = document.querySelector(`.sidebar-category[data-target="${targetId}"]`);
            
            if (!group || !toggle) {
                console.warn('Could not find elements for sidebar category:', targetId);
                return;
            }
            
            group.classList.remove('show');
            toggle.classList.remove('active');
            toggle.setAttribute('aria-expanded', 'false');
            
            // Save state
            this.saveCategoryState(targetId, false);
        },
        
        /**
         * Save category states to localStorage
         */
        saveCategoryState: function(categoryId, isExpanded) {
            try {
                const savedStates = JSON.parse(localStorage.getItem('sidebarCategoryStates') || '{}');
                savedStates[categoryId] = isExpanded;
                localStorage.setItem('sidebarCategoryStates', JSON.stringify(savedStates));
            } catch (err) {
                console.error('Error saving sidebar category state:', err);
            }
        },
        
        /**
         * Load saved category states from localStorage
         */
        loadSavedCategoryStates: function() {
            console.log('Loading saved category states');
            try {
                const savedStates = JSON.parse(localStorage.getItem('sidebarCategoryStates') || '{}');
                console.log('Saved states:', savedStates);
                
                // Set initial aria-expanded attributes based on current state
                this.categoryToggles.forEach(toggle => {
                    const targetId = toggle.getAttribute('data-target');
                    const group = document.getElementById(targetId);
                    if (group && group.classList.contains('show')) {
                        toggle.setAttribute('aria-expanded', 'true');
                        toggle.classList.add('active');
                    } else {
                        toggle.setAttribute('aria-expanded', 'false');
                        toggle.classList.remove('active');
                    }
                });
                
                // Apply saved states (only collapse if explicitly saved as collapsed)
                Object.entries(savedStates).forEach(([categoryId, isExpanded]) => {
                    console.log(`Setting ${categoryId} to ${isExpanded ? 'expanded' : 'collapsed'}`);
                    if (!isExpanded) {
                        // Only collapse if user explicitly collapsed it
                        this.collapseCategory(categoryId);
                    }
                });
                
                // Handle active navigation links - ensure parent is expanded
                const activeLink = this.sidebar.querySelector('.sidebar-nav a.active');
                if (activeLink) {
                    const parentGroup = activeLink.closest('.nav-group');
                    if (parentGroup) {
                        console.log('Found active link in category:', parentGroup.id);
                        this.expandCategory(parentGroup.id);
                    }
                }
                
            } catch (err) {
                console.error('Error loading sidebar category states:', err);
                // Reset states if corrupted
                localStorage.removeItem('sidebarCategoryStates');
                // Set default aria-expanded for all toggles
                this.categoryToggles.forEach(toggle => {
                    toggle.setAttribute('aria-expanded', 'true');
                    toggle.classList.add('active');
                });
            }
        },
        
        /**
         * Ensure at least one category is visible
         */
        ensureVisibleCategory: function() {
            console.log('Ensuring at least one category is visible');
            // Check if any category is expanded
            const anyExpanded = Array.from(this.navGroups).some(group => 
                group.classList.contains('show')
            );
            
            // If none are expanded, expand the first one
            if (!anyExpanded && this.navGroups.length > 0) {
                const firstGroup = this.navGroups[0];
                console.log('No categories expanded, expanding:', firstGroup.id);
                this.expandCategory(firstGroup.id);
            }
        },

        /**
         * Setup keyboard navigation
         */
        setupKeyboardNavigation: function() {
            const navLinks = this.sidebar.querySelectorAll('.sidebar-nav a');
            
            navLinks.forEach((link, index) => {
                link.addEventListener('keydown', (e) => {
                    let targetIndex = -1;
                    
                    switch (e.key) {
                        case 'ArrowDown':
                            e.preventDefault();
                            targetIndex = (index + 1) % navLinks.length;
                            break;
                        case 'ArrowUp':
                            e.preventDefault();
                            targetIndex = (index - 1 + navLinks.length) % navLinks.length;
                            break;
                        case 'Home':
                            e.preventDefault();
                            targetIndex = 0;
                            break;
                        case 'End':
                            e.preventDefault();
                            targetIndex = navLinks.length - 1;
                            break;
                    }
                    
                    if (targetIndex >= 0) {
                        navLinks[targetIndex].focus();
                    }
                });
            });
        },

        /**
         * Toggle sidebar open/closed
         */
        toggle: function() {
            if (this.isOpen) {
                this.close();
            } else {
                this.open();
            }
        },

        /**
         * Open sidebar
         */
        open: function() {
            if (this.isOpen) return;

            this.isOpen = true;
            this.sidebar.classList.add('show');
            
            if (this.isMobile) {
                this.overlay.classList.add('show');
                this.sidebar.setAttribute('aria-hidden', 'false');
                
                // Prevent body scroll
                document.body.style.overflow = 'hidden';
                
                // Focus first navigation item
                const firstNavLink = this.sidebar.querySelector('.sidebar-nav a');
                if (firstNavLink) {
                    setTimeout(() => firstNavLink.focus(), 100);
                }
            }

            // Update toggle button state
            if (this.toggleBtn) {
                this.toggleBtn.setAttribute('aria-expanded', 'true');
                this.toggleBtn.classList.add('active');
            }

            // Dispatch custom event
            this.sidebar.dispatchEvent(new CustomEvent('sidebar:opened', {
                bubbles: true,
                detail: { isMobile: this.isMobile }
            }));
        },

        /**
         * Close sidebar
         */
        close: function() {
            if (!this.isOpen) return;

            this.isOpen = false;
            this.sidebar.classList.remove('show');
            
            if (this.isMobile) {
                this.overlay.classList.remove('show');
                this.sidebar.setAttribute('aria-hidden', 'true');
                
                // Restore body scroll
                document.body.style.overflow = '';
            }

            // Update toggle button state
            if (this.toggleBtn) {
                this.toggleBtn.setAttribute('aria-expanded', 'false');
                this.toggleBtn.classList.remove('active');
                
                // Return focus to toggle button if it was opened via keyboard
                if (document.activeElement && 
                    this.sidebar.contains(document.activeElement)) {
                    this.toggleBtn.focus();
                }
            }

            // Dispatch custom event
            this.sidebar.dispatchEvent(new CustomEvent('sidebar:closed', {
                bubbles: true,
                detail: { isMobile: this.isMobile }
            }));
        },
        
        /**
         * Debounce function for handling resize events efficiently
         */
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    };
    
    // Make toggleSidebar global function available for legacy code
    window.toggleSidebar = function() {
        sidebar.toggle();
    };

    // Attach to app object immediately
    window.app = window.app || {};
    window.app.sidebar = sidebar;

    // Initialize on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function() {
        sidebar.init();
    });
})();