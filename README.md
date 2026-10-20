# MSK-Therapy-OS (Milestone M1 CLI)

> ⚠️ **EDUCATIONAL AND ENGINEERING PROOF OF CONCEPT ONLY.**  
> Do not enter patient names, identifiable medical details, or real clinical records.  
> This system does **not** provide autonomous medical diagnosis, treatment prescriptions, spinal manipulation directives, or DDS electrical machine control. See [SPEC.md](SPEC.md) for safety/security blockers.

---

## 1. Quick Start (Python 3.10+; Zero External Dependencies)

From the project root on Windows PowerShell (or use `py -3 -m msk_therapy_os`):

```powershell
# 1. Initialize SQLite database schema
python -m msk_therapy_os init --db demo.sqlite3

# 2. Seed synthetic demonstration cases, evidence catalog, and anatomy mappings
python -m msk_therapy_os seed-demo --db demo.sqlite3

# 3. View synthetic cases
python -m msk_therapy_os cases --db demo.sqlite3

# 4. View structured intake for a case
python -m msk_therapy_os show-intake --db demo.sqlite3 --case DEMO-NECK-001

# 5. Add a synthetic visit
python -m msk_therapy_os add-visit --db demo.sqlite3 --case DEMO-NECK-001 --date 2026-10-19 --pain 6 --rom 42 --region neck --flag none --note 'Fictional student exercise'

# 6. Add structured objective ROM measurement (motion, side, angle, instrument)
python -m msk_therapy_os add-rom --db demo.sqlite3 --visit-id 1 --motion cervical_rotation --side left --angle 42.0 --method goniometer

# 7. Draft a structured SOAP note (Student role -> DRAFT)
python -m msk_therapy_os add-soap --db demo.sqlite3 --visit-id 1 --s "Stiffness turning head left" --o "Active left rotation 42 deg goniometer" --a "Mechanical cervical strain hypothesis" --p "Gentle ROM education and ergonomics" --role student

# 8. Clinical instructor supervisory review (Reviewer role -> APPROVED)
python -m msk_therapy_os review-soap --db demo.sqlite3 --soap-id 1 --reviewer "Dr. Taylor" --decision APPROVED --feedback "Appropriate educational assessment"

# 9. View longitudinal visit timeline
python -m msk_therapy_os timeline --db demo.sqlite3 --case DEMO-NECK-001

# 10. Generate comprehensive offline case report (Markdown with audit warnings)
python -m msk_therapy_os report --db demo.sqlite3 --case DEMO-NECK-001 --out report_DEMO_NECK_001.md

# 11. Run all automated unit tests
python -m unittest discover -s tests -v
```

---

## 2. Safety Gating and Contraindication Screening

The rule-based safety engine strictly enforces hard stops on red flags and modality contraindications:

```powershell
# Red flag drill: returns STOP_AND_REFER
python -m msk_therapy_os screen-safety --flag progressive_weakness

# Modality contraindication drill: DDS device with cardiac pacemaker
python -m msk_therapy_os screen-safety --flag none --modality dds_device --contraindication cardiac_pacemaker

# Forbidden modality drill: high-velocity spinal manipulation is strictly rejected
python -m msk_therapy_os screen-safety --flag none --modality spinal_manipulation
```

---

## 3. Evidence Catalog and Anatomy Adapter

Explore vetted scientific references, evidence tiers, and BodyParts3D FMA identifiers:

```powershell
# Browse Tier 1 clinical guidelines (NICE, IFOMPT, FDA)
python -m msk_therapy_os evidence --db demo.sqlite3 --tier 1

# Lookup specific evidence ID
python -m msk_therapy_os evidence --db demo.sqlite3 --id EVID-G-001

# Browse neck anatomy with BodyParts3D links
python -m msk_therapy_os anatomy --db demo.sqlite3 --region neck

# Browse traditional meridian / reflexology schemas (strictly isolated namespace)
python -m msk_therapy_os anatomy --db demo.sqlite3 --namespace TRADITIONAL_MERIDIAN

# Browse scenario-based assessment questionnaires
python -m msk_therapy_os questionnaires --db demo.sqlite3 --region neck
```

---

## 4. Architecture & Engineering Constraints

- **Platform:** Windows 64-bit, 8GB RAM, CPU-first, stdlib Python + SQLite.
- **Constraints Applied:** Constraint-first → Artifact-first → CLI-first → Evidence-first → Cost-aware → Automation-last.
- **No Cloud / AI Dependencies:** Zero external API keys, zero local LLMs, zero Docker containers.
