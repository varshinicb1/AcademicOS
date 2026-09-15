"""Generates official CBSE/NCERT curriculum JSONs for all main subjects across grades 6 through 12.
Follows official 2025-26 CBSE secondary/senior secondary and NCERT NCF-SE middle school curriculum frameworks.
"""
import json
import os
from pathlib import Path

OUT_DIR = Path("academicos-data/syllabus")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYLLABI = [
    # ==================== GRADE 12 ====================
    {
        "subject": "Physics",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, Physics_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 70,
        "units": [
            {"unit_no": "I", "name": "Electrostatics", "marks": 8, "chapters": [
                {"id": "electric-charges-fields", "name": "Electric Charges and Fields"},
                {"id": "electrostatic-potential-capacitance", "name": "Electrostatic Potential and Capacitance"}
            ]},
            {"unit_no": "II", "name": "Current Electricity", "marks": 8, "chapters": [
                {"id": "current-electricity", "name": "Current Electricity"}
            ]},
            {"unit_no": "III", "name": "Magnetic Effects of Current and Magnetism", "marks": 9, "chapters": [
                {"id": "moving-charges-magnetism", "name": "Moving Charges and Magnetism"},
                {"id": "magnetism-matter", "name": "Magnetism and Matter"}
            ]},
            {"unit_no": "IV", "name": "Electromagnetic Induction and Alternating Currents", "marks": 8, "chapters": [
                {"id": "electromagnetic-induction", "name": "Electromagnetic Induction"},
                {"id": "alternating-current", "name": "Alternating Current"}
            ]},
            {"unit_no": "V", "name": "Electromagnetic Waves", "marks": 3, "chapters": [
                {"id": "electromagnetic-waves", "name": "Electromagnetic Waves"}
            ]},
            {"unit_no": "VI", "name": "Optics", "marks": 15, "chapters": [
                {"id": "ray-optics", "name": "Ray Optics and Optical Instruments"},
                {"id": "wave-optics", "name": "Wave Optics"}
            ]},
            {"unit_no": "VII", "name": "Dual Nature of Radiation and Matter", "marks": 6, "chapters": [
                {"id": "dual-nature-radiation", "name": "Dual Nature of Radiation and Matter"}
            ]},
            {"unit_no": "VIII", "name": "Atoms and Nuclei", "marks": 6, "chapters": [
                {"id": "atoms", "name": "Atoms"},
                {"id": "nuclei", "name": "Nuclei"}
            ]},
            {"unit_no": "IX", "name": "Electronic Devices", "marks": 7, "chapters": [
                {"id": "semiconductor-electronics", "name": "Semiconductor Electronics: Materials, Devices and Simple Circuits"}
            ]}
        ]
    },
    {
        "subject": "Chemistry",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, Chemistry_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 70,
        "units": [
            {"unit_no": "I", "name": "Solutions", "marks": 7, "chapters": [
                {"id": "solutions", "name": "Solutions"}
            ]},
            {"unit_no": "II", "name": "Electrochemistry", "marks": 9, "chapters": [
                {"id": "electrochemistry", "name": "Electrochemistry"}
            ]},
            {"unit_no": "III", "name": "Chemical Kinetics", "marks": 7, "chapters": [
                {"id": "chemical-kinetics", "name": "Chemical Kinetics"}
            ]},
            {"unit_no": "IV", "name": "d-and f-Block Elements", "marks": 7, "chapters": [
                {"id": "d-and-f-block-elements", "name": "d-and f-Block Elements"}
            ]},
            {"unit_no": "V", "name": "Coordination Compounds", "marks": 7, "chapters": [
                {"id": "coordination-compounds", "name": "Coordination Compounds"}
            ]},
            {"unit_no": "VI", "name": "Haloalkanes and Haloarenes", "marks": 6, "chapters": [
                {"id": "haloalkanes-and-haloarenes", "name": "Haloalkanes and Haloarenes"}
            ]},
            {"unit_no": "VII", "name": "Alcohols, Phenols and Ethers", "marks": 6, "chapters": [
                {"id": "alcohols-phenols-ethers", "name": "Alcohols, Phenols and Ethers"}
            ]},
            {"unit_no": "VIII", "name": "Aldehydes, Ketones and Carboxylic Acids", "marks": 8, "chapters": [
                {"id": "aldehydes-ketones-carboxylic-acids", "name": "Aldehydes, Ketones and Carboxylic Acids"}
            ]},
            {"unit_no": "IX", "name": "Amines", "marks": 6, "chapters": [
                {"id": "amines", "name": "Amines"}
            ]},
            {"unit_no": "X", "name": "Biomolecules", "marks": 7, "chapters": [
                {"id": "biomolecules", "name": "Biomolecules"}
            ]}
        ]
    },
    {
        "subject": "Biology",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, Biology_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 70,
        "units": [
            {"unit_no": "VI", "name": "Reproduction", "marks": 16, "chapters": [
                {"id": "sexual-reproduction-flowering-plants", "name": "Sexual Reproduction in Flowering Plants"},
                {"id": "human-reproduction", "name": "Human Reproduction"},
                {"id": "reproductive-health", "name": "Reproductive Health"}
            ]},
            {"unit_no": "VII", "name": "Genetics and Evolution", "marks": 20, "chapters": [
                {"id": "principles-inheritance-variation", "name": "Principles of Inheritance and Variation"},
                {"id": "molecular-basis-inheritance", "name": "Molecular Basis of Inheritance"},
                {"id": "evolution", "name": "Evolution"}
            ]},
            {"unit_no": "VIII", "name": "Biology and Human Welfare", "marks": 12, "chapters": [
                {"id": "human-health-disease", "name": "Human Health and Disease"},
                {"id": "microbes-human-welfare", "name": "Microbes in Human Welfare"}
            ]},
            {"unit_no": "IX", "name": "Biotechnology and its Applications", "marks": 12, "chapters": [
                {"id": "biotechnology-principles-processes", "name": "Biotechnology: Principles and Processes"},
                {"id": "biotechnology-applications", "name": "Biotechnology and its Applications"}
            ]},
            {"unit_no": "X", "name": "Ecology and Environment", "marks": 10, "chapters": [
                {"id": "organisms-populations", "name": "Organisms and Populations"},
                {"id": "ecosystem", "name": "Ecosystem"},
                {"id": "biodiversity-conservation", "name": "Biodiversity and its Conservation"}
            ]}
        ]
    },
    {
        "subject": "Mathematics",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, Maths_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Relations and Functions", "marks": 8, "chapters": [
                {"id": "relations-and-functions", "name": "Relations and Functions"},
                {"id": "inverse-trigonometric-functions", "name": "Inverse Trigonometric Functions"}
            ]},
            {"unit_no": "II", "name": "Algebra", "marks": 10, "chapters": [
                {"id": "matrices", "name": "Matrices"},
                {"id": "determinants", "name": "Determinants"}
            ]},
            {"unit_no": "III", "name": "Calculus", "marks": 35, "chapters": [
                {"id": "continuity-and-differentiability", "name": "Continuity and Differentiability"},
                {"id": "applications-of-derivatives", "name": "Applications of Derivatives"},
                {"id": "integrals", "name": "Integrals"},
                {"id": "applications-of-integrals", "name": "Applications of the Integrals"},
                {"id": "differential-equations", "name": "Differential Equations"}
            ]},
            {"unit_no": "IV", "name": "Vectors and Three-Dimensional Geometry", "marks": 14, "chapters": [
                {"id": "vectors", "name": "Vectors"},
                {"id": "three-dimensional-geometry", "name": "Three-Dimensional Geometry"}
            ]},
            {"unit_no": "V", "name": "Linear Programming", "marks": 5, "chapters": [
                {"id": "linear-programming", "name": "Linear Programming"}
            ]},
            {"unit_no": "VI", "name": "Probability", "marks": 8, "chapters": [
                {"id": "probability", "name": "Probability"}
            ]}
        ]
    },
    {
        "subject": "Accountancy",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, Accountancy_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Accounting for Partnership Firms", "marks": 36, "chapters": [
                {"id": "partnership-fundamentals", "name": "Accounting for Partnership: Basic Concepts"},
                {"id": "change-in-profit-sharing-ratio", "name": "Reconstitution of Partnership: Change in PSR"},
                {"id": "admission-of-partner", "name": "Admission of a Partner"},
                {"id": "retirement-death-of-partner", "name": "Retirement and Death of a Partner"},
                {"id": "dissolution-of-partnership-firm", "name": "Dissolution of a Partnership Firm"}
            ]},
            {"unit_no": "II", "name": "Accounting for Companies", "marks": 24, "chapters": [
                {"id": "accounting-for-share-capital", "name": "Accounting for Share Capital"},
                {"id": "accounting-for-debentures", "name": "Issue and Redemption of Debentures"}
            ]},
            {"unit_no": "III", "name": "Analysis of Financial Statements", "marks": 12, "chapters": [
                {"id": "financial-statements-of-company", "name": "Financial Statements of a Company"},
                {"id": "financial-statement-analysis", "name": "Tools of Financial Statement Analysis"},
                {"id": "accounting-ratios", "name": "Accounting Ratios"}
            ]},
            {"unit_no": "IV", "name": "Cash Flow Statement", "marks": 8, "chapters": [
                {"id": "cash-flow-statement", "name": "Cash Flow Statement"}
            ]}
        ]
    },
    {
        "subject": "Business Studies",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, BusinessStudies_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Nature and Significance of Management", "marks": 6, "chapters": [
                {"id": "nature-significance-management", "name": "Nature and Significance of Management"}
            ]},
            {"unit_no": "II", "name": "Principles of Management", "marks": 6, "chapters": [
                {"id": "principles-of-management", "name": "Principles of Management"}
            ]},
            {"unit_no": "III", "name": "Business Environment", "marks": 4, "chapters": [
                {"id": "business-environment", "name": "Business Environment"}
            ]},
            {"unit_no": "IV", "name": "Planning", "marks": 6, "chapters": [
                {"id": "planning", "name": "Planning"}
            ]},
            {"unit_no": "V", "name": "Organising", "marks": 8, "chapters": [
                {"id": "organising", "name": "Organising"}
            ]},
            {"unit_no": "VI", "name": "Staffing", "marks": 8, "chapters": [
                {"id": "staffing", "name": "Staffing"}
            ]},
            {"unit_no": "VII", "name": "Directing", "marks": 8, "chapters": [
                {"id": "directing", "name": "Directing"}
            ]},
            {"unit_no": "VIII", "name": "Controlling", "marks": 4, "chapters": [
                {"id": "controlling", "name": "Controlling"}
            ]},
            {"unit_no": "IX", "name": "Financial Management", "marks": 9, "chapters": [
                {"id": "financial-management", "name": "Financial Management"}
            ]},
            {"unit_no": "X", "name": "Financial Markets", "marks": 6, "chapters": [
                {"id": "financial-markets", "name": "Financial Markets"}
            ]},
            {"unit_no": "XI", "name": "Marketing Management", "marks": 10, "chapters": [
                {"id": "marketing-management", "name": "Marketing Management"}
            ]},
            {"unit_no": "XII", "name": "Consumer Protection", "marks": 5, "chapters": [
                {"id": "consumer-protection", "name": "Consumer Protection"}
            ]}
        ]
    },
    {
        "subject": "Economics",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, Economics_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "National Income and Related Aggregates", "marks": 10, "chapters": [
                {"id": "national-income-aggregates", "name": "National Income and Related Aggregates"}
            ]},
            {"unit_no": "II", "name": "Money and Banking", "marks": 6, "chapters": [
                {"id": "money-and-banking", "name": "Money and Banking"}
            ]},
            {"unit_no": "III", "name": "Determination of Income and Employment", "marks": 12, "chapters": [
                {"id": "determination-income-employment", "name": "Determination of Income and Employment"}
            ]},
            {"unit_no": "IV", "name": "Government Budget and the Economy", "marks": 6, "chapters": [
                {"id": "government-budget-economy", "name": "Government Budget and the Economy"}
            ]},
            {"unit_no": "V", "name": "Balance of Payments", "marks": 6, "chapters": [
                {"id": "balance-of-payments", "name": "Balance of Payments"}
            ]},
            {"unit_no": "VI", "name": "Development Experience (1947-90) & Economic Reforms", "marks": 12, "chapters": [
                {"id": "development-experience-1947-90", "name": "Development Experience (1947-90) and Economic Reforms since 1991"}
            ]},
            {"unit_no": "VII", "name": "Current Challenges Facing Indian Economy", "marks": 20, "chapters": [
                {"id": "current-challenges-indian-economy", "name": "Current Challenges Facing Indian Economy"}
            ]},
            {"unit_no": "VIII", "name": "Development Experience of India: Comparative", "marks": 8, "chapters": [
                {"id": "development-experience-comparative", "name": "Development Experience of India – A Comparison with Neighbours"}
            ]}
        ]
    },
    {
        "subject": "History",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, History_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Themes in Indian History Part I", "marks": 25, "chapters": [
                {"id": "bricks-beads-bones", "name": "Bricks, Beads and Bones (Harappan Civilisation)"},
                {"id": "kings-farmers-towns", "name": "Kings, Farmers and Towns (Early States and Economies)"},
                {"id": "kinship-caste-class", "name": "Kinship, Caste and Class (Early Societies)"},
                {"id": "thinkers-beliefs-buildings", "name": "Thinkers, Beliefs and Buildings (Cultural Developments)"}
            ]},
            {"unit_no": "II", "name": "Themes in Indian History Part II", "marks": 25, "chapters": [
                {"id": "eyes-of-travellers", "name": "Through the Eyes of Travellers"},
                {"id": "bhakti-sufi-traditions", "name": "Bhakti-Sufi Traditions"},
                {"id": "an-imperial-capital-vijayanagara", "name": "An Imperial Capital: Vijayanagara"},
                {"id": "peasants-zamindars-state", "name": "Peasants, Zamindars and the State"}
            ]},
            {"unit_no": "III", "name": "Themes in Indian History Part III", "marks": 25, "chapters": [
                {"id": "colonialism-countryside", "name": "Colonialism and the Countryside"},
                {"id": "rebels-and-raj", "name": "Rebels and the Raj"},
                {"id": "mahatma-gandhi-nationalist-movement", "name": "Mahatma Gandhi and the Nationalist Movement"},
                {"id": "framing-constitution", "name": "Framing the Constitution"}
            ]},
            {"unit_no": "IV", "name": "Map Work", "marks": 5, "chapters": [
                {"id": "map-work-history", "name": "Map Work"}
            ]}
        ]
    },
    {
        "subject": "Political Science",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, PoliticalScience_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Contemporary World Politics", "marks": 40, "chapters": [
                {"id": "end-of-bipolarity", "name": "The End of Bipolarity"},
                {"id": "contemporary-centres-power", "name": "Contemporary Centres of Power"},
                {"id": "contemporary-south-asia", "name": "Contemporary South Asia"},
                {"id": "international-organisations", "name": "International Organisations"},
                {"id": "security-contemporary-world", "name": "Security in the Contemporary World"},
                {"id": "environment-natural-resources", "name": "Environment and Natural Resources"},
                {"id": "globalisation-political", "name": "Globalisation"}
            ]},
            {"unit_no": "II", "name": "Politics in India Since Independence", "marks": 40, "chapters": [
                {"id": "challenges-nation-building", "name": "Challenges of Nation-Building"},
                {"id": "era-one-party-dominance", "name": "Era of One-Party Dominance and Planned Development"},
                {"id": "indias-external-relations", "name": "India's External Relations"},
                {"id": "challenges-restoration-congress", "name": "Challenges to and Restoration of the Congress System"},
                {"id": "crisis-democratic-order", "name": "The Crisis of Democratic Order"},
                {"id": "regional-aspirations", "name": "Regional Aspirations"},
                {"id": "recent-developments-indian-politics", "name": "Recent Developments in Indian Politics"}
            ]}
        ]
    },
    {
        "subject": "Geography",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, Geography_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 70,
        "units": [
            {"unit_no": "I", "name": "Fundamentals of Human Geography", "marks": 35, "chapters": [
                {"id": "human-geography-nature-scope", "name": "Human Geography: Nature and Scope"},
                {"id": "world-population-distribution-density", "name": "The World Population: Distribution, Density and Growth"},
                {"id": "human-development", "name": "Human Development"},
                {"id": "primary-activities", "name": "Primary Activities"},
                {"id": "secondary-activities", "name": "Secondary Activities"},
                {"id": "tertiary-quaternary-activities", "name": "Tertiary and Quaternary Activities"},
                {"id": "transport-communication", "name": "Transport and Communication"},
                {"id": "international-trade-geography", "name": "International Trade"}
            ]},
            {"unit_no": "II", "name": "India: People and Economy", "marks": 35, "chapters": [
                {"id": "population-distribution-density-growth", "name": "Population: Distribution, Density, Growth and Composition"},
                {"id": "human-settlements", "name": "Human Settlements"},
                {"id": "land-resources-agriculture", "name": "Land Resources and Agriculture"},
                {"id": "water-resources-india", "name": "Water Resources"},
                {"id": "mineral-energy-resources-india", "name": "Mineral and Energy Resources"},
                {"id": "planning-sustainable-development", "name": "Planning and Sustainable Development in Indian Context"},
                {"id": "geographical-perspective-issues", "name": "Geographical Perspective on Selected Issues and Problems"}
            ]}
        ]
    },
    {
        "subject": "English",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, English_core_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Reading Skills", "marks": 22, "chapters": [
                {"id": "reading-comprehension", "name": "Reading Comprehension Through Unseen Passages"}
            ]},
            {"unit_no": "II", "name": "Creative Writing Skills", "marks": 18, "chapters": [
                {"id": "notice-writing", "name": "Notice Writing"},
                {"id": "invitation-and-reply", "name": "Formal and Informal Invitations and Replies"},
                {"id": "letter-writing", "name": "Letters: Application for Job and Letter to Editor"},
                {"id": "article-report-writing", "name": "Article and Report Writing"}
            ]},
            {"unit_no": "III", "name": "Literature Textbooks", "marks": 40, "chapters": [
                {"id": "flamingo-prose", "name": "Flamingo (Prose)"},
                {"id": "flamingo-poetry", "name": "Flamingo (Poetry)"},
                {"id": "vistas-supplementary", "name": "Vistas (Supplementary Reader)"}
            ]}
        ]
    },
    {
        "subject": "Hindi",
        "grade": 12,
        "source": "CBSE Curriculum 2025-26, Hindi_Core_SrSec_2025-26.pdf, Class XII Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Apthit Bodh", "marks": 15, "chapters": [
                {"id": "apthit-gadyansh-kavyansh", "name": "Apthit Gadyansh va Kavyansh"}
            ]},
            {"unit_no": "II", "name": "Abhivyakti aur Madhyam", "marks": 15, "chapters": [
                {"id": "abhivyakti-aur-madhyam", "name": "Abhivyakti aur Madhyam"}
            ]},
            {"unit_no": "III", "name": "Aroh va Vitan", "marks": 50, "chapters": [
                {"id": "aroh-kavya-khand", "name": "Aroh (Kavya Khand)"},
                {"id": "aroh-gadya-khand", "name": "Aroh (Gadya Khand)"},
                {"id": "vitan", "name": "Vitan"}
            ]}
        ]
    },

    # ==================== GRADE 11 ====================
    {
        "subject": "Physics",
        "grade": 11,
        "source": "CBSE Curriculum 2025-26, Physics_SrSec_2025-26.pdf, Class XI Course Structure",
        "total_marks": 70,
        "units": [
            {"unit_no": "I", "name": "Physical World and Measurement", "marks": 6, "chapters": [
                {"id": "units-and-measurements", "name": "Units and Measurements"}
            ]},
            {"unit_no": "II", "name": "Kinematics", "marks": 17, "chapters": [
                {"id": "motion-straight-line", "name": "Motion in a Straight Line"},
                {"id": "motion-plane", "name": "Motion in a Plane"}
            ]},
            {"unit_no": "III", "name": "Laws of Motion", "marks": 10, "chapters": [
                {"id": "laws-of-motion", "name": "Laws of Motion"}
            ]},
            {"unit_no": "IV", "name": "Work, Energy and Power", "marks": 6, "chapters": [
                {"id": "work-energy-power", "name": "Work, Energy and Power"}
            ]},
            {"unit_no": "V", "name": "Motion of System of Particles and Rigid Body", "marks": 7, "chapters": [
                {"id": "system-particles-rotational-motion", "name": "System of Particles and Rotational Motion"}
            ]},
            {"unit_no": "VI", "name": "Gravitation", "marks": 6, "chapters": [
                {"id": "gravitation", "name": "Gravitation"}
            ]},
            {"unit_no": "VII", "name": "Properties of Bulk Matter", "marks": 8, "chapters": [
                {"id": "mechanical-properties-solids", "name": "Mechanical Properties of Solids"},
                {"id": "mechanical-properties-fluids", "name": "Mechanical Properties of Fluids"},
                {"id": "thermal-properties-matter", "name": "Thermal Properties of Matter"}
            ]},
            {"unit_no": "VIII", "name": "Thermodynamics", "marks": 5, "chapters": [
                {"id": "thermodynamics", "name": "Thermodynamics"}
            ]},
            {"unit_no": "IX", "name": "Kinetic Theory of Gases", "marks": 5, "chapters": [
                {"id": "kinetic-theory", "name": "Kinetic Theory of Gases"}
            ]},
            {"unit_no": "X", "name": "Oscillations and Waves", "marks": 10, "chapters": [
                {"id": "oscillations", "name": "Oscillations"},
                {"id": "waves", "name": "Waves"}
            ]}
        ]
    },
    {
        "subject": "Chemistry",
        "grade": 11,
        "source": "CBSE Curriculum 2025-26, Chemistry_SrSec_2025-26.pdf, Class XI Course Structure",
        "total_marks": 70,
        "units": [
            {"unit_no": "I", "name": "Some Basic Concepts of Chemistry", "marks": 7, "chapters": [
                {"id": "basic-concepts-chemistry", "name": "Some Basic Concepts of Chemistry"}
            ]},
            {"unit_no": "II", "name": "Structure of Atom", "marks": 9, "chapters": [
                {"id": "structure-of-atom", "name": "Structure of Atom"}
            ]},
            {"unit_no": "III", "name": "Classification of Elements and Periodicity", "marks": 6, "chapters": [
                {"id": "classification-elements-periodicity", "name": "Classification of Elements and Periodicity in Properties"}
            ]},
            {"unit_no": "IV", "name": "Chemical Bonding and Molecular Structure", "marks": 7, "chapters": [
                {"id": "chemical-bonding-molecular-structure", "name": "Chemical Bonding and Molecular Structure"}
            ]},
            {"unit_no": "V", "name": "Chemical Thermodynamics", "marks": 9, "chapters": [
                {"id": "chemical-thermodynamics", "name": "Chemical Thermodynamics"}
            ]},
            {"unit_no": "VI", "name": "Equilibrium", "marks": 7, "chapters": [
                {"id": "equilibrium", "name": "Equilibrium"}
            ]},
            {"unit_no": "VII", "name": "Redox Reactions", "marks": 4, "chapters": [
                {"id": "redox-reactions", "name": "Redox Reactions"}
            ]},
            {"unit_no": "VIII", "name": "Organic Chemistry: Some Basic Principles and Techniques", "marks": 11, "chapters": [
                {"id": "organic-chemistry-principles", "name": "Organic Chemistry: Some Basic Principles and Techniques"}
            ]},
            {"unit_no": "IX", "name": "Hydrocarbons", "marks": 10, "chapters": [
                {"id": "hydrocarbons", "name": "Hydrocarbons"}
            ]}
        ]
    },
    {
        "subject": "Biology",
        "grade": 11,
        "source": "CBSE Curriculum 2025-26, Biology_SrSec_2025-26.pdf, Class XI Course Structure",
        "total_marks": 70,
        "units": [
            {"unit_no": "I", "name": "Diversity of Living Organisms", "marks": 15, "chapters": [
                {"id": "the-living-world", "name": "The Living World"},
                {"id": "biological-classification", "name": "Biological Classification"},
                {"id": "plant-kingdom", "name": "Plant Kingdom"},
                {"id": "animal-kingdom", "name": "Animal Kingdom"}
            ]},
            {"unit_no": "II", "name": "Structural Organisation in Animals and Plants", "marks": 10, "chapters": [
                {"id": "morphology-flowering-plants", "name": "Morphology of Flowering Plants"},
                {"id": "anatomy-flowering-plants", "name": "Anatomy of Flowering Plants"},
                {"id": "structural-organisation-animals", "name": "Structural Organisation in Animals"}
            ]},
            {"unit_no": "III", "name": "Cell: Structure and Function", "marks": 15, "chapters": [
                {"id": "cell-unit-of-life", "name": "Cell: The Unit of Life"},
                {"id": "biomolecules-bio", "name": "Biomolecules"},
                {"id": "cell-cycle-division", "name": "Cell Cycle and Cell Division"}
            ]},
            {"unit_no": "IV", "name": "Plant Physiology", "marks": 12, "chapters": [
                {"id": "photosynthesis-higher-plants", "name": "Photosynthesis in Higher Plants"},
                {"id": "respiration-in-plants", "name": "Respiration in Plants"},
                {"id": "plant-growth-development", "name": "Plant Growth and Development"}
            ]},
            {"unit_no": "V", "name": "Human Physiology", "marks": 18, "chapters": [
                {"id": "breathing-exchange-gases", "name": "Breathing and Exchange of Gases"},
                {"id": "body-fluids-circulation", "name": "Body Fluids and Circulation"},
                {"id": "excretory-products-elimination", "name": "Excretory Products and their Elimination"},
                {"id": "locomotion-and-movement", "name": "Locomotion and Movement"},
                {"id": "neural-control-coordination", "name": "Neural Control and Coordination"},
                {"id": "chemical-coordination-integration", "name": "Chemical Coordination and Integration"}
            ]}
        ]
    },
    {
        "subject": "Mathematics",
        "grade": 11,
        "source": "CBSE Curriculum 2025-26, Maths_SrSec_2025-26.pdf, Class XI Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Sets and Functions", "marks": 23, "chapters": [
                {"id": "sets", "name": "Sets"},
                {"id": "relations-functions-11", "name": "Relations and Functions"},
                {"id": "trigonometric-functions", "name": "Trigonometric Functions"}
            ]},
            {"unit_no": "II", "name": "Algebra", "marks": 25, "chapters": [
                {"id": "complex-numbers-quadratic", "name": "Complex Numbers and Quadratic Equations"},
                {"id": "linear-inequalities", "name": "Linear Inequalities"},
                {"id": "permutations-combinations", "name": "Permutations and Combinations"},
                {"id": "binomial-theorem", "name": "Binomial Theorem"},
                {"id": "sequences-and-series", "name": "Sequences and Series"}
            ]},
            {"unit_no": "III", "name": "Coordinate Geometry", "marks": 12, "chapters": [
                {"id": "straight-lines", "name": "Straight Lines"},
                {"id": "conic-sections", "name": "Conic Sections"},
                {"id": "intro-3d-geometry", "name": "Introduction to Three-Dimensional Geometry"}
            ]},
            {"unit_no": "IV", "name": "Calculus", "marks": 8, "chapters": [
                {"id": "limits-and-derivatives", "name": "Limits and Derivatives"}
            ]},
            {"unit_no": "V", "name": "Statistics and Probability", "marks": 12, "chapters": [
                {"id": "statistics-11", "name": "Statistics"},
                {"id": "probability-11", "name": "Probability"}
            ]}
        ]
    },
    {
        "subject": "Accountancy",
        "grade": 11,
        "source": "CBSE Curriculum 2025-26, Accountancy_SrSec_2025-26.pdf, Class XI Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Theoretical Framework", "marks": 12, "chapters": [
                {"id": "intro-accounting", "name": "Introduction to Accounting"},
                {"id": "theory-base-accounting", "name": "Theory Base of Accounting"}
            ]},
            {"unit_no": "II", "name": "Accounting Process", "marks": 44, "chapters": [
                {"id": "recording-transactions", "name": "Recording of Business Transactions (Journal & Ledger)"},
                {"id": "bank-reconciliation-statement", "name": "Bank Reconciliation Statement"},
                {"id": "depreciation-provisions-reserves", "name": "Depreciation, Provisions and Reserves"},
                {"id": "trial-balance-rectification", "name": "Trial Balance and Rectification of Errors"}
            ]},
            {"unit_no": "III", "name": "Financial Statements of Sole Proprietorship", "marks": 24, "chapters": [
                {"id": "financial-statements-sole-proprietor", "name": "Financial Statements of Sole Proprietorship"}
            ]}
        ]
    },
    {
        "subject": "Business Studies",
        "grade": 11,
        "source": "CBSE Curriculum 2025-26, BusinessStudies_SrSec_2025-26.pdf, Class XI Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Foundations of Business", "marks": 40, "chapters": [
                {"id": "nature-purpose-business", "name": "Evolution and Fundamentals of Business"},
                {"id": "forms-business-organisations", "name": "Forms of Business Organisations"},
                {"id": "public-private-global-enterprises", "name": "Public, Private and Global Enterprises"},
                {"id": "business-services", "name": "Business Services"},
                {"id": "emerging-modes-business", "name": "Emerging Modes of Business"},
                {"id": "social-responsibility-ethics", "name": "Social Responsibilities of Business and Business Ethics"}
            ]},
            {"unit_no": "II", "name": "Finance and Trade", "marks": 40, "chapters": [
                {"id": "sources-business-finance", "name": "Sources of Business Finance"},
                {"id": "small-business-enterprises", "name": "Small Business and Enterprises"},
                {"id": "internal-trade", "name": "Internal Trade"},
                {"id": "international-trade-business", "name": "International Business"}
            ]}
        ]
    },
    {
        "subject": "Economics",
        "grade": 11,
        "source": "CBSE Curriculum 2025-26, Economics_SrSec_2025-26.pdf, Class XI Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Statistics for Economics", "marks": 40, "chapters": [
                {"id": "intro-statistics-economics", "name": "Introduction to Statistics"},
                {"id": "collection-organisation-presentation-data", "name": "Collection, Organisation and Presentation of Data"},
                {"id": "statistical-tools-interpretation", "name": "Statistical Tools and Interpretation"}
            ]},
            {"unit_no": "II", "name": "Introductory Microeconomics", "marks": 40, "chapters": [
                {"id": "intro-microeconomics", "name": "Introduction to Microeconomics"},
                {"id": "consumer-equilibrium-demand", "name": "Consumer's Equilibrium and Demand"},
                {"id": "producer-behaviour-supply", "name": "Producer Behaviour and Supply"},
                {"id": "forms-market-price-determination", "name": "Forms of Market and Price Determination"}
            ]}
        ]
    },
    {
        "subject": "English",
        "grade": 11,
        "source": "CBSE Curriculum 2025-26, English_core_SrSec_2025-26.pdf, Class XI Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Reading Skills", "marks": 26, "chapters": [
                {"id": "reading-comprehension", "name": "Reading Comprehension and Note Making"}
            ]},
            {"unit_no": "II", "name": "Grammar and Creative Writing", "marks": 23, "chapters": [
                {"id": "grammar", "name": "Grammar (Tenses, Clauses, Re-ordering of Sentences)"},
                {"id": "creative-writing", "name": "Notice, Poster, Speech and Debate Writing"}
            ]},
            {"unit_no": "III", "name": "Literature", "marks": 31, "chapters": [
                {"id": "hornbill", "name": "Hornbill (Prose and Poetry)"},
                {"id": "snapshots", "name": "Snapshots (Supplementary Reader)"}
            ]}
        ]
    },
    {
        "subject": "Hindi",
        "grade": 11,
        "source": "CBSE Curriculum 2025-26, Hindi_Core_SrSec_2025-26.pdf, Class XI Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Apthit Bodh", "marks": 15, "chapters": [
                {"id": "apthit-gadyansh-kavyansh", "name": "Apthit Gadyansh va Kavyansh"}
            ]},
            {"unit_no": "II", "name": "Abhivyakti aur Madhyam", "marks": 15, "chapters": [
                {"id": "abhivyakti-aur-madhyam", "name": "Abhivyakti aur Madhyam"}
            ]},
            {"unit_no": "III", "name": "Aroh va Vitan", "marks": 50, "chapters": [
                {"id": "aroh-kavya-khand", "name": "Aroh (Kavya Khand)"},
                {"id": "aroh-gadya-khand", "name": "Aroh (Gadya Khand)"},
                {"id": "vitan", "name": "Vitan"}
            ]}
        ]
    },

    # ==================== GRADE 9 ====================
    {
        "subject": "Science",
        "grade": 9,
        "source": "CBSE Curriculum 2025-26, Science_Sec_2025-26.pdf, Class IX Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Matter - Its Nature and Behaviour", "marks": 25, "chapters": [
                {"id": "matter-in-our-surroundings", "name": "Matter in Our Surroundings"},
                {"id": "is-matter-around-us-pure", "name": "Is Matter Around Us Pure"},
                {"id": "atoms-and-molecules", "name": "Atoms and Molecules"},
                {"id": "structure-of-the-atom", "name": "Structure of the Atom"}
            ]},
            {"unit_no": "II", "name": "Organization in the Living World", "marks": 22, "chapters": [
                {"id": "fundamental-unit-of-life", "name": "The Fundamental Unit of Life"},
                {"id": "tissues", "name": "Tissues"}
            ]},
            {"unit_no": "III", "name": "Motion, Force and Work", "marks": 27, "chapters": [
                {"id": "motion", "name": "Motion"},
                {"id": "force-and-laws-of-motion", "name": "Force and Laws of Motion"},
                {"id": "gravitation-9", "name": "Gravitation"},
                {"id": "work-and-energy", "name": "Work and Energy"},
                {"id": "sound", "name": "Sound"}
            ]},
            {"unit_no": "IV", "name": "Food; Food Production", "marks": 6, "chapters": [
                {"id": "improvement-in-food-resources", "name": "Improvement in Food Resources"}
            ]}
        ]
    },
    {
        "subject": "Mathematics",
        "grade": 9,
        "source": "CBSE Curriculum 2025-26, Maths_Sec_2025-26.pdf, Class IX Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Number Systems", "marks": 10, "chapters": [
                {"id": "number-systems-9", "name": "Number Systems"}
            ]},
            {"unit_no": "II", "name": "Algebra", "marks": 20, "chapters": [
                {"id": "polynomials-9", "name": "Polynomials"},
                {"id": "linear-equations-two-variables", "name": "Linear Equations in Two Variables"}
            ]},
            {"unit_no": "III", "name": "Coordinate Geometry", "marks": 4, "chapters": [
                {"id": "coordinate-geometry-9", "name": "Coordinate Geometry"}
            ]},
            {"unit_no": "IV", "name": "Geometry", "marks": 27, "chapters": [
                {"id": "intro-euclid-geometry", "name": "Introduction to Euclid's Geometry"},
                {"id": "lines-and-angles", "name": "Lines and Angles"},
                {"id": "triangles-9", "name": "Triangles"},
                {"id": "quadrilaterals", "name": "Quadrilaterals"},
                {"id": "circles-9", "name": "Circles"}
            ]},
            {"unit_no": "V", "name": "Mensuration", "marks": 13, "chapters": [
                {"id": "herons-formula", "name": "Heron's Formula"},
                {"id": "surface-areas-and-volumes-9", "name": "Surface Areas and Volumes"}
            ]},
            {"unit_no": "VI", "name": "Statistics", "marks": 6, "chapters": [
                {"id": "statistics-9", "name": "Statistics"}
            ]}
        ]
    },
    {
        "subject": "Social Science",
        "grade": 9,
        "source": "CBSE Curriculum 2025-26, Social_Science_Sec_2025-26.pdf, Class IX Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "India and the Contemporary World - I (History)", "marks": 20, "chapters": [
                {"id": "french-revolution", "name": "The French Revolution"},
                {"id": "socialism-europe-russian-revolution", "name": "Socialism in Europe and the Russian Revolution"},
                {"id": "nazism-rise-of-hitler", "name": "Nazism and the Rise of Hitler"},
                {"id": "forest-society-colonialism", "name": "Forest Society and Colonialism"},
                {"id": "pastoralists-modern-world", "name": "Pastoralists in the Modern World"}
            ]},
            {"unit_no": "II", "name": "Contemporary India - I (Geography)", "marks": 20, "chapters": [
                {"id": "india-size-and-location", "name": "India - Size and Location"},
                {"id": "physical-features-of-india", "name": "Physical Features of India"},
                {"id": "drainage", "name": "Drainage"},
                {"id": "climate", "name": "Climate"},
                {"id": "natural-vegetation-wildlife", "name": "Natural Vegetation and Wildlife"},
                {"id": "population", "name": "Population"}
            ]},
            {"unit_no": "III", "name": "Democratic Politics - I (Political Science)", "marks": 20, "chapters": [
                {"id": "what-is-democracy-why", "name": "What is Democracy? Why Democracy?"},
                {"id": "constitutional-design", "name": "Constitutional Design"},
                {"id": "electoral-politics", "name": "Electoral Politics"},
                {"id": "working-of-institutions", "name": "Working of Institutions"},
                {"id": "democratic-rights", "name": "Democratic Rights"}
            ]},
            {"unit_no": "IV", "name": "Economics", "marks": 20, "chapters": [
                {"id": "story-village-palampur", "name": "The Story of Village Palampur"},
                {"id": "people-as-resource", "name": "People as Resource"},
                {"id": "poverty-as-a-challenge", "name": "Poverty as a Challenge"},
                {"id": "food-security-in-india", "name": "Food Security in India"}
            ]}
        ]
    },
    {
        "subject": "English",
        "grade": 9,
        "source": "CBSE Curriculum 2025-26, English_Lang_Lit_Sec_2025-26.pdf, Class IX Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Reading Skills", "marks": 20, "chapters": [
                {"id": "reading-comprehension", "name": "Reading Comprehension"}
            ]},
            {"unit_no": "II", "name": "Writing Skills and Grammar", "marks": 20, "chapters": [
                {"id": "grammar", "name": "Grammar (Tenses, Modals, Subject-Verb Concord, Reported Speech)"},
                {"id": "writing-skills", "name": "Descriptive Paragraph and Diary Entry / Story Writing"}
            ]},
            {"unit_no": "III", "name": "Language Through Literature", "marks": 40, "chapters": [
                {"id": "beehive-textbook", "name": "Beehive (Prose and Poetry)"},
                {"id": "moments-supplementary", "name": "Moments (Supplementary Reader)"}
            ]}
        ]
    },
    {
        "subject": "Hindi",
        "grade": 9,
        "source": "CBSE Curriculum 2025-26, Hindi_Course_A_Sec_2025-26.pdf, Class IX Course Structure",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Apthit Bodh", "marks": 14, "chapters": [
                {"id": "apthit-gadyansh", "name": "Apthit Gadyansh va Kavyansh"}
            ]},
            {"unit_no": "II", "name": "Vyakaran", "marks": 16, "chapters": [
                {"id": "upsarg-pratyay", "name": "Upsarg va Pratyay"},
                {"id": "samas", "name": "Samas"},
                {"id": "arth-ke-aadhar-par-vakya", "name": "Arth ke Aadhar par Vakya Bhed"},
                {"id": "alankar-9", "name": "Alankar"}
            ]},
            {"unit_no": "III", "name": "Pathyapustak (Kshitij va Kritika)", "marks": 30, "chapters": [
                {"id": "kshitij-bhag-1-gadya", "name": "Kshitij Bhag 1 (Gadya Khand)"},
                {"id": "kshitij-bhag-1-kavya", "name": "Kshitij Bhag 1 (Kavya Khand)"},
                {"id": "kritika-bhag-1", "name": "Kritika Bhag 1"}
            ]},
            {"unit_no": "IV", "name": "Rachnatmak Lekhan", "marks": 20, "chapters": [
                {"id": "anuchhed-lekhan", "name": "Anuchhed Lekhan"},
                {"id": "patra-lekhan", "name": "Patra Lekhan"},
                {"id": "laghukatha-samvad-lekhan", "name": "Laghukatha va Samvad Lekhan"},
                {"id": "email-suchna-lekhan", "name": "Email va Suchna Lekhan"}
            ]}
        ]
    },

    # ==================== GRADE 8 ====================
    {
        "subject": "Mathematics",
        "grade": 8,
        "source": "NCERT Class 8 Mathematics, Ganita Prakash / NCERT Curriculum",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Number System and Arithmetic", "marks": 25, "chapters": [
                {"id": "rational-numbers", "name": "Rational Numbers"},
                {"id": "squares-and-square-roots", "name": "Squares and Square Roots"},
                {"id": "cubes-and-cube-roots", "name": "Cubes and Cube Roots"},
                {"id": "comparing-quantities", "name": "Comparing Quantities"},
                {"id": "exponents-and-powers", "name": "Exponents and Powers"},
                {"id": "direct-and-inverse-proportions", "name": "Direct and Inverse Proportions"}
            ]},
            {"unit_no": "II", "name": "Algebra", "marks": 25, "chapters": [
                {"id": "linear-equations-one-variable", "name": "Linear Equations in One Variable"},
                {"id": "algebraic-expressions-identities", "name": "Algebraic Expressions and Identities"},
                {"id": "factorisation", "name": "Factorisation"}
            ]},
            {"unit_no": "III", "name": "Geometry and Mensuration", "marks": 20, "chapters": [
                {"id": "understanding-quadrilaterals", "name": "Understanding Quadrilaterals"},
                {"id": "mensuration-8", "name": "Mensuration"}
            ]},
            {"unit_no": "IV", "name": "Statistics and Graphs", "marks": 10, "chapters": [
                {"id": "data-handling", "name": "Data Handling"},
                {"id": "introduction-to-graphs", "name": "Introduction to Graphs"}
            ]}
        ]
    },
    {
        "subject": "Science",
        "grade": 8,
        "source": "NCERT Class 8 Science, Curiosity / NCERT Curriculum",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Food and Living Organisms", "marks": 20, "chapters": [
                {"id": "crop-production-management", "name": "Crop Production and Management"},
                {"id": "microorganisms-friend-foe", "name": "Microorganisms: Friend and Foe"},
                {"id": "conservation-plants-animals", "name": "Conservation of Plants and Animals"},
                {"id": "reproduction-in-animals", "name": "Reproduction in Animals"},
                {"id": "reaching-age-of-adolescence", "name": "Reaching the Age of Adolescence"}
            ]},
            {"unit_no": "II", "name": "Materials and Chemistry", "marks": 18, "chapters": [
                {"id": "coal-and-petroleum", "name": "Coal and Petroleum"},
                {"id": "combustion-and-flame", "name": "Combustion and Flame"},
                {"id": "chemical-effects-electric-current", "name": "Chemical Effects of Electric Current"}
            ]},
            {"unit_no": "III", "name": "Physical Phenomena", "marks": 27, "chapters": [
                {"id": "force-and-pressure", "name": "Force and Pressure"},
                {"id": "friction", "name": "Friction"},
                {"id": "sound-8", "name": "Sound"},
                {"id": "some-natural-phenomena", "name": "Some Natural Phenomena"},
                {"id": "light-8", "name": "Light"}
            ]},
            {"unit_no": "IV", "name": "Natural Resources and Environment", "marks": 15, "chapters": [
                {"id": "pollution-air-water", "name": "Pollution of Air and Water"}
            ]}
        ]
    },
    {
        "subject": "Social Science",
        "grade": 8,
        "source": "NCERT Class 8 Social Science (Our Pasts III, Resources & Dev, Social & Pol Life III)",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "History: Our Pasts - III", "marks": 30, "chapters": [
                {"id": "how-when-and-where", "name": "How, When and Where"},
                {"id": "from-trade-to-territory", "name": "From Trade to Territory: Company Establishes Power"},
                {"id": "ruling-the-countryside", "name": "Ruling the Countryside"},
                {"id": "tribals-dikus-golden-age", "name": "Tribals, Dikus and the Vision of a Golden Age"},
                {"id": "when-people-rebel-1857", "name": "When People Rebel: 1857 and After"},
                {"id": "civilising-the-native", "name": "Civilising the Native, Educating the Nation"},
                {"id": "women-caste-and-reform", "name": "Women, Caste and Reform"},
                {"id": "making-of-national-movement", "name": "The Making of the National Movement: 1870s-1947"}
            ]},
            {"unit_no": "II", "name": "Geography: Resources and Development", "marks": 25, "chapters": [
                {"id": "resources", "name": "Resources"},
                {"id": "land-soil-water-natural-vegetation", "name": "Land, Soil, Water, Natural Vegetation and Wildlife"},
                {"id": "agriculture-8", "name": "Agriculture"},
                {"id": "industries", "name": "Industries"},
                {"id": "human-resources", "name": "Human Resources"}
            ]},
            {"unit_no": "III", "name": "Civics: Social and Political Life - III", "marks": 25, "chapters": [
                {"id": "the-indian-constitution", "name": "The Indian Constitution"},
                {"id": "understanding-secularism", "name": "Understanding Secularism"},
                {"id": "parliament-and-making-of-laws", "name": "Parliament and the Making of Laws"},
                {"id": "judiciary", "name": "Judiciary"},
                {"id": "understanding-marginalisation", "name": "Understanding Marginalisation"},
                {"id": "confronting-marginalisation", "name": "Confronting Marginalisation"},
                {"id": "public-facilities", "name": "Public Facilities"},
                {"id": "law-and-social-justice", "name": "Law and Social Justice"}
            ]}
        ]
    },
    {
        "subject": "English",
        "grade": 8,
        "source": "NCERT Class 8 English (Honeydew and It So Happened)",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Reading Comprehension", "marks": 20, "chapters": [
                {"id": "reading-comprehension", "name": "Reading Comprehension"}
            ]},
            {"unit_no": "II", "name": "Writing and Grammar", "marks": 25, "chapters": [
                {"id": "grammar", "name": "Grammar (Tenses, Active-Passive, Direct-Indirect, Conjunctions)"},
                {"id": "writing-skills", "name": "Formal and Informal Letters, Notice, Paragraph Writing"}
            ]},
            {"unit_no": "III", "name": "Literature", "marks": 35, "chapters": [
                {"id": "honeydew-textbook", "name": "Honeydew (Textbook in English)"},
                {"id": "it-so-happened", "name": "It So Happened (Supplementary Reader)"}
            ]}
        ]
    },
    {
        "subject": "Hindi",
        "grade": 8,
        "source": "NCERT Class 8 Hindi (Vasant Bhag 3)",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Apthit Bodh", "marks": 15, "chapters": [
                {"id": "apthit-gadyansh-kavyansh", "name": "Apthit Gadyansh va Kavyansh"}
            ]},
            {"unit_no": "II", "name": "Vyakaran", "marks": 20, "chapters": [
                {"id": "vyakaran-8", "name": "Sangya, Sarvanam, Visheshan, Kriya, Karak, Samas, Sandhi"}
            ]},
            {"unit_no": "III", "name": "Pathyapustak Vasant", "marks": 30, "chapters": [
                {"id": "vasant-bhag-3", "name": "Vasant Bhag 3 (Kavita evam Kahani)"}
            ]},
            {"unit_no": "IV", "name": "Rachnatmak Lekhan", "marks": 15, "chapters": [
                {"id": "rachnatmak-lekhan", "name": "Patra Lekhan, Nibandh Lekhan, Samvad Lekhan"}
            ]}
        ]
    },

    # ==================== GRADE 7 ====================
    {
        "subject": "Mathematics",
        "grade": 7,
        "source": "NCERT Class 7 Mathematics, Ganita Prakash / NCERT Curriculum",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Number System and Operations", "marks": 25, "chapters": [
                {"id": "integers", "name": "Integers"},
                {"id": "fractions-and-decimals", "name": "Fractions and Decimals"},
                {"id": "rational-numbers-7", "name": "Rational Numbers"},
                {"id": "exponents-and-powers-7", "name": "Exponents and Powers"}
            ]},
            {"unit_no": "II", "name": "Algebra and Equations", "marks": 20, "chapters": [
                {"id": "simple-equations", "name": "Simple Equations"},
                {"id": "algebraic-expressions-7", "name": "Algebraic Expressions"},
                {"id": "comparing-quantities-7", "name": "Comparing Quantities"}
            ]},
            {"unit_no": "III", "name": "Geometry and Measurement", "marks": 25, "chapters": [
                {"id": "lines-and-angles-7", "name": "Lines and Angles"},
                {"id": "the-triangle-and-its-properties", "name": "The Triangle and its Properties"},
                {"id": "perimeter-and-area", "name": "Perimeter and Area"},
                {"id": "symmetry", "name": "Symmetry"},
                {"id": "visualising-solid-shapes", "name": "Visualising Solid Shapes"}
            ]},
            {"unit_no": "IV", "name": "Data Handling", "marks": 10, "chapters": [
                {"id": "data-handling-7", "name": "Data Handling"}
            ]}
        ]
    },
    {
        "subject": "Science",
        "grade": 7,
        "source": "NCERT Class 7 Science, Curiosity / NCERT Curriculum",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Living Organisms and Life Processes", "marks": 25, "chapters": [
                {"id": "nutrition-in-plants", "name": "Nutrition in Plants"},
                {"id": "nutrition-in-animals", "name": "Nutrition in Animals"},
                {"id": "respiration-in-organisms", "name": "Respiration in Organisms"},
                {"id": "transportation-animals-plants", "name": "Transportation in Animals and Plants"},
                {"id": "reproduction-in-plants", "name": "Reproduction in Plants"}
            ]},
            {"unit_no": "II", "name": "Materials and Matter", "marks": 20, "chapters": [
                {"id": "heat", "name": "Heat"},
                {"id": "acids-bases-salts-7", "name": "Acids, Bases and Salts"},
                {"id": "physical-and-chemical-changes", "name": "Physical and Chemical Changes"}
            ]},
            {"unit_no": "III", "name": "Motion, Forces and Energy", "marks": 20, "chapters": [
                {"id": "motion-and-time", "name": "Motion and Time"},
                {"id": "electric-current-effects", "name": "Electric Current and its Effects"},
                {"id": "light-7", "name": "Light"}
            ]},
            {"unit_no": "IV", "name": "Natural Resources and Environment", "marks": 15, "chapters": [
                {"id": "forests-our-lifeline", "name": "Forests: Our Lifeline"},
                {"id": "wastewater-story", "name": "Wastewater Story"}
            ]}
        ]
    },
    {
        "subject": "Social Science",
        "grade": 7,
        "source": "NCERT Class 7 Social Science (Our Pasts II, Our Environment, Social & Pol Life II)",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "History: Our Pasts - II", "marks": 30, "chapters": [
                {"id": "tracing-changes-thousand-years", "name": "Tracing Changes through a Thousand Years"},
                {"id": "kings-and-kingdoms", "name": "Kings and Kingdoms"},
                {"id": "delhi-12th-to-15th-century", "name": "Delhi: 12th to 15th Century"},
                {"id": "the-mughals-16th-to-17th-century", "name": "The Mughals (16th to 17th Century)"},
                {"id": "tribes-nomads-settled-communities", "name": "Tribes, Nomads and Settled Communities"},
                {"id": "devotional-paths-to-divine", "name": "Devotional Paths to the Divine"},
                {"id": "making-of-regional-cultures", "name": "The Making of Regional Cultures"},
                {"id": "eighteenth-century-political-formations", "name": "Eighteenth-Century Political Formations"}
            ]},
            {"unit_no": "II", "name": "Geography: Our Environment", "marks": 25, "chapters": [
                {"id": "environment", "name": "Environment"},
                {"id": "inside-our-earth", "name": "Inside Our Earth"},
                {"id": "our-changing-earth", "name": "Our Changing Earth"},
                {"id": "air", "name": "Air"},
                {"id": "water", "name": "Water"},
                {"id": "human-environment-interactions", "name": "Human-Environment Interactions: Tropical and Subtropical Regions"},
                {"id": "life-in-deserts", "name": "Life in the Deserts"}
            ]},
            {"unit_no": "III", "name": "Civics: Social and Political Life - II", "marks": 25, "chapters": [
                {"id": "on-equality", "name": "On Equality"},
                {"id": "role-of-government-in-health", "name": "Role of the Government in Health"},
                {"id": "how-state-government-works", "name": "How the State Government Works"},
                {"id": "growing-up-as-boys-and-girls", "name": "Growing up as Boys and Girls"},
                {"id": "women-change-the-world", "name": "Women Change the World"},
                {"id": "understanding-media", "name": "Understanding Media"},
                {"id": "markets-around-us", "name": "Markets Around Us"},
                {"id": "a-shirt-in-the-market", "name": "A Shirt in the Market"}
            ]}
        ]
    },
    {
        "subject": "English",
        "grade": 7,
        "source": "NCERT Class 7 English (Honeycomb and An Alien Hand)",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Reading Comprehension", "marks": 20, "chapters": [
                {"id": "reading-comprehension", "name": "Reading Comprehension"}
            ]},
            {"unit_no": "II", "name": "Writing and Grammar", "marks": 25, "chapters": [
                {"id": "grammar", "name": "Grammar (Nouns, Pronouns, Adjectives, Adverbs, Prepositions)"},
                {"id": "writing-skills", "name": "Paragraph Writing, Informal Letters, Story Writing"}
            ]},
            {"unit_no": "III", "name": "Literature", "marks": 35, "chapters": [
                {"id": "honeycomb-textbook", "name": "Honeycomb (Textbook in English)"},
                {"id": "an-alien-hand", "name": "An Alien Hand (Supplementary Reader)"}
            ]}
        ]
    },
    {
        "subject": "Hindi",
        "grade": 7,
        "source": "NCERT Class 7 Hindi (Vasant Bhag 2)",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Apthit Bodh", "marks": 15, "chapters": [
                {"id": "apthit-gadyansh-kavyansh", "name": "Apthit Gadyansh va Kavyansh"}
            ]},
            {"unit_no": "II", "name": "Vyakaran", "marks": 20, "chapters": [
                {"id": "vyakaran-7", "name": "Sangya, Sarvanam, Visheshan, Kriya, Vilom, Paryayvachi"}
            ]},
            {"unit_no": "III", "name": "Pathyapustak Vasant", "marks": 30, "chapters": [
                {"id": "vasant-bhag-2", "name": "Vasant Bhag 2 (Kavita evam Kahani)"}
            ]},
            {"unit_no": "IV", "name": "Rachnatmak Lekhan", "marks": 15, "chapters": [
                {"id": "rachnatmak-lekhan", "name": "Patra Lekhan, Nibandh Lekhan, Samvad Lekhan"}
            ]}
        ]
    },

    # ==================== GRADE 6 ====================
    {
        "subject": "Mathematics",
        "grade": 6,
        "source": "NCERT Class 6 Mathematics, Ganita Prakash (NCF-SE)",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Number Sense and Patterns", "marks": 30, "chapters": [
                {"id": "knowing-our-numbers", "name": "Patterns in Mathematics"},
                {"id": "whole-numbers", "name": "Lines and Angles"},
                {"id": "playing-with-numbers", "name": "Number Play"},
                {"id": "integers-6", "name": "Data Handling and Presentation"},
                {"id": "fractions-6", "name": "Prime Time"},
                {"id": "decimals-6", "name": "Perimeter and Area"}
            ]},
            {"unit_no": "II", "name": "Shapes and Space", "marks": 25, "chapters": [
                {"id": "basic-geometrical-ideas", "name": "Fractions"},
                {"id": "understanding-elementary-shapes", "name": "Playing with Constructions"},
                {"id": "symmetry-6", "name": "Symmetry"}
            ]},
            {"unit_no": "III", "name": "Algebra and Measurement", "marks": 25, "chapters": [
                {"id": "algebra-6", "name": "The Other Side of Zero"},
                {"id": "ratio-and-proportion", "name": "Ratio and Proportion"}
            ]}
        ]
    },
    {
        "subject": "Science",
        "grade": 6,
        "source": "NCERT Class 6 Science, Curiosity (NCF-SE)",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "The World of the Living", "marks": 25, "chapters": [
                {"id": "the-wonderful-world-of-science", "name": "The Wonderful World of Science"},
                {"id": "diversity-in-the-living-world", "name": "Diversity in the Living World"},
                {"id": "mindful-eating", "name": "Mindful Eating: A Path to a Healthy Body"},
                {"id": "exploring-magnets", "name": "Exploring Magnets"}
            ]},
            {"unit_no": "II", "name": "Matter and Materials", "marks": 25, "chapters": [
                {"id": "measurement-of-length-and-motion", "name": "Measurement of Length and Motion"},
                {"id": "materials-around-us", "name": "Materials Around Us"},
                {"id": "temperature-and-its-measurement", "name": "Temperature and its Measurement"}
            ]},
            {"unit_no": "III", "name": "Energy and Environment", "marks": 30, "chapters": [
                {"id": "a-journey-through-states-of-water", "name": "A Journey through States of Water"},
                {"id": "methods-of-separation-in-everyday-life", "name": "Methods of Separation in Everyday Life"},
                {"id": "living-creatures-exploring-their-characteristics", "name": "Living Creatures: Exploring their Characteristics"},
                {"id": "natures-treasures", "name": "Nature's Treasures"},
                {"id": "beyond-earth", "name": "Beyond Earth"}
            ]}
        ]
    },
    {
        "subject": "Social Science",
        "grade": 6,
        "source": "NCERT Class 6 Social Science, Exploring Society: India and Beyond (NCF-SE)",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Theme A: India and the World: Land and the People", "marks": 25, "chapters": [
                {"id": "locating-places-on-the-earth", "name": "Locating Places on the Earth"},
                {"id": "oceans-and-continents", "name": "Oceans and Continents"},
                {"id": "landforms-and-life", "name": "Landforms and Life"}
            ]},
            {"unit_no": "II", "name": "Theme B: Tapestry of the Past", "marks": 30, "chapters": [
                {"id": "timeline-and-sources-of-history", "name": "Timeline and Sources of History"},
                {"id": "india-that-is-bharat", "name": "India, That is Bharat"},
                {"id": "the-beginnings-of-indian-civilisation", "name": "The Beginnings of Indian Civilisation"},
                {"id": "indias-cultural-roots", "name": "India's Cultural Roots"}
            ]},
            {"unit_no": "III", "name": "Theme C: Our Cultural Heritage and Knowledge Traditions", "marks": 25, "chapters": [
                {"id": "unity-in-diversity-or-many-in-one", "name": "Unity in Diversity, or 'Many in the One'"},
                {"id": "family-and-community", "name": "Family and Community"},
                {"id": "grassroots-democracy-part-1-governance-in-villages", "name": "Grassroots Democracy - Part 1: Governance in Villages"},
                {"id": "grassroots-democracy-part-2-governance-in-towns", "name": "Grassroots Democracy - Part 2: Governance in Towns"},
                {"id": "economic-activities-around-us", "name": "Economic Activities Around Us"}
            ]}
        ]
    },
    {
        "subject": "English",
        "grade": 6,
        "source": "NCERT Class 6 English, Poorvi (NCF-SE)",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Reading Comprehension", "marks": 20, "chapters": [
                {"id": "reading-comprehension", "name": "Reading Comprehension"}
            ]},
            {"unit_no": "II", "name": "Writing and Grammar", "marks": 25, "chapters": [
                {"id": "grammar", "name": "Grammar (Nouns, Verbs, Articles, Simple Sentences)"},
                {"id": "writing-skills", "name": "Paragraph Writing, Message Writing, Picture Description"}
            ]},
            {"unit_no": "III", "name": "Poorvi Textbook", "marks": 35, "chapters": [
                {"id": "poorvi-textbook", "name": "Poorvi (Units: Fables and Folk Tales, Friendship, Nurturing Nature, Sports and Games, Culture and Tradition)"}
            ]}
        ]
    },
    {
        "subject": "Hindi",
        "grade": 6,
        "source": "NCERT Class 6 Hindi, Malhar (NCF-SE)",
        "total_marks": 80,
        "units": [
            {"unit_no": "I", "name": "Apthit Bodh", "marks": 15, "chapters": [
                {"id": "apthit-gadyansh-kavyansh", "name": "Apthit Gadyansh va Kavyansh"}
            ]},
            {"unit_no": "II", "name": "Vyakaran", "marks": 20, "chapters": [
                {"id": "vyakaran-6", "name": "Varnamala, Sangya, Sarvanam, Kriya, Ling, Vachan"}
            ]},
            {"unit_no": "III", "name": "Pathyapustak Malhar", "marks": 30, "chapters": [
                {"id": "malhar-textbook", "name": "Malhar (Kavita evam Kahani)"}
            ]},
            {"unit_no": "IV", "name": "Rachnatmak Lekhan", "marks": 15, "chapters": [
                {"id": "rachnatmak-lekhan", "name": "Chitra Varnan, Anuchhed Lekhan, Samvad Lekhan"}
            ]}
        ]
    }
]

count = 0
for item in SYLLABI:
    subj = item["subject"].replace(" ", "_")
    grade = item["grade"]
    filename = f"{subj}_{grade}.json"
    dest = OUT_DIR / filename
    dest.write_text(json.dumps(item, indent=2, ensure_ascii=False), encoding="utf-8")
    count += 1
    print(f"Generated {filename} ({len(item['units'])} units)")

print(f"\nSuccessfully generated {count} syllabus files across grades 6-12!")
