/**
 * Cascading Dropdowns for Education Forms
 * Handles Campus → College → Program → Major selection
 */

// Campus-specific program mapping
const programsByCampus = {
    'NORSU-MAIN': 'ALL',
    'NORSU-BSC': {  // Bayawan-Sta. Catalina Campus
        'CAFF': [
            ['BSA-AGRI', 'Bachelor of Science in Agriculture'],
            ['BSF', 'Bachelor of Science in Forestry']
        ],
        'CAS': [
            ['BSIT', 'Bachelor of Science in Information Technology'],
            ['BSCS', 'Bachelor of Science in Computer Science']
        ],
        'CBA': [
            ['BSBA', 'Bachelor of Science in Business Administration'],
            ['BSHM', 'Bachelor of Science in Hospitality Management'],
            ['BSOA', 'Bachelor of Science in Office Administration']
        ],
        'CCJE': [
            ['BSCRIM', 'Bachelor of Science in Criminology']
        ],
        'CIT': [
            ['BIT', 'Bachelor of Science in Industrial Technology']
        ],
        'CTE': [
            ['BEED', 'Bachelor of Elementary Education'],
            ['BSED', 'Bachelor of Secondary Education']
        ]
    },
    'NORSU-BAIS': 'ALL',
    'NORSU-GUI': 'ALL',
    'NORSU-MAB': 'ALL',
    'NORSU-SIA': 'ALL',
    'NORSU-PAM': 'ALL',
    'OTHER': 'ALL'
};

// All courses by college
const coursesByCollege = {
    'CAS': [
        ['BSBIO', 'BS in Biology'],
        ['BSCHEM', 'BS in Chemistry'],
        ['BSCS', 'BS in Computer Science'],
        ['BSGEO', 'BS in Geology'],
        ['BSIT', 'BS in Information Technology'],
        ['BMC', 'Bachelor of Mass Communication'],
        ['BSM', 'BS in Mathematics'],
        ['BSP', 'BS in Psychology']
    ],
    'CBA': [
        ['BSA', 'BS in Accountancy'],
        ['BSBA', 'BS in Business Administration'],
        ['BSBA-HRDM', 'BSBA Major in Human Resource Development Management'],
        ['BSBA-FM', 'BSBA Major in Financial Management'],
        ['BSOSM', 'BS in Office Systems Management'],
        ['BSOA', 'BS in Office Administration'],
        ['BSHM', 'BS in Hospitality Management']
    ],
    'CEA': [
        ['BSARCH', 'BS in Architecture'],
        ['BSCE', 'BS in Civil Engineering'],
        ['BSCPE', 'BS in Computer Engineering'],
        ['BSEE', 'BS in Electrical Engineering'],
        ['BSECE', 'BS in Electronics and Communication Engineering'],
        ['BSGE', 'BS in Geodetic Engineering'],
        ['BSGTHE', 'BS in Geothermal Engineering'],
        ['BSME', 'BS in Mechanical Engineering']
    ],
    'CNPAHS': [
        ['BSN', 'BS in Nursing'],
        ['BSP', 'BS in Pharmacy'],
        ['MIDWIFERY', 'Midwifery'],
        ['AMDNA', 'AMDNA']
    ],
    'CTHM': [
        ['BSHM', 'BS in Hospitality Management'],
        ['BSTM', 'BS in Tourism']
    ],
    'CAFF': [
        ['BSF', 'BS in Forestry'],
        ['BSA-AGRI', 'BS in Agriculture'],
        ['BSA-AGRON', 'BS in Agriculture Major in Agronomy'],
        ['BSA-HORT', 'BS in Agriculture Major in Horticulture'],
        ['BSA-ANSCI', 'BS in Agriculture Major in Animal Science'],
        ['BSA-AGEXT', 'BS in Agriculture Major in Agricultural Extension']
    ],
    'CCJE': [
        ['BSCRIM', 'BS in Criminology']
    ],
    'CIT': [
        ['BIT', 'BS in Industrial Technology'],
        ['BSAT', 'BS in Automotive Technology'],
        ['BSAM', 'BS in Aviation Maintenance'],
        ['BSCT', 'BS in Civil Technology'],
        ['BSCET', 'BS in Computer and Electronics Technology'],
        ['BSET', 'BS in Electrical Technology'],
        ['BSFT', 'BS in Food Technology'],
        ['BSIT-INDTECH', 'BS in Industrial Technology'],
        ['BSMT', 'BS in Mechanical Technology'],
        ['BSRACT', 'BS in Refrigeration and Air-Conditioning Technology']
    ],
    'CTE': [
        ['BSED', 'BS in Secondary Education'],
        ['BEED', 'BS in Elementary Education']
    ],
    'COL': [
        ['LLB', 'Bachelor of Law']
    ]
};

