import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, "/tmp/pdfdeps")

from pypdf import PdfReader


PDF_PATH = Path(
    "/Users/kondrukirankumar/Documents/NEET preparation/"
    "LC Gupta, Kusum Gupta, Abhitabh Gupta - Practical Standard Prescriber "
    "(2009, Jaypee Brothers Med. Publ.) - libgen.li.pdf"
)
OUT_PATH = Path("data/diagnoses.json")

CATEGORY_MAP = {
    "GASTROINTESTINAL DISEASES": "Gastrointestinal",
    "RESPIRATORY DISEASES": "Respiratory",
    "HEART DISEASES": "Cardiology",
    "SKIN DISEASES": "Skin",
    "PSYCHIATRIC DISEASES": "Psychiatry",
    "GYNAECOLOGICAL DISORDERS": "Gynaecology",
    "EAR AND NOSE DISEASES": "ENT",
    "EYE DISORDERS": "Eye",
    "DISEASES OF CHILDREN": "Pediatrics",
    "MEDICAL EMERGENCIES": "Emergencies",
    "MISCELLANEOUS": "Miscellaneous",
    "RENAL SYSTEM": "Renal",
    "NEUROLOGICAL DISEASES": "Neurology",
    "HAEMATOLOGY": "Hematology",
    "ORAL DISEASES": "Oral",
    "DISEASES OF BONES AND JOINTS": "Bones & Joints",
}

EXCLUDED_CATEGORIES = {
    "GENERAL INFORMATION",
    "DIET THERAPY",
    "BLOOD COUNT",
    "BLOOD BIOCHEMISTRY",
    "CEREBROSPINAL FLUID",
    "GLUCOSE TOLERANCE TEST",
    "BONE MARROW ASPIRATION",
    "RENAL FUNCTION TESTS",
    "LIVER FUNCTION TESTS",
    "FUNDUS EXAMINATION",
    "APPENDIX",
}

NAME_FIXES = {
    "Diabtetes Mellitus": "Diabetes Mellitus",
    "Hypermesis Gravidarum": "Hyperemesis Gravidarum",
    "Acute Giomerulonephritis": "Acute Glomerulonephritis",
    "Acute Pyleonephritis": "Acute Pyelonephritis",
    "Bad Breath (Halithosis)": "Bad Breath (Halitosis)",
    "Goutyarthritis": "Gouty Arthritis",
    "Osteoartheritis": "Osteoarthritis",
    "Viral Penumonia": "Viral Pneumonia",
    "Sub-Acute Bacterial Endocarditis": "Subacute Bacterial Endocarditis",
}

EMERGENCY_OR_SURGICAL = {
    "Acute Cholecystitis",
    "Appendicitis",
    "Diabetic Ketoacidosis",
    "Anaphylactic Shock",
    "Acute Respiratory Failure",
    "Cardiac Arrest",
    "Cardiogenic Shock",
    "Ectopic Pregnancy",
    "Meningitis",
    "Organophosphorus Poisoning",
    "Snake Bite",
    "Tension Pneumothorax",
}

MODERN_UPDATES = {
    "Achalasia Cardia": [
        "Current update: confirm with endoscopy, barium swallow and high-resolution manometry when available.",
        "Current update: definitive options are pneumatic dilation, laparoscopic Heller myotomy with fundoplication, or POEM; medicines such as nitrates/calcium-channel blockers are temporary options when procedures are unsuitable.",
    ],
    "Acute Cholecystitis": [
        "Current update: admit, give IV fluids, analgesia and antibiotics, and arrange early laparoscopic cholecystectomy when fit, ideally within 1 week of diagnosis.",
    ],
    "Acute Gastritis": [
        "Current update: stop NSAIDs/alcohol/irritants where possible; use a proton pump inhibitor when acid suppression is needed; test/treat H. pylori when ulcer disease or recurrent dyspepsia is suspected.",
    ],
    "Amoebiasis": [
        "Current update: symptomatic invasive disease usually needs a nitroimidazole followed by a luminal agent such as paromomycin, iodoquinol or diloxanide where available.",
    ],
    "Congenital Syphilis": [
        "Current update: evaluate mother and infant serology, clinical findings, CSF/CBC/long-bone radiographs as indicated, and manage with pediatric/infectious disease specialist input.",
        "Current update: CDC regimens for confirmed/highly probable neonatal congenital syphilis use aqueous crystalline penicillin G 50,000 units/kg/dose IV every 12 hours during the first 7 days of life and every 8 hours thereafter for a total of 10 days, or procaine penicillin G 50,000 units/kg IM daily for 10 days.",
    ],
    "Appendicitis": [
        "Current update: urgent surgical evaluation is standard; appendectomy remains usual treatment, with IV fluids and antibiotics. Antibiotics alone are reserved for selected uncomplicated cases after surgical review.",
    ],
    "Bronchial Asthma": [
        "Current update: adults and adolescents should receive ICS-containing therapy; avoid SABA-only treatment. Preferred reliever/controller pathways use low-dose ICS-formoterol where available.",
    ],
    "Hypertension": [
        "Current update: confirm with repeated clinic BP and preferably ABPM/HBPM; first-line drug choice is guided by age, diabetes, ethnicity, CKD, heart failure and pregnancy status. Avoid sublingual nifedipine for hypertensive emergencies.",
    ],
    "Diabetes Mellitus": [
        "Current update: use HbA1c/plasma glucose for diagnosis and monitoring. Metformin remains common first-line when tolerated and renal function allows; SGLT2 inhibitors or GLP-1 receptor agonists are prioritized when cardiorenal or weight benefit is needed.",
    ],
    "Diabetic Ketoacidosis": [
        "Current update: DKA requires monitored admission with protocolized fluids, insulin and potassium. Bicarbonate is reserved for severe acidosis rather than routine use at pH 7.2.",
    ],
    "Anaphylactic Shock": [
        "Current update: first-line treatment is adrenaline 1 mg/mL (1:1000) IM into the mid-outer thigh, 0.3-0.5 mg in adults, repeated every 5-15 minutes if needed; antihistamines and steroids are adjuncts only.",
    ],
}

ALT_HEADINGS = {
    "Primary Biliary Cirrhosis": ["Primary Billiary Cirrhosis"],
    "Acute Leukemia": ["Acute Leukaemia"],
    "Chronic Lymphatic Leukemia": ["Chronic Lymphatic Leukaemia"],
    "Chronic Myeloid Leukemia": ["Chronic Myeloid Leukaemia"],
    "Hyperkalemia": ["Hyperkalaemia"],
}

MANUAL_TOC_ENTRIES = [
    {
        "number": 206,
        "diagnosis": "Spontaneous Pneumothorax",
        "category": "Emergencies",
        "include": True,
        "bookPage": 249,
        "pdfPage": "277",
    },
    {
        "number": 267,
        "diagnosis": "Bell’s Palsy",
        "category": "Neurology",
        "include": True,
        "bookPage": 432,
        "pdfPage": "460",
    },
    {
        "number": 293,
        "diagnosis": "Hodgkin’s Disease",
        "category": "Hematology",
        "include": True,
        "bookPage": 456,
        "pdfPage": "484",
    },
    {
        "number": 304,
        "diagnosis": "Ankylosing Spondylitis",
        "category": "Bones & Joints",
        "include": True,
        "bookPage": 467,
        "pdfPage": "495",
    },
]


