# Diagnosis Prescriber

Local clinical reference app using a summarized diagnosis JSON database.

## Run

```bash
python3 -m http.server 4173
```

Open `http://127.0.0.1:4173`.

## Included

- 286 alphabetized diagnoses with concise Essentials and Treatment/Management summaries.
- No original PDF, page scans, or long raw textbook pages are included in the public app.
- Search, fuzzy matching, category filters and diagnosis dropdown.
- Editable prescription output with copy and print actions.
- Emergency/referral prescription wording for conditions such as DKA, appendicitis, acute cholecystitis and anaphylaxis.

## Data

The app reads `data/diagnoses.json`, which is limited to short summarized clinical points for hosting safety.

## Install

Desktop install:
Open the Netlify URL in Chrome or Edge.
Click the install icon in the address bar, or browser menu -> Cast, save, and share -> Install page as app.

Android install:
Open the Netlify URL in Chrome.
Tap menu ⋮ -> Add to Home screen / Install app.

iPhone install:
Open the Netlify URL in Safari.
Tap Share -> Add to Home Screen.

Checked starter diagnoses:

- Achalasia Cardia
- Acute Cholecystitis
- Acute Gastritis
- Amoebiasis
- Appendicitis
- Bronchial Asthma
- Hypertension
- Diabetes Mellitus
- Diabetic Ketoacidosis
- Anaphylactic Shock