// Majors by program
const majorsByProgram = {
    'BSED': [
        ['ENGLISH', 'Major in English'],
        ['FILIPINO', 'Major in Filipino'],
        ['MATHEMATICS', 'Major in Mathematics'],
        ['SCIENCE', 'Major in Science'],
        ['SOCIAL_STUDIES', 'Major in Social Studies'],
        ['VALUES_EDUCATION', 'Major in Religious and Values Education']
    ],
    'BEED': [
        ['GENERAL_EDUCATION', 'Major in General Education'],
        ['EARLY_CHILDHOOD', 'Major in Early Childhood Education'],
        ['SPECIAL_EDUCATION', 'Major in Special Education'],
        ['ENGLISH', 'Major in English'],
        ['FILIPINO', 'Major in Filipino'],
        ['MATHEMATICS', 'Major in Mathematics'],
        ['SCIENCE', 'Major in Science'],
        ['SOCIAL_STUDIES', 'Major in Social Studies'],
        ['MAPE', 'Major in Music, Arts and Physical Education'],
        ['THE', 'Major in Technology and Home Economics']
    ],
    'BIT': [
        ['AUTOMOTIVE', 'Major in Automotive Technology'],
        ['COMPUTER', 'Major in Computer Technology'],
        ['ELECTRICAL', 'Major in Electrical Technology'],
        ['ELECTRONICS', 'Major in Electronics Technology'],
        ['DRAFTING', 'Major in Drafting Technology'],
        ['FOOD_PROCESSING', 'Major in Food Processing Technology'],
        ['WELDING', 'Major in Welding and Fabrication Technology']
    ],
    'BSBA': [
        ['FINANCIAL_MANAGEMENT', 'Major in Financial Management'],
        ['MARKETING_MANAGEMENT', 'Major in Marketing Management'],
        ['HUMAN_RESOURCE_MANAGEMENT', 'Major in Human Resource Management'],
        ['OPERATIONS_MANAGEMENT', 'Major in Operations Management']
    ]
};

// Campus-specific major restrictions
const majorsByCampusProgram = {
    'NORSU-BSC': {
        'BSED': [
            ['SCIENCE', 'Major in Science'],
            ['MATHEMATICS', 'Major in Mathematics'],
            ['ENGLISH', 'Major in English']
        ],
        'BEED': [
            ['GENERAL_CURRICULUM', 'Major in General Curriculum']
        ],
        'BIT': [
            ['AUTOMOTIVE', 'Major in Automotive Technology'],
            ['COMPUTER', 'Major in Computer Technology'],
            ['ELECTRICAL', 'Major in Electrical Technology'],
            ['ELECTRONICS', 'Major in Electronics Technology']
        ],
        'BSCS': [],
        'BSIT': [],
        'BSCRIM': [],
        'BSOA': [],
        'BSHM': [],
        'BSBA': []
    }
};

// College names
const collegeNames = {
    'CAS': 'College of Arts and Sciences',
    'CBA': 'College of Business Administration',
    'CTE': 'College of Teacher Education',
    'CNPAHS': 'College of Nursing, Pharmacy and Allied Health Sciences',
    'CCJE': 'College of Criminal Justice Education',
    'CTHM': 'College of Tourism and Hospitality Management',
    'CEA': 'College of Engineering and Architecture',
    'CAFF': 'College of Agriculture, Forestry and Fishery',
    'CIT': 'College of Industrial Technology',
    'COL': 'College of Law'
};

/**
 * Initialize cascading dropdowns for education form
 * @param {string} formId - The ID of the form element
 */