CURATED_PRESCRIPTIONS = {
    "Achalasia Cardia": """Rx
1. Urgent gastroenterology referral for confirmation and definitive therapy
   Dose:
   Route:
   Frequency:
   Duration:
   Instructions: Soft diet, small frequent meals, eat upright, avoid lying down for 2-3 hours after meals.

Advice:
- Avoid alcohol, spicy irritants, salicylates/NSAIDs where possible, gulping food and unchewed food.

Follow-up:
- Gastroenterology/surgical review for pneumatic dilation, Heller myotomy or POEM.

Red flags:
- Progressive dysphagia with weight loss
- Aspiration, cough with fever, or inability to swallow liquids""",
    "Acute Cholecystitis": """Rx
1. Urgent referral/admission advised
   Dose:
   Route:
   Frequency:
   Duration:
   Instructions: Keep nil orally; arrange IV fluids, analgesia, antibiotics and surgical review.

Advice:
- Ultrasound abdomen, CBC, LFT, bilirubin, renal function and electrolytes.
- Early laparoscopic cholecystectomy when fit.

Follow-up:
- Same-day surgical admission.

Red flags:
- Peritonitis
- Sepsis or hypotension
- Jaundice or suspected cholangitis""",
    "Appendicitis": """Rx
1. Urgent referral/admission advised
   Dose:
   Route:
   Frequency:
   Duration:
   Instructions: Keep nil orally; arrange IV fluids, analgesia, antibiotics and surgical review.

Advice:
- CBC, renal function/electrolytes, urine test and pregnancy test where relevant.

Follow-up:
- Same-day surgical assessment.

Red flags:
- Generalized peritonitis
- Sepsis
- Appendicular mass or abscess""",
    "Acute Gastritis": """Rx
1. Omeprazole 20 mg capsule
   Dose: 1 capsule
   Route: Oral
   Frequency: Once daily before breakfast
   Duration: 14 days
   Instructions: Avoid NSAIDs, alcohol and known food triggers.

2. Antacid/alginate suspension
   Dose: 10-15 mL
   Route: Oral
   Frequency: After meals and at bedtime if needed
   Duration: 5-7 days
   Instructions:

Advice:
- Bland soft diet and hydration.
- Test/treat H. pylori if ulcer disease or recurrent dyspepsia is suspected.

Follow-up:
- Review if pain, vomiting or dyspepsia persists.

Red flags:
- Haematemesis or melaena
- Persistent vomiting
- Weight loss or anaemia""",
    "Amoebiasis": """Rx
1. Metronidazole tablet
   Dose: Adult 400-800 mg
   Route: Oral
   Frequency: Three times daily
   Duration: 5-10 days
   Instructions: Avoid alcohol.

2. Luminal amoebicide such as paromomycin, iodoquinol or diloxanide where available
   Dose: Use local formulary dose
   Route: Oral
   Frequency:
   Duration:
   Instructions: Give after nitroimidazole course to reduce relapse.

Advice:
- ORS and hydration.
- Avoid antimotility drugs if fever, blood in stool or toxic colitis.

Follow-up:
- Review stool result/clinical response.

Red flags:
- Dehydration
- Severe abdominal tenderness
- Suspected liver abscess""",
    "Bronchial Asthma": """Rx
1. Budesonide-formoterol 200/6 mcg inhaler
   Dose: 1 inhalation when symptomatic
   Route: Inhaled
   Frequency: As reliever, within product/local maximum
   Duration: Ongoing
   Instructions: Check inhaler technique; rinse mouth if used regularly.

2. If persistent symptoms: maintenance ICS-formoterol
   Dose: As per severity/local protocol
   Route: Inhaled
   Frequency:
   Duration:
   Instructions:

Advice:
- Avoid triggers and smoking.
- Check peak flow/spirometry where available.

Follow-up:
- Review control and inhaler technique in 2-6 weeks, earlier after exacerbation.

Red flags:
- Unable to speak full sentences
- Silent chest
- Cyanosis or exhaustion""",
    "Congenital Syphilis": """Rx
1. Urgent pediatric/infectious disease referral advised
2. Aqueous crystalline penicillin G 50,000 units/kg/dose IV every 12 hours during first 7 days of life, then every 8 hours thereafter for total 10 days
3. Alternative where appropriate: procaine penicillin G 50,000 units/kg IM once daily for 10 days

Advice:
- Document maternal serology/treatment and compare maternal and neonatal RPR/VDRL titers
- Evaluate with CBC, CSF and long-bone radiographs when indicated

Follow-up:
- Serial serologic follow-up until nontreponemal test becomes nonreactive or appropriately declines

Red flags:
- Fever, wasting or poor feeding
- Hepatosplenomegaly
- Rash, snuffles, bone tenderness or neurologic signs""",
    "Hypertension": """Rx
1. Amlodipine 5 mg tablet
   Dose: 1 tablet
   Route: Oral
   Frequency: Once daily
   Duration: 30 days
   Instructions: Monitor BP; watch for ankle swelling/flushing.

2. Alternative when clinically suitable: ACE inhibitor or ARB
   Dose: As per selected drug and renal function
   Route: Oral
   Frequency:
   Duration:
   Instructions: Check creatinine/eGFR and potassium; avoid ACE inhibitor/ARB in pregnancy.

Advice:
- Low-salt diet, weight reduction, exercise, tobacco cessation and alcohol moderation.
- Check urine ACR/dipstick, creatinine/eGFR, potassium, glucose/HbA1c, lipids and ECG.

Follow-up:
- Review BP log and titrate therapy.

Red flags:
- Chest pain
- Neurologic deficit
- Pulmonary oedema
- Pregnancy with high BP""",
    "Diabetes Mellitus": """Rx
1. Metformin XR 500 mg tablet
   Dose: 1 tablet
   Route: Oral
   Frequency: Once daily with evening meal
   Duration: 2 weeks, then titrate
   Instructions: Check eGFR; titrate gradually to reduce GI intolerance.

2. Consider SGLT2 inhibitor or GLP-1 receptor agonist when ASCVD, heart failure, CKD or weight benefit is a priority
   Dose: As per selected drug/local formulary
   Route:
   Frequency:
   Duration:
   Instructions:

Advice:
- Individualized diet, exercise, weight management and foot care.
- Check HbA1c, fasting/PP glucose, creatinine/eGFR, urine ACR, lipids, BP, eye and foot exam.

Follow-up:
- Review glucose record and HbA1c plan.

Red flags:
- Ketones or DKA symptoms
- Severe hyperglycaemia with dehydration
- Foot ulcer or infection""",
    "Diabetic Ketoacidosis": """Rx
1. Urgent referral/admission advised
   Dose:
   Route:
   Frequency:
   Duration:
   Instructions: Start monitored DKA protocol with fluids, insulin and potassium after urgent assessment.

Advice:
- Check bedside glucose/ketones, venous blood gas, electrolytes, renal function, ECG and precipitating cause.

Follow-up:
- Emergency admission/monitored care.

Red flags:
- Altered sensorium
- Shock
- Severe acidosis
- Potassium abnormality""",
    "Anaphylactic Shock": """Rx
1. Adrenaline 1 mg/mL (1:1000)
   Dose: Adult 0.3-0.5 mg
   Route: IM, mid-outer thigh
   Frequency: Repeat every 5-15 minutes if needed
   Duration: Emergency doses as clinically required
   Instructions: Do not delay adrenaline for antihistamine or steroid.

Advice:
- High-flow oxygen, IV fluids for hypotension, airway support and trigger removal.

Follow-up:
- Emergency observation/admission and allergy follow-up after stabilization.

Red flags:
- Airway swelling
- Wheeze or stridor
- Hypotension or syncope
- Recurrent symptoms""",
}

