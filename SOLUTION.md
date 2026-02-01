# AI Engineer Home Task - ANSWERS

---

## TASK 1: Use Case Evaluation

| Use Case | Provider Submitted | Correct or Incorrect | How to Detect Overbilling vs Naive Mistake |
|----------|-------------------|---------------------|-------------------------------------------|
| Provider performs operation 29806 for shoulder arthroscopy | Claim with two lines to be charged for each shoulder | **INCORRECT** - Per UHC Bilateral Procedures Policy: "Modifier 50 indicates that a procedure has been rendered bilaterally." Bilateral procedures must be billed on ONE line with modifier 50, not two separate lines. Two lines would pay 200% instead of the correct 150%. | **Overbilling indicators:** (1) Pattern repeats across multiple claims from same provider, (2) Provider has history of billing issues, (3) No documentation justifying separate procedures. **Naive mistake indicators:** (1) One-time occurrence, (2) Clean billing history, (3) Documentation exists but coding was incorrect. **Detection:** Query for same CPT code appearing >1 time on same claim without modifier 50. |
| A pregnant woman arrived to hospital with bad feeling on Sunday and on Monday she gave birth | 59409 for the delivery on Monday and 99223 for the general EM on Sunday | **CORRECT** - Per UHC Obstetrical Policy: CPT 59409 is "delivery only" and does NOT include antepartum care. The Sunday E/M visit (99223) occurred BEFORE delivery and is separately billable. If provider had used 59400 (global OB package), this would be INCORRECT since 59400 includes antepartum visits. | **To verify correctness:** (1) Check that OB code is 59409/59514 (delivery only), NOT 59400/59510 (global). (2) Verify E/M date is before delivery date. (3) Diagnosis codes should support medical necessity for Sunday visit. **Would be overbilling if:** (1) Used global OB code (59400) AND billed separate E/M, (2) E/M and delivery on same date without modifier 25. |

---

## TASK 2: Rule Implementation Table

| Use Case / Rule | Condition Abstraction | Implementation (pseudo-code) |
|-----------------|----------------------|------------------------------|
| At this example we've a rule that implements a policy that simply says that some service (Robotic_Assisted_Surgery) is not covered | Robotic_Assisted_Surgery = [S2900]<br><br>IF CPT = Data.'Robotic_Assisted_Surgery', THEN deny | `l1: code = Robotic_Assisted_Surgery`<br>`reject "l1.code not supported"` |
| Pregnant service can't be performed on non female | IF CPT is <59400> AND patient is male THEN deny | `l1: code = 59400, Gender not in [F]`<br>`reject "l1.code cannot be provided to non-female"` |
| Preventive care includes E/M service, so in same session provider can charge for both E/M and Preventive service. In rare case provider can mark that E/M is not related to preventive by adding modifier '25' | IF claim contains CPT1 = Data.Preventive_Medicine_E/M AND CPT2 = Data.Problem_Based_E/M WITH modifier != 25 on same DOS and same Tax ID, THEN deny CPT2 | `l1: code = Data.Preventive_Medicine_E/M`<br>`l2: code = Problem_Based_E/M, Modifiers not '25'`<br>`l1.TIN = l2.TIN`<br>`l1.patient_id = l2.patient_id`<br>`l1.dos = l2.dos`<br>`reject l2 "l2.code is included in l1.code"` |
| Emergency Department Services (99281-99285) must be provided in hospital that has ER emergency room (place of service = 23) | IF CPT in [99281, 99282, 99283, 99284, 99285] AND POS != '23', THEN deny | `l1: code in [99281, 99282, 99283, 99284, 99285]`<br>`l1.place_of_service != '23'`<br>`reject l1 "ED services require POS 23 (Emergency Room)"` |
| Patient can get x-ray of Chest from just one provider on a single day | IF claim contains CPT in Chest_Xray_Codes AND another claim exists with same patient, same DOS, different provider, same anatomical area, THEN flag duplicate | `l1: code in [71045, 71046, 71047, 71048]`<br>`l2: code in [71045, 71046, 71047, 71048]`<br>`l1.patient_id = l2.patient_id`<br>`l1.dos = l2.dos`<br>`l1.provider_npi != l2.provider_npi`<br>`reject l2 "Duplicate chest X-ray from different provider same day"` |
| When more than one x-ray view of the same anatomical area is performed on a single date of service, only the code with the higher number of views will be reimbursed | IF CMS 1500 claim contains CPT_1 = Xray AND CPT_2 = Xray on same day AND CPT_1 views > CPT_2 views, THEN reject CPT_2 | **Rule 1 (Chest):**<br>`l1: code = 71046 (2 views)`<br>`l2: code = 71045 (1 view)`<br>`l1.patient_id = l2.patient_id`<br>`l1.dos = l2.dos`<br>`reject l2 "Single view bundled into 2-view code"`<br><br>**Rule 2 (General):**<br>`l1: code in Xray_Codes, views = X`<br>`l2: code in Xray_Codes, views = Y, same body_part`<br>`l1.dos = l2.dos`<br>`IF X > Y: reject l2 "Lower view code bundled"` |
| Provider should cover patient any E/M (Evaluation and Management) 45 days after primary operation (e.g., 54910) unless the return is injury or there was unrelated operation. Injury case can be detected by Diagnostic code that starts with 'S' or 'T'. Provider can notify that the service is unrelated by adding modifier 78 | IF CPT1 = Major_Surgery_With_Global AND CPT2 = E/M_Code AND CPT2.dos within global_period of CPT1.dos AND modifier NOT IN ['24', '78', '79'] AND ICD NOT LIKE 'S%' AND ICD NOT LIKE 'T%', THEN deny CPT2 | `l1: code in [54910, ...] -- Major surgery with global period`<br>`l2: code in [99201-99215, 99221-99233] -- E/M codes`<br>`l2.dos BETWEEN l1.dos AND (l1.dos + 90)`<br>`l2.modifier not in ['24', '78', '79']`<br>`l2.icd_code not like 'S%'`<br>`l2.icd_code not like 'T%'`<br>`l1.patient_id = l2.patient_id`<br>`l1.provider_npi = l2.provider_npi`<br>`reject l2 "E/M within global period - use modifier 24/78/79 if unrelated"` |

---

## Summary of Key Rules

### Modifiers You Must Know

| Modifier | Name | Use |
|----------|------|-----|
| **50** | Bilateral | Procedure on BOTH sides - use ONE line |
| **25** | Significant E/M | E/M is separate from same-day procedure |
| **24** | Unrelated E/M | E/M during global period for DIFFERENT condition |
| **78** | Return to OR | Unplanned return during global period |
| **79** | Unrelated Procedure | Different surgery during global period |

### Global Period Rule

After major surgery (90-day global), the surgeon's fee INCLUDES all follow-up E/M visits. To bill separately, must use:
- Modifier **24** if E/M is for unrelated condition
- Modifier **78** if returning to OR for complication
- Modifier **79** if performing unrelated procedure
- OR diagnosis must be injury (ICD starts with S or T)

### Bilateral Rule

**WRONG:** Two lines for each side → pays 200%
```
Line 1: 29806 (right)
Line 2: 29806 (left)
```

**RIGHT:** One line with modifier 50 → pays 150%
```
Line 1: 29806-50
```