function initEducationCascadingDropdowns(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    const campusSelect = form.querySelector('[name="campus"]');
    const collegeSelect = form.querySelector('[name="college"]');
    const programSelect = form.querySelector('[name="program"]');
    const majorInput = form.querySelector('[name="major"]');

    if (!campusSelect || !collegeSelect || !programSelect) return;

    // Get initial values from data attributes or current values
    const initialProgram = programSelect.getAttribute('data-initial-value') || programSelect.value;
    
    // Derive college from program using the mapping
    let initialCollege = collegeSelect.getAttribute('data-initial-value') || collegeSelect.value;
    
    // If no college but we have a program, derive it from the program
    if (!initialCollege && initialProgram) {
        initialCollege = getProgramCollege(initialProgram);
    }

    // Handle campus change
    campusSelect.addEventListener('change', function() {
        const selectedCampus = this.value;
        
        // Clear and reset dependent fields
        collegeSelect.innerHTML = '';
        programSelect.innerHTML = '';
        if (majorInput && !programSelect.value) majorInput.value = '';

        if (selectedCampus === '') {
            collegeSelect.disabled = true;
            programSelect.disabled = true;
            
            collegeSelect.innerHTML = '<option value="">-- Select your campus first --</option>';
            programSelect.innerHTML = '<option value="">-- Select your campus and college first --</option>';
        } else {
            collegeSelect.disabled = false;
            programSelect.disabled = true;
            
            // Add default option
            collegeSelect.innerHTML = '<option value="">-- Select your college --</option>';
            
            // Get available colleges
            const campusPrograms = programsByCampus[selectedCampus];
            let availableColleges = [];

            if (campusPrograms === 'ALL') {
                availableColleges = Object.keys(coursesByCollege);
            } else {
                availableColleges = Object.keys(campusPrograms);
            }

            // Add college options
            availableColleges.forEach(collegeCode => {
                const option = document.createElement('option');
                option.value = collegeCode;
                option.textContent = collegeNames[collegeCode] || collegeCode;
                collegeSelect.appendChild(option);
            });
            
            // Restore initial college value if it exists and is valid
            if (initialCollege && availableColleges.includes(initialCollege)) {
                collegeSelect.value = initialCollege;
                // Trigger college change to populate programs
                setTimeout(() => {
                    collegeSelect.dispatchEvent(new Event('change'));
                }, 50);
            }
        }
    });

    // Handle college change
    collegeSelect.addEventListener('change', function() {
        const selectedCampus = campusSelect.value;
        const selectedCollege = this.value;
        
        // Clear program
        programSelect.innerHTML = '';
        if (majorInput && !programSelect.value) majorInput.value = '';

        if (selectedCollege === '') {
            programSelect.disabled = true;
            programSelect.innerHTML = '<option value="">-- Select your college first --</option>';
        } else {
            programSelect.disabled = false;
            programSelect.innerHTML = '<option value="">-- Select your program --</option>';
            
            // Get programs for this campus-college combination
            let programs = [];
            const campusPrograms = programsByCampus[selectedCampus];

            if (campusPrograms === 'ALL') {
                programs = coursesByCollege[selectedCollege] || [];
            } else {
                programs = campusPrograms[selectedCollege] || [];
            }

            // Add program options
            programs.forEach(([programCode, programName]) => {
                const option = document.createElement('option');
                option.value = programCode;
                option.textContent = programName;
                programSelect.appendChild(option);
            });
            
            // Restore initial program value if it exists and is valid
            if (initialProgram) {
                const programCodes = programs.map(p => p[0]);
                if (programCodes.includes(initialProgram)) {
                    programSelect.value = initialProgram;
                    // Trigger program change to update major placeholder
                    setTimeout(() => {
                        programSelect.dispatchEvent(new Event('change'));
                    }, 50);
                }
            }
        }
    });

    // Handle program change (for major suggestions)
    if (majorInput) {
        programSelect.addEventListener('change', function() {
            const selectedProgram = this.value;
            const selectedCampus = campusSelect.value;
            
            // Check if program has majors
            let majors = [];
            
            if (selectedCampus && majorsByCampusProgram[selectedCampus]) {
                if (selectedProgram in majorsByCampusProgram[selectedCampus]) {
                    majors = majorsByCampusProgram[selectedCampus][selectedProgram] || [];
                } else {
                    majors = majorsByProgram[selectedProgram] || [];
                }
            } else {
                majors = majorsByProgram[selectedProgram] || [];
            }
            
            // Update major field placeholder
            if (majors.length > 0) {
                majorInput.placeholder = 'e.g., ' + majors.map(m => m[1]).slice(0, 2).join(', ');
            } else {
                majorInput.placeholder = 'Enter your major/specialization (if any)';
            }
        });
    }

    // Initialize form state if campus has a value
    if (campusSelect.value) {
        // Trigger campus change to populate colleges
        campusSelect.dispatchEvent(new Event('change'));
    } else {
        // No campus selected - enable college anyway if it has a value
        // This handles legacy data where college might exist without proper campus
        if (initialCollege) {
            collegeSelect.disabled = false;
            collegeSelect.innerHTML = '<option value="">-- Select your college --</option>';
            
            // Add all colleges as fallback
            Object.keys(collegeNames).forEach(collegeCode => {
                const option = document.createElement('option');
                option.value = collegeCode;
                option.textContent = collegeNames[collegeCode];
                collegeSelect.appendChild(option);
            });
            
            collegeSelect.value = initialCollege;
            
            // Enable and populate program dropdown
            if (initialProgram) {
                programSelect.disabled = false;
                programSelect.innerHTML = '<option value="">-- Select your program --</option>';
                
                const programs = coursesByCollege[initialCollege] || [];
                programs.forEach(([programCode, programName]) => {
                    const option = document.createElement('option');
                    option.value = programCode;
                    option.textContent = programName;
                    programSelect.appendChild(option);
                });
                
                programSelect.value = initialProgram;
            }
        }
    }
}

/**
 * Helper function to get college from program code
 * @param {string} programCode - The program code
 * @returns {string} - The college code
 */
function getProgramCollege(programCode) {
    for (const [collegeCode, programs] of Object.entries(coursesByCollege)) {
        const programCodes = programs.map(p => p[0]);
        if (programCodes.includes(programCode)) {
            return collegeCode;
        }
    }
    return '';
}