CURATED_PRESCRIPTIONS = {
    "Achalasia Cardia": """Rx
1. Gastroenterology referral for confirmation and definitive therapy
2. Soft diet, small frequent meals, eat upright, avoid lying down for 2-3 hours after meals

Advice:
- Avoid alcohol, spicy irritants, salicylates/NSAIDs where possible, gulping food and unchewed food

Follow-up:
- Gastroenterology/surgical review for pneumatic dilation, Heller myotomy or POEM

Red flags:
- Progressive dysphagia with weight loss
- Aspiration, cough with fever, or inability to swallow liquids""",
    "Acute Bronchitis": """Rx
1. Supportive care: rest, warm fluids and steam inhalation if helpful
2. Tab Paracetamol 500 mg orally every 6-8 hours if fever/pain for up to 3 days
3. Antibiotic only if systemically very unwell, high-risk, or bacterial complication suspected

Advice:
- Stop smoking and avoid fumes/dust
- Rule out pneumonia if fever, tachypnoea, tachycardia, hypoxia or focal chest signs

Follow-up:
- Review if cough worsens, fever persists, or breathlessness develops

Red flags:
- Breathlessness
- Chest pain
- Persistent high fever
- Altered sensorium""",
    "Acute Cholecystitis": """Rx
1. Urgent hospital admission and surgical review advised
2. Keep nil orally
3. Start IV fluids, analgesia and antibiotics as per hospital protocol

Advice:
- Ultrasound abdomen, CBC, LFT, bilirubin, renal function and electrolytes
- Early laparoscopic cholecystectomy when fit

Follow-up:
- Same-day surgical admission

Red flags:
- Peritonitis
- Sepsis or hypotension
- Jaundice or suspected cholangitis""",
    "Acute Gastritis": """Rx
1. Cap Omeprazole 20 mg orally once daily before breakfast for 14 days
2. Antacid/alginate suspension 10-15 mL orally after meals and at bedtime if needed for 5-7 days

Advice:
- Bland soft diet and hydration
- Avoid NSAIDs, alcohol and known food triggers
- Test/treat H. pylori if ulcer disease or recurrent dyspepsia is suspected

Follow-up:
- Review if pain, vomiting or dyspepsia persists

Red flags:
- Haematemesis or melaena
- Persistent vomiting
- Weight loss or anaemia""",
    "Acute Glaucoma": """Rx
1. Urgent ophthalmology referral/emergency treatment advised
2. Tab Acetazolamide 500 mg orally stat, then 250 mg every 6 hours if not contraindicated
3. Timolol 0.5% eye drops, pilocarpine 2-4% eye drops, and osmotic agent as per ophthalmology/emergency protocol

Advice:
- Do not delay definitive ophthalmology care; laser peripheral iridotomy is usually required after pressure control

Follow-up:
- Emergency ophthalmology care now

Red flags:
- Severe eye pain
- Vomiting
- Halos/misty vision
- Rapid visual loss""",
    "Amoebiasis": """Rx
1. Tab Metronidazole 400-800 mg orally three times daily for 5-10 days
2. Luminal amoebicide such as paromomycin, iodoquinol or diloxanide orally after nitroimidazole course where available
3. ORS after loose stools

Advice:
- Avoid alcohol with metronidazole
- Avoid antimotility drugs if fever, blood in stool or toxic colitis

Follow-up:
- Review stool result and clinical response

Red flags:
- Dehydration
- Severe abdominal tenderness
- Suspected liver abscess""",
    "Appendicitis": """Rx
1. Urgent hospital admission and surgical review advised
2. Keep nil orally
3. Start IV fluids, analgesia and antibiotics as per emergency/surgical protocol

Advice:
- CBC, renal function/electrolytes, urine test and pregnancy test where relevant

Follow-up:
- Same-day surgical assessment

Red flags:
- Generalized peritonitis
- Sepsis
- Appendicular mass or abscess""",
    "Bronchial Asthma": """Rx
1. Budesonide-formoterol 200/6 mcg inhaler: 1 inhalation when symptomatic, within product/local maximum
2. If persistent symptoms: maintenance ICS-formoterol as per severity/local protocol

Advice:
- Check inhaler technique and avoid triggers/smoking
- Check peak flow/spirometry where available

Follow-up:
- Review control and inhaler technique in 2-6 weeks, earlier after exacerbation

Red flags:
- Unable to speak full sentences
- Silent chest
- Cyanosis or exhaustion""",
    "Congenital Syphilis": """Rx
1. Urgent pediatric/infectious disease referral advised
2. Aqueous crystalline penicillin G 50,000 units/kg/dose IV every 12 hours during first 7 days of life, then every 8 hours thereafter for total 10 days
3. Alternative where appropriate: procaine penicillin G 50,000 units/kg IM once daily for 10 days

Advice:
- Document maternal serology/treatment and compare maternal and neonatal RPR/VDRL titers
- Evaluate with CBC, CSF and long-bone radiographs when indicated

Follow-up:
- Serial serologic follow-up until nontreponemal test becomes nonreactive or appropriately declines

Red flags:
- Fever, wasting or poor feeding
- Hepatosplenomegaly
- Rash, snuffles, bone tenderness or neurologic signs""",
    "Hypertension": """Rx
1. Tab Amlodipine 5 mg orally once daily for 30 days
2. Alternative when clinically suitable: ACE inhibitor or ARB with creatinine/eGFR and potassium monitoring

Advice:
- Low-salt diet, weight reduction, exercise, tobacco cessation and alcohol moderation
- Check urine ACR/dipstick, creatinine/eGFR, potassium, glucose/HbA1c, lipids and ECG

Follow-up:
- Review BP log and titrate therapy

Red flags:
- Chest pain
- Neurologic deficit
- Pulmonary oedema
- Pregnancy with high BP""",
    "Diabetes Mellitus": """Rx
1. Tab Metformin XR 500 mg orally once daily with evening meal for 2 weeks, then titrate if tolerated
2. Consider SGLT2 inhibitor or GLP-1 receptor agonist when ASCVD, heart failure, CKD or weight benefit is a priority

Advice:
- Individualized diet, exercise, weight management and foot care
- Check HbA1c, fasting/PP glucose, creatinine/eGFR, urine ACR, lipids, BP, eye and foot exam

Follow-up:
- Review glucose record and HbA1c plan

Red flags:
- Ketones or DKA symptoms
- Severe hyperglycaemia with dehydration
- Foot ulcer or infection""",
    "Diabetic Ketoacidosis": """Rx
1. Urgent hospital admission/monitored care advised
2. Start protocolized IV fluids, insulin and potassium after urgent assessment
3. Add dextrose when glucose falls while ketosis persists, as per DKA protocol

Advice:
- Check bedside glucose/ketones, venous blood gas, electrolytes, renal function, ECG and precipitating cause

Follow-up:
- Emergency admission/monitored care

Red flags:
- Altered sensorium
- Shock
- Severe acidosis
- Potassium abnormality""",
    "Anaphylactic Shock": """Rx
1. Inj Adrenaline 1 mg/mL (1:1000) 0.3-0.5 mg IM into mid-outer thigh immediately; repeat every 5-15 minutes if needed
2. High-flow oxygen and IV fluids for hypotension
3. Antihistamine/corticosteroid only as adjunct after adrenaline

Advice:
- Remove trigger and support airway/breathing/circulation

Follow-up:
- Emergency observation/admission and allergy follow-up after stabilization

Red flags:
- Airway swelling
- Wheeze or stridor
- Hypotension or syncope
- Recurrent symptoms""",
}

SECTION_OVERRIDES = {
    ("Epistaxis", "ENT"): {
        "essentials": [
            "Nasal bleeding; examine and locate the bleeding site, especially Little's area for anterior bleeding.",
            "If blood flows down the nasopharynx, consider posterior epistaxis and the need for post-nasal packing.",
            "Search for causes after bleeding stops, including hypertension, acute exanthemata, bleeding/coagulation disorders, polyps, malignancy, leukaemia, haemangioma, telangiectasis and trauma.",
        ],
        "treatment": [
            "For bleeding from Little's area, insert cotton wool soaked with 4 per cent lignocaine and 1 in 1000 adrenaline and compress the nose for a few minutes.",
            "If bleeding recurs, seal the bleeding point with chemical or electrical cautery.",
            "For diffuse nasal mucosal bleeding, use an inflatable nasal bag or anterior nasal pack with vaseline or anti-infective impregnated gauze; antibiotic cover is essential.",
            "If blood flows into the nasopharynx, use a post-nasal pack; uncontrolled epistaxis may need arterial supply interruption.",
            "Keep the patient on bed rest, propped up, with adequate fluids and sedation/anxiolysis where appropriate.",
        ],
    },
    ("Haemothorax", "Respiratory"): {
        "essentials": [
            "Blood in the pleural sac, commonly due to trauma, tumours, tuberculosis or pulmonary infarction.",
            "Assess respiratory compromise and ongoing bleeding in suspected haemothorax.",
        ],
        "treatment": [
            "Evacuate the pleural sac early with thoracocentesis and water-seal drainage.",
            "If bleeding continues, thoracotomy is indicated.",
            "Surgical removal of retained blood clots may be necessary.",
        ],
    },
    ("Hydrothorax", "Respiratory"): {
        "essentials": [
            "Serous or transudative pleural effusion with specific gravity less than 1015 and protein less than 3 g per cent.",
            "Common associations include congestive heart failure, superior vena cava obstruction, cirrhosis and hypoproteinaemia.",
        ],
        "treatment": [
            "Thoracocentesis may be done to relieve dyspnoea.",
            "Treat the underlying cause such as heart failure, cirrhosis, vena caval obstruction or hypoproteinaemia.",
        ],
    },
    ("Tension Pneumothorax", "Respiratory"): {
        "essentials": [
            "Medical emergency due to tension pneumothorax.",
            "Requires immediate decompression when clinically suspected.",
        ],
        "treatment": [
            "Introduce a trocar into the second intercostal space anteriorly to relieve tension.",
            "After tension is relieved, introduce a Foley catheter into the pleural space and attach to a water trap.",
            "A suction pump up to a maximum vacuum of 30 cm water may be attached when needed.",
        ],
    },
    ("Traumatic Pneumothorax", "Respiratory"): {
        "essentials": [
            "Emergency pneumothorax following chest trauma.",
            "Open chest or sucking wounds require immediate attention.",
            "May also occur from lung puncture or laceration.",
        ],
        "treatment": [
            "Make open chest wounds airtight immediately by any available means such as bandage or handkerchief.",
            "Close the chest wound surgically as soon as possible.",
            "Traumatic pneumothorax due to lung puncture or laceration is managed as spontaneous pneumothorax.",
        ],
    },
    ("Poisoning", "Emergencies"): {
        "essentials": [
            "Suspected or confirmed exposure to poison; identify substance, amount, time and route where possible.",
            "Assess airway, breathing, circulation, consciousness and vital functions immediately.",
            "Document medico-legal details and preserve relevant samples when indicated.",
        ],
        "treatment": [
            "Remove unabsorbed poison when appropriate and safe.",
            "Enhance removal of absorbed poison when indicated.",
            "Maintain vital functions and provide general supportive care.",
            "Administer a specific antidote where available and clinically indicated.",
            "Give symptomatic treatment and complete medico-legal responsibilities.",
        ],
    },
    ("Heart Disease", "Cardiology"): {
        "essentials": [
            "Common manifestations include dyspnoea, fatigue, chest pain, palpitation and oedema.",
            "Paroxysmal nocturnal dyspnoea may suggest left ventricular failure or tight mitral stenosis.",
            "Age and risk pattern help orient diagnosis: congenital disease is common under 15 years, while coronary disease and hypertension are more likely later.",
        ],
        "treatment": [
            "Classify the cardiac syndrome and manage under the specific diagnosis such as angina, hypertension, heart failure, rheumatic disease or congenital heart disease.",
            "Evaluate symptoms with clinical examination, blood pressure, ECG and further investigations as indicated.",
            "Urgent referral is needed for acute chest pain, pulmonary oedema, syncope, severe dyspnoea or shock.",
        ],
    },
    ("Chronic Simple Otitis Media", "ENT"): {
        "essentials": [
            "Gradually increasing deafness with recurrent ear discharge and occasional earache.",
            "Central tympanic membrane perforation may expose the promontory, round and oval windows or eustachian tube opening.",
            "Audiogram shows conductive deafness; X-ray mastoid may show pneumatic mastoid and X-ray PNS may show sinusitis or DNS.",
        ],
        "treatment": [
            "Aural toilet if discharge is present and protective dressing such as silicone ear drops.",
            "Control infection of paranasal sinuses, nose and throat.",
            "Give a proper full antibiotic course for residual middle-ear infection; the textbook mentions ciprofloxacin 500 mg twice daily for 5 days.",
            "Tympanoplasty and reconstruction of the ossicular chain may be required.",
            "Advise no head bath, plug ears during bathing, use prophylactic decongestant nasal drops, and use ear drops such as nebasulf, chloromycetin or gentamicin 3-5 drops three times daily until dry.",
        ],
    },
    ("Common Headache", "Neurology"): {
        "essentials": [
            "Migraine is typically throbbing, unilateral, sporadic and lasts about 6-40 hours, often with nausea or vomiting.",
            "Cluster headache is typically boring, unilateral, sporadic and lasts about 2-3 hours.",
            "Psychogenic headache is often dull, diffuse and frequent, with depression noted in the textbook table.",
        ],
        "treatment": [
            "Identify the headache type and manage under the relevant diagnosis such as migraine, cluster headache or tension/psychogenic headache.",
            "Assess for red flags before symptomatic treatment, especially sudden severe onset, neurologic deficit, fever, meningism, papilloedema or trauma.",
            "Use simple analgesia only when appropriate and avoid repeated unsupervised analgesic use.",
        ],
    },
    ("Broadman’s Areas of Brain", "Neurology"): {
        "essentials": [
            "Occipital lobe areas 17, 18 and 19 correspond to visual cortex and visual association areas.",
            "Parietal lobe areas 3, 1, 2, 5 and 7 relate to principal sensory and sensory association areas.",
            "Frontal lobe areas 4, 6, 8 and 44 relate to principal motor area, extrapyramidal circuit, eye movement and motor speech area.",
        ],
        "treatment": [
            "Reference topic for neurological localization; no drug prescription is required.",
            "Use the cortical area map to correlate symptoms, examination findings and imaging.",
        ],
    },
    ("Transfusion Reactions", "Emergencies"): {
        "essentials": [
            "Allergic reactions may present with urticaria, sore throat, joint pain, fever, angioneurotic oedema or lymphadenopathy.",
            "Febrile reactions may occur 1-24 hours after transfusion with chills, fever, headache, nausea and vomiting.",
            "Stop and assess the transfusion reaction promptly, and exclude severe haemolytic or septic reaction clinically.",
        ],
        "treatment": [
            "Stop transfusion and maintain IV access while assessing the patient.",
            "For allergic reaction, the textbook mentions Inj Avil 2 cc stat IV.",
            "Corticosteroid options mentioned are Inj Decadron 2 cc stat IV or Inj Efcorlin 100-200 mg IV stat.",
            "For febrile reaction, give symptomatic treatment and investigate the cause; the textbook mentions penicillin for throat infection.",
        ],
    },
    ("Rectal Polyp", "Gastrointestinal"): {
        "essentials": [
            "Painless rectal bleeding in a child.",
            "Consider rectal polyp when bleeding is recurrent without major pain.",
        ],
        "treatment": [
            "Simple polypectomy by avulsion.",
            "Refer for surgical/endoscopic assessment and histopathology where appropriate.",
        ],
    },
    ("Secondary Otitis Media", "ENT"): {
        "essentials": [
            "Common cause of deafness in childhood due to obstruction of the eustachian tube.",
            "Deafness occurs without pain, though there may be dullness of the ear.",
            "Tuning fork tests and audiometry may show conductive deafness; there is no ear discharge.",
            "Symptoms of enlarged adenoids or chronic sinusitis may be present.",
        ],
        "treatment": [
            "Assess and treat the cause of eustachian tube obstruction, especially adenoids or chronic sinusitis.",
            "Confirm conductive deafness with tuning fork tests and audiometry where available.",
            "ENT referral is appropriate for persistent childhood deafness or suspected adenoidal disease.",
        ],
    },
    ("Diseases of Nose", "ENT"): {
        "essentials": [
            "Nasal obstruction may cause nasal voice, mouth breathing, crowding of teeth, high arched palate and nasal deformity when childhood obstruction persists.",
            "Nasal discharge may be mucopus, mucus, blood or CSF in cribriform plate fracture.",
            "Sneezing suggests allergic rhinitis; loss of smell, headache or facial discomfort may suggest sinus disease or osteomyelitis.",
        ],
        "treatment": [
            "Use the symptom pattern to identify the specific nasal diagnosis such as allergic rhinitis, sinusitis, septal deviation, epistaxis or CSF leak.",
            "Investigate blood-stained discharge, suspected CSF leak, persistent obstruction or facial pain urgently as indicated.",
            "Treat under the specific diagnosis and refer to ENT for persistent obstruction, recurrent bleeding, suspected malignancy or CSF leak.",
        ],
    },
    ("Ear Diseases", "ENT"): {
        "essentials": [
            "Ear pain may be due to otitis media, boil or impacted wax, or referred from tongue, tonsil or molar tooth.",
            "Watery discharge suggests diffuse otitis externa; purulent discharge may come from a canal boil.",
            "Mucopurulent discharge suggests middle-ear disease; foul smell suggests cholesteatoma or marginal granulations.",
            "Blood-stained discharge may occur with aural polyp or acute otitis media with bleeding into the middle ear.",
        ],
        "treatment": [
            "Examine the ear and manage according to the specific cause such as wax, otitis externa, otitis media, cholesteatoma or referred pain.",
            "Foul-smelling or blood-stained discharge, persistent deafness, facial weakness, vertigo or suspected cholesteatoma needs ENT review.",
            "Tinnitus requires ear and upper respiratory tract assessment and evaluation for otosclerosis or chronic otitis media when suspected.",
        ],
    },
    ("Hiccup", "Gastrointestinal"): {
        "essentials": [
            "Usually transient and may occur with neuroses, CNS disorders or gastrointestinal disorders.",
            "May be the only symptom of peptic oesophagitis.",
        ],
        "treatment": [
            "Slow deep breathing.",
            "The textbook mentions Neooctinum 30 drops in water every 4 hours or Neooctinum dragees 1 three times daily.",
            "The textbook mentions Tab Valium 2 mg three times daily; if no response, chlorpromazine 25 mg IM or 50 mg orally.",
            "Antispasmodic treatment mentioned is atropine sulphate 0.3-0.6 mg subcutaneously.",
            "Antacids such as Gelucil/Digene after each meal; persistent cases may need gastric lavage with ice-cold saline or 1 per cent sodium bicarbonate solution.",
        ],
    },
    ("Dumping Syndrome (Post-Gastrectomy Syndrome)", "Gastrointestinal"): {
        "essentials": [
            "Symptoms occur within about 20 minutes of a meal after gastrectomy.",
            "Features include sweating, tachycardia, pallor, abdominal cramps and weakness.",
            "Severe cases may have syncope.",
        ],
        "treatment": [
            "Frequent small feeds with high protein, moderately high fat and low carbohydrate.",
            "Take fluids between meals, not soon after meals.",
            "Sedatives and anticholinergics are mentioned in the textbook.",
        ],
    },
    ("Acute Morphine Poisoning", "Emergencies"): {
        "essentials": [
            "Suspect opioid poisoning with respiratory depression and pupillary constriction.",
            "Assess cyanosis, aspiration risk, blood pressure and level of consciousness.",
            "Preserve first stomach wash sample for chemical examination when medico-legally indicated.",
        ],
        "treatment": [
            "Support airway and breathing; give oxygen if cyanosis is present and position the patient to reduce aspiration risk.",
            "Naloxone 0.4-1.2 mg IV may be repeated if respiratory depression and pupillary constriction are not reversed within 1-2 minutes.",
            "The textbook mentions stomach wash first with plain water for chemical examination, then with 0.2 per cent potassium permanganate.",
            "Treat shock with IV 5 per cent glucose with noradrenaline if blood pressure is very low.",
        ],
    },
    ("Delaying Menstruation", "Gynaecology"): {
        "essentials": [
            "Menstruation may be delayed for unavoidable circumstances such as examinations or sports competition.",
            "Exclude pregnancy and contraindications to hormonal therapy before prescribing.",
        ],
        "treatment": [
            "The textbook mentions Primulor-N one tablet three times daily.",
            "Another option mentioned is Primovlar or any oral contraceptive once daily at bedtime.",
            "The textbook also mentions Tab Orgametril 2 tablets daily until bleeding is desired, with first dose not later than day 22.",
        ],
    },
}

CURATED_PRESCRIPTIONS.update(
    {
        "Epistaxis": """Rx
1. Pinch soft part of nose and keep patient sitting forward while bleeding site is assessed
2. Cotton wool soaked with 4% lignocaine and 1:1000 adrenaline for anterior Little's area bleeding, followed by compression
3. If recurrent or persistent: cautery, anterior nasal pack or post-nasal pack as indicated; antibiotic cover if packed

Advice:
- Bed rest in propped-up position and adequate fluids
- Check blood pressure and look for local/systemic cause after bleeding stops

Follow-up:
- ENT review if recurrent, posterior, severe or uncontrolled bleeding

Red flags:
- Posterior bleed or blood flowing into throat
- Shock, syncope or heavy ongoing bleeding
- Bleeding disorder or anticoagulant use""",
        "Tension Pneumothorax": """Rx
1. Emergency decompression/admission advised immediately
2. Needle/trocar decompression in second intercostal space anteriorly followed by pleural catheter/water trap drainage as per emergency protocol
3. Oxygen and cardiorespiratory monitoring

Advice:
- Do not delay decompression for imaging if clinically unstable

Follow-up:
- Emergency/ICU or surgical care now

Red flags:
- Severe breathlessness
- Hypotension or shock
- Cyanosis or tracheal deviation""",
        "Traumatic Pneumothorax": """Rx
1. Emergency admission and surgical review advised
2. Seal open sucking chest wound immediately with an airtight dressing
3. Manage lung puncture/laceration pneumothorax as spontaneous pneumothorax with chest drainage when indicated

Advice:
- Oxygen, analgesia and trauma evaluation

Follow-up:
- Same-day emergency/surgical care

Red flags:
- Open chest wound
- Respiratory distress
- Shock or major trauma""",
        "Haemothorax": """Rx
1. Urgent hospital admission and chest drainage/surgical review advised
2. Thoracocentesis and water-seal drainage as indicated
3. Thoracotomy if bleeding continues

Advice:
- Monitor vitals, oxygenation and blood loss; arrange imaging and cross-match as needed

Follow-up:
- Emergency/surgical care

Red flags:
- Shock
- Severe breathlessness
- Ongoing bleeding""",
        "Hydrothorax": """Rx
1. Treat underlying cause such as heart failure, cirrhosis, SVC obstruction or hypoproteinaemia
2. Thoracocentesis if dyspnoea is significant or diagnostic sampling is needed

Advice:
- Evaluate pleural fluid and systemic cause

Follow-up:
- Review after cause-directed treatment or earlier if breathlessness worsens

Red flags:
- Severe breathlessness
- Hypoxia
- Fever or suspected infected effusion""",
        "Poisoning": """Rx
1. Emergency assessment of airway, breathing, circulation and consciousness
2. Remove unabsorbed poison only when safe and appropriate
3. Give specific antidote if indicated and provide supportive/symptomatic care

Advice:
- Identify substance, dose, timing and route; preserve samples when medico-legally needed

Follow-up:
- Emergency observation/admission as clinically indicated

Red flags:
- Altered sensorium
- Respiratory depression
- Shock, seizures or arrhythmia""",
        "Chronic Simple Otitis Media": """Rx
1. Aural toilet and protective dressing if ear discharge is present
2. Ciprofloxacin 500 mg orally twice daily for 5 days if bacterial middle-ear infection is clinically appropriate
3. Ear drops such as nebasulf/chloromycetin/gentamicin 3-5 drops three times daily until ear is dry, if suitable after otoscopic assessment

Advice:
- Keep ear dry; plug ear during bathing and avoid head bath
- Treat associated nose, throat or sinus infection

Follow-up:
- ENT review for tympanoplasty/ossicular reconstruction if persistent perforation or conductive deafness

Red flags:
- Facial weakness
- Vertigo
- Foul-smelling discharge or suspected cholesteatoma""",
        "Transfusion Reactions": """Rx
1. Stop transfusion immediately and keep IV line open with normal saline
2. For allergic reaction: Inj Avil 2 cc IV stat as mentioned in textbook
3. Corticosteroid such as Inj Decadron 2 cc IV stat or hydrocortisone 100-200 mg IV stat if clinically indicated

Advice:
- Check vitals, clerical match, urine, blood sample and transfusion bag as per transfusion reaction protocol

Follow-up:
- Observe/admit depending on severity

Red flags:
- Hypotension
- Dyspnoea or wheeze
- Fever with rigors
- Haemoglobinuria or back pain""",
        "Rectal Polyp": """Rx
1. Surgical/endoscopic referral for simple polypectomy by avulsion

Advice:
- Assess recurrent painless rectal bleeding and send removed polyp for histopathology where available

Follow-up:
- Review after polypectomy or earlier if bleeding is heavy

Red flags:
- Heavy rectal bleeding
- Anaemia
- Weight loss or persistent symptoms""",
        "Secondary Otitis Media": """Rx
1. ENT evaluation for conductive deafness in childhood
2. Treat adenoids, chronic sinusitis or other cause of eustachian tube obstruction

Advice:
- Confirm with tuning fork tests/audiometry when available

Follow-up:
- ENT follow-up if deafness persists

Red flags:
- Persistent childhood hearing loss
- Speech delay
- Ear pain, fever or discharge""",
        "Hiccup": """Rx
1. Slow deep breathing
2. Treat suspected peptic oesophagitis or gastrointestinal trigger
3. Chlorpromazine may be considered for persistent troublesome hiccup where appropriate

Advice:
- Review medicines, CNS symptoms and gastrointestinal symptoms if hiccup persists

Follow-up:
- Review if persistent or recurrent

Red flags:
- Neurologic symptoms
- Chest pain or breathlessness
- Persistent vomiting or dehydration""",
        "Dumping Syndrome (Post-Gastrectomy Syndrome)": """Rx
1. Frequent small meals with high protein, moderately high fat and low carbohydrate
2. Take fluids between meals, not soon after meals

Advice:
- Avoid large carbohydrate-heavy meals
- Sit or lie down if presyncopal symptoms occur

Follow-up:
- Review nutritional status and symptoms after dietary change

Red flags:
- Syncope
- Weight loss or dehydration
- Persistent severe post-meal symptoms""",
        "Acute Morphine Poisoning": """Rx
1. Emergency admission and airway/ventilation support
2. Inj Naloxone 0.4-1.2 mg IV; repeat if respiratory depression and miosis persist after 1-2 minutes
3. Oxygen if cyanosed and position to reduce aspiration risk

Advice:
- Preserve first gastric lavage sample for chemical examination when indicated
- Treat shock and monitor respiration closely

Follow-up:
- Emergency monitored care

Red flags:
- Respiratory depression
- Cyanosis
- Coma or shock""",
    }
)


def clean_name(name):
    name = re.sub(r"\s+", " ", name).strip(" .")
    return NAME_FIXES.get(name, name)


def slugify(value):
    folded = unicodedata.normalize("NFKD", value)
    folded = "".join(part for part in folded if not unicodedata.combining(part))
    slug = re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")
    return slug or "topic"


def parse_contents(reader):
    entries = []
    current_category = None
    pending = None

    for page_index in range(13, 28):
        text = reader.pages[page_index].extract_text() or ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            normalized = re.sub(r"\s+", " ", line)
            if re.search(r"Practical Standard Prescriber|Contents|^x{1,3}v?i*", normalized, re.I):
                continue
            if normalized.isupper() and not re.match(r"^\d+\s*\.", normalized):
                current_category = normalized
                pending = None
                continue

            split_number = re.match(r"^(\d+)$", normalized)
            match = re.match(r"^(\d+)\s*\.\s*(.*)$", normalized)
            if split_number:
                if pending:
                    entries.append(pending)
                pending = {
                    "number": int(split_number.group(1)),
                    "category": current_category,
                    "parts": [],
                    "bookPage": None,
                }
            elif match:
                if pending:
                    entries.append(pending)
                pending = {
                    "number": int(match.group(1)),
                    "category": current_category,
                    "parts": [match.group(2)],
                    "bookPage": None,
                }
            elif pending:
                pending["parts"].append(normalized)

            if pending:
                joined = " ".join(pending["parts"])
                page_match = re.search(r"(.+?)(?:\s*\.{2,}|\s+)(\d+)\s*$", joined)
                if page_match:
                    pending["name"] = clean_name(page_match.group(1))
                    pending["bookPage"] = int(page_match.group(2))
                    entries.append(pending)
                    pending = None

    if pending and pending.get("parts"):
        pending["name"] = clean_name(" ".join(pending["parts"]))
        entries.append(pending)

    output = []
    for entry in entries:
        category = entry.get("category") or "MISCELLANEOUS"
        name = clean_name(entry.get("name", ""))
        if not name:
            continue
        book_page = entry.get("bookPage")
        output.append(
            {
                "number": entry["number"],
                "id": f"{entry['number']}-{slugify(name)}",
                "diagnosis": name,
                "category": CATEGORY_MAP.get(category, "Miscellaneous"),
                "include": category not in EXCLUDED_CATEGORIES,
                "bookPage": book_page,
                "pdfPage": str(book_page + 28) if book_page else "",
            }
        )
    existing_numbers = {entry["number"] for entry in output}
    for entry in MANUAL_TOC_ENTRIES:
        if entry["number"] not in existing_numbers:
            item = dict(entry)
            item["id"] = f"{item['number']}-{slugify(item['diagnosis'])}"
            output.append(item)
    return sorted(output, key=lambda item: item["number"])


def compact_with_map(text):
    compact = []
    mapping = []
    for index, char in enumerate(text):
        folded = unicodedata.normalize("NFKD", char)
        folded = "".join(part for part in folded if not unicodedata.combining(part))
        for part in folded:
            if part.isalnum():
                compact.append(part.lower())
                mapping.append(index)
    return "".join(compact), mapping


def compact(value):
    folded = unicodedata.normalize("NFKD", value)
    folded = "".join(part for part in folded if not unicodedata.combining(part))
    return "".join(char.lower() for char in folded if char.isalnum())


def normalize_raw_text(text):
    text = re.sub(r"([A-Za-z])-\s*\n\s*([a-z])", r"\1\2", text)
    text = text.replace("\u00ad", "")
    text = text.replace("×", "x")
    text = text.replace("½", "1/2")
    return text


def strip_noise(text):
    text = normalize_raw_text(text)
    cleaned = []
    category_words = tuple(CATEGORY_MAP.keys())
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        if line.startswith("[[PDFPAGE"):
            continue
        if "Practical Standard Prescriber" in line:
            continue
        upper_line = line.upper()
        if any(upper_line == word or upper_line.startswith(word) for word in category_words):
            continue
        if re.match(r"^[A-Z][A-Za-z ]+\d+$", line):
            continue
        if re.match(r"^[A-Z][A-Za-z &-]+ Diseases\d+$", line):
            continue
        if re.match(r"^\d+$", line):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def split_items(lines):
    items = []
    current = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue

        bullet = re.match(r"^[•\-\u2022]\s*(.*)$", line)
        numbered = re.match(r"^\d+\.\s+(.*)$", line)
        starts_item = bool(bullet or numbered)
        value = (bullet or numbered).group(1).strip() if starts_item else line

        if starts_item:
            if current:
                items.append(current.strip())
            current = value
        elif not current:
            current = value
        elif re.match(r"^(Acute|Chronic|Surgical|Operative|Conservative|Supportive|Caution|Remember|Indications|Contraindications)\b", value):
            items.append(current.strip())
            current = value
        else:
            current += " " + value

    if current:
        items.append(current.strip())

    normalized = []
    for item in items:
        item = re.sub(r"\s+", " ", item).strip(" ;")
        item = re.sub(r"\bSources of possible\b", "Possible", item)
        item = item.replace(" .", ".")
        if item and item not in normalized:
            normalized.append(item)
    return normalized


def useful_items(items, limit=None):
    cleaned = []
    seen = set()
    skip_fragments = {
        "acute",
        "chronic",
        "essentials of diagnosis",
        "treatment",
        "management",
        "general measures",
        "surgical",
        "operative",
        "conservative",
    }
    for item in items:
        item = re.sub(r"\s+", " ", item).strip(" .;:")
        if not item:
            continue
        if item.lower() in skip_fragments:
            continue
        if len(item) < 18:
            continue
        if len(item.split()) < 3:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item + ("" if item.endswith((".", ":", ";")) else "."))
        if limit and len(cleaned) >= limit:
            break
    return cleaned


def clip_at_word(text, max_chars=180):
    text = re.sub(r"\s+", " ", text).strip(" .;:")
    if len(text) <= max_chars:
        return text
    clipped = text[:max_chars]
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    clipped = clipped.rstrip(" ,;:-")
    if len(clipped) >= max_chars:
        clipped = clipped[: max_chars - 1].rstrip(" ,;:-")
    return clipped + "."


def split_long_item(item):
    item = re.sub(r"\s+", " ", item).strip(" .;:")
    leak_markers = [
        " GENERAL INFORMATION",
        " APPENDIX",
        " DEAFNESS Deafness",
        " ACUTE LEUKAEMIA",
        " ADULT RESPIRATORY DISTRESS",
        " SPONTANEOUS PNEUMOTHORAX",
        " DUMPING SYNDROME",
        " GENERAL INFORMATION",
    ]
    for marker in leak_markers:
        position = item.find(marker)
        if position > 0:
            item = item[:position].strip(" .;:")

    if len(item) <= 180:
        return [item]

    parts = re.split(r"(?<=[.;:])\s+|(?:\s+[ivx]{1,4}\.\s+)|(?:\s+•\s+)|(?:\s+\s+)", item)
    output = []
    for part in parts:
        part = part.strip(" .;:")
        if not part:
            continue
        if len(part) <= 180:
            output.append(part)
            continue
        subparts = re.split(r"\s+(?:or|and then|then|plus)\s+", part, flags=re.I)
        for subpart in subparts:
            subpart = subpart.strip(" .;:")
            if subpart:
                output.append(clip_at_word(subpart))
    return output or [clip_at_word(item)]


def concise_items(items, limit, max_chars=180):
    concise = []
    seen = set()
    for item in items:
        for part in split_long_item(item):
            part = clip_at_word(part, max_chars)
            if not part.endswith((".", ":", ";")):
                part = clip_at_word(part, max_chars - 1)
            key = re.sub(r"[^a-z0-9]+", "", part.lower())
            if not key or key in seen:
                continue
            if len(part.split()) < 3:
                continue
            seen.add(key)
            concise.append(part + ("" if part.endswith((".", ":", ";")) else "."))
            if len(concise) >= limit:
                return concise
    return concise


def validate_public_summary(essentials, treatment):
    return concise_items(essentials, 6), concise_items(treatment, 8)


def split_section(cleaned_text):
    lines = cleaned_text.splitlines()
    essentials_index = None
    treatment_index = None

    for index, line in enumerate(lines):
        key = re.sub(r"[^a-z]+", "", line.lower())
        if key == "essentialsofdiagnosis" and essentials_index is None:
            essentials_index = index
        if key in {"treatment", "management"} and treatment_index is None:
            treatment_index = index

    if essentials_index is not None and treatment_index is not None and treatment_index > essentials_index:
        essentials_lines = lines[essentials_index + 1 : treatment_index]
        treatment_lines = lines[treatment_index + 1 :]
        has_essentials = True
        has_treatment = True
    elif essentials_index is not None:
        extracted = split_items(lines[essentials_index + 1 :])
        pivot = min(max(2, len(extracted) // 2), max(2, len(extracted) - 1))
        essentials_lines = extracted[:pivot]
        treatment_lines = extracted[pivot:]
        has_essentials = bool(essentials_lines)
        has_treatment = bool(treatment_lines)
    elif treatment_index is not None:
        treatment_lines = lines[treatment_index + 1 :]
        essentials_lines = lines[:treatment_index]
        has_essentials = bool(essentials_lines)
        has_treatment = True
    else:
        extracted = split_items(lines)
        pivot = min(max(2, len(extracted) // 2), max(2, len(extracted) - 1))
        essentials_lines = extracted[:pivot]
        treatment_lines = extracted[pivot:]
        has_essentials = bool(essentials_lines)
        has_treatment = bool(treatment_lines)

    essentials = useful_items(split_items(essentials_lines), limit=7)
    treatment = useful_items(split_items(treatment_lines), limit=9)
    if len(treatment) < 2:
        all_items = useful_items(split_items(lines), limit=12)
        remaining = [item for item in all_items if item not in essentials]
        treatment = useful_items(treatment + remaining, limit=9)
        if not treatment:
            treatment = useful_items(all_items, limit=9)
    if len(essentials) < 2:
        all_items = useful_items(split_items(lines), limit=12)
        essentials = useful_items(essentials + all_items, limit=7)
    return essentials, treatment, has_essentials, has_treatment


def probable_heading_at(text, position, heading):
    line_start = text.rfind("\n", 0, position) + 1
    prefix = text[line_start:position].strip()
    if prefix:
        return False
    lookahead = text[position : position + max(80, len(heading) + 40)]
    first_line = lookahead.splitlines()[0].strip() if lookahead.splitlines() else ""
    if not first_line:
        return False
    return compact(first_line).startswith(compact(heading))


def find_section(document, page_offsets, entries, index):
    entry = entries[index]
    start_page = max(0, (entry.get("bookPage") or 1) + 27)
    next_page = len(page_offsets) - 1
    if index + 1 < len(entries) and entries[index + 1].get("bookPage"):
        next_page = min(len(page_offsets) - 1, entries[index + 1]["bookPage"] + 29)

    window_start = page_offsets[max(0, start_page - 1)]
    window_end = page_offsets[min(len(page_offsets) - 1, next_page)]
    window = document[window_start:window_end]
    comp, mapping = compact_with_map(window)
    needles = [compact(entry["diagnosis"])] + [compact(item) for item in ALT_HEADINGS.get(entry["diagnosis"], [])]
    ideal_start = max(0, page_offsets[start_page] - window_start - 150)
    match = -1
    needle = needles[0]

    def boundary_ok(comp_index, value):
        start_original = mapping[comp_index]
        end_original = mapping[comp_index + len(value) - 1]
        if start_original > 0 and window[start_original - 1].isalnum():
            return False
        if end_original + 1 < len(window) and window[end_original + 1].isalnum():
            return False
        return True

    for candidate in needles:
        search_from = 0
        while True:
            candidate_match = comp.find(candidate, search_from)
            if candidate_match < 0:
                break
            if not boundary_ok(candidate_match, candidate):
                search_from = candidate_match + 1
                continue
            original_pos = mapping[candidate_match]
            if original_pos >= ideal_start:
                if match < 0 or original_pos < mapping[match]:
                    match = candidate_match
                    needle = candidate
                break
            search_from = candidate_match + 1
        if match < 0:
            candidate_match = comp.find(candidate)
            if candidate_match >= 0 and boundary_ok(candidate_match, candidate):
                match = candidate_match
                needle = candidate
    if match < 0:
        return ""

    heading_end = mapping[match + len(needle) - 1] + 1
    section_end = len(window)
    for next_entry in entries[index + 1 : min(len(entries), index + 6)]:
        next_needles = [next_entry["diagnosis"]] + ALT_HEADINGS.get(next_entry["diagnosis"], [])
        found_heading = False
        for next_heading in next_needles:
            next_needle = compact(next_heading)
            search_from = match + len(needle)
            while True:
                next_match = comp.find(next_needle, search_from)
                if next_match < 0:
                    break
                candidate = mapping[next_match]
                if candidate > heading_end + 40 and probable_heading_at(window, candidate, next_heading):
                    section_end = min(section_end, candidate)
                    found_heading = True
                    break
                search_from = next_match + 1
            if found_heading:
                break
        if found_heading:
            break

    return window[heading_end:section_end]


def remove_cross_duplicates(essentials, treatment):
    essential_keys = {re.sub(r"[^a-z0-9]+", "", item.lower()) for item in essentials}
    cleaned_treatment = []
    for item in treatment:
        key = re.sub(r"[^a-z0-9]+", "", item.lower())
        if key and key in essential_keys:
            continue
        cleaned_treatment.append(item)
    return essentials, cleaned_treatment


def apply_section_override(entry, essentials, treatment):
    override = SECTION_OVERRIDES.get((entry["diagnosis"], entry["category"]))
    if not override:
        return essentials, treatment
    return (
        useful_items(override.get("essentials", essentials), limit=7),
        useful_items(override.get("treatment", treatment), limit=9),
    )


def red_flags_for(name, essentials, treatment):
    text = " ".join(essentials + treatment).lower()
    flags = []
    checks = [
        ("shock", "Shock or hypotension"),
        ("peritonitis", "Peritonitis"),
        ("perforation", "Perforation suspected"),
        ("gangrene", "Gangrene suspected"),
        ("dehydration", "Dehydration"),
        ("difficulty in breathing", "Difficulty breathing"),
        ("cyanosis", "Cyanosis"),
        ("coma", "Altered sensorium or coma"),
        ("haematemesis", "Haematemesis"),
        ("hematemesis", "Haematemesis"),
        ("jaundice", "Jaundice"),
        ("sepsis", "Sepsis"),
        ("silent chest", "Silent chest"),
    ]
    for needle, label in checks:
        if needle in text and label not in flags:
            flags.append(label)
    if name in EMERGENCY_OR_SURGICAL and "Urgent referral/admission advised" not in flags:
        flags.insert(0, "Urgent referral/admission advised")
    return flags[:6]


def is_drug_like(item):
    return bool(
        re.search(
            r"\b(tab|tablet|cap|capsule|inj|injection|syp|syrup|mg|gm|ml|iv|im|sc|oral|tds|bd|od|qid|sos|nebul|inhal|drops?)\b",
            item,
            re.I,
        )
    )


def natural_rx_line(item):
    text = re.sub(r"\s+", " ", item).strip(" .;")
    text = re.sub(r"^(Tab|Tablet)\b", "Tab", text, flags=re.I)
    text = re.sub(r"^(Cap|Capsule)\b", "Cap", text, flags=re.I)
    text = re.sub(r"^(Inj|Injection)\b", "Inj", text, flags=re.I)
    if re.match(r"^(Tab|Tablet|Cap|Capsule)\b", text, re.I) and not re.search(r"\borally\b|\bby mouth\b", text, re.I):
        text = re.sub(r"\s+(tds|bd|od|qid|sos|hs)\b", r" orally \1", text, count=1, flags=re.I)
    return text


def dedupe(items):
    output = []
    seen = set()
    for item in items:
        item = re.sub(r"\s+", " ", item).strip(" -.;")
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def compact_prescription(text):
    cleaned = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        if re.match(r"^(Dose|Route|Frequency|Duration|Instructions):\s*$", line):
            continue
        if re.match(r"^[-•]\s*$", line):
            continue
        cleaned.append(line)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    return "\n".join(cleaned)


def build_prescription(name, treatment, red_flags):
    if name in CURATED_PRESCRIPTIONS:
        return compact_prescription(CURATED_PRESCRIPTIONS[name])

    rx_items = [item for item in treatment if is_drug_like(item)]
    advice_items = [item for item in treatment if not is_drug_like(item)]
    if not rx_items:
        rx_items = treatment[:2]
        advice_items = treatment[2:]

    lines = ["Rx"]
    if name in EMERGENCY_OR_SURGICAL:
        lines.append("1. Urgent referral/admission advised")
        for number, item in enumerate(treatment[:2], start=2):
            lines.append(f"{number}. {natural_rx_line(item)}")
    else:
        for number, item in enumerate(dedupe(rx_items)[:3], start=1):
            lines.append(f"{number}. {natural_rx_line(item)}")

    lines.extend(["", "Advice:"])
    for item in dedupe(advice_items)[:3] or dedupe(treatment[:2]):
        lines.append(f"- {item}")

    lines.extend(["", "Follow-up:"])
    if name in EMERGENCY_OR_SURGICAL:
        lines.append("- Same-day referral/admission.")
    else:
        lines.append("- Review according to symptoms and response.")

    lines.extend(["", "Red flags:"])
    for item in red_flags or ["Worsening symptoms", "Poor response to treatment"]:
        lines.append(f"- {item}")
    return compact_prescription("\n".join(lines))


def is_valid_disease(name, essentials, treatment):
    if not name or len(name) < 3:
        return False
    if len(useful_items(essentials)) < 1:
        return False
    if len(useful_items(treatment)) < 1:
        return False
    bad_text = " ".join(essentials + treatment).lower()
    if any(fragment in bad_text for fragment in ["chemical constituents of blood", "reference values for urine"]):
        return False
    return True


def main():
    reader = PdfReader(str(PDF_PATH))
    entries = parse_contents(reader)

    page_texts = [normalize_raw_text(page.extract_text() or "") for page in reader.pages]
    page_offsets = []
    chunks = []
    offset = 0
    for index, text in enumerate(page_texts, start=1):
        chunk = f"\n\n[[PDFPAGE {index}]]\n{text}"
        page_offsets.append(offset)
        chunks.append(chunk)
        offset += len(chunk)
    page_offsets.append(offset)
    document = "".join(chunks)

    records = []
    skipped = []
    for index, entry in enumerate(entries):
        if not entry.get("include"):
            continue
        raw_section = find_section(document, page_offsets, entries, index)
        cleaned = strip_noise(raw_section)
        essentials, treatment, has_essentials, has_treatment = split_section(cleaned)
        essentials, treatment = apply_section_override(entry, essentials, treatment)
        if entry["diagnosis"] in MODERN_UPDATES:
            treatment = useful_items(treatment + MODERN_UPDATES[entry["diagnosis"]], limit=9)
        essentials, treatment = remove_cross_duplicates(essentials, treatment)
        essentials, treatment = validate_public_summary(essentials, treatment)

        if not is_valid_disease(entry["diagnosis"], essentials, treatment):
            skipped.append(entry["diagnosis"])
            continue

        red_flags = red_flags_for(entry["diagnosis"], essentials, treatment)
        records.append(
            {
                "id": entry["id"],
                "diagnosis": entry["diagnosis"],
                "category": entry["category"],
                "pdfPage": entry["pdfPage"],
                "essentialsOfDiagnosis": essentials,
                "treatmentManagement": treatment,
                "prescription": build_prescription(entry["diagnosis"], treatment, red_flags),
                "redFlags": red_flags,
            }
        )

    records.sort(key=lambda item: item["diagnosis"].lower())
    OUT_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} diagnoses to {OUT_PATH}")
    print(f"Skipped {len(skipped)} low-content/non-treatment entries")


if __name__ == "__main__":
    main()
