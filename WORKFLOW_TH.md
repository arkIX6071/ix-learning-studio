# IX Learning Studio — Reusable Learning Workflow v1.0

**Scope:** ใช้ได้ทุกหัวข้อ; มี Interactive HTML เป็นสื่อหลัก **เมื่อแนวคิดนั้นมีความสัมพันธ์เชิงตัวแปรที่ทดลองได้** แต่ไม่บังคับใส่ Slider ให้หัวข้อที่ไม่เหมาะ (เช่น การตีความเอกสาร กฎหมาย ประวัติศาสตร์ หรือหลักการเชิงคุณค่า)

## Intake & privacy

- รับหัวข้อ, คำถาม, PDF, research paper, dataset, lecture, หรือ URL; กำหนด learning objective เดียวที่วัดได้
- ตรวจระดับผู้เรียนและความรู้เดิมจากบทสนทนาปัจจุบัน; ถ้าข้อมูลพอให้เริ่มทันที ไม่สร้างแบบฟอร์มยาว
- ตั้ง Source Registry: ชื่อ, ผู้เขียน/หน่วยงาน, version/date, URL หรือ file source, ช่วงที่นำมาใช้, license, และความน่าเชื่อถือ
- แยก **FACT / MODEL / ASSUMPTION / LIMITATION / RECOMMENDATION** สำหรับข้อเท็จจริงและผลสรุปสำคัญ
- จัดชั้นข้อมูล: PUBLIC / PRIVATE / RESTRICTED. เนื้อหาที่เป็นงานราชการ/วิจัยที่ยังไม่เผยแพร่/ข้อมูลสำคัญ = ห้ามใส่ public GitHub Pages. ถ้าไม่แน่ใจ ไม่เผยแพร่

## Six-stage build with QA Gates

| Stage | Deliverable | Quality gate (ผ่านก่อนขั้นถัดไป) |
|---|---|---|
| 1. Intake | objective, source registry, privacy status | แหล่งข้อมูลชัดเจน เป้าหมายวัดได้ และอนุญาตให้นำข้อมูลไปใช้ในรูปแบบที่เลือก |
| 2. Explain | short explanation → deep explanation, glossary, misconception | ผู้เรียนเข้าใจประเด็นภายใน ~20 วินาที; facts/model/assumptions แยกชัด; ไม่คิดเลขผิด |
| 3. Visualize | flow/SVG/diagram + alt text | ทุกลูกศรมีความหมาย label ชัด แม้ปิด animation |
| 4. Experiment | HTML with real state, derived output, reset, numeric alternative | เปลี่ยน input แล้ว output/graph อัปเดต; ตรวจกรณีขอบเขต, หน่วย, domain, iPad CSS; ไม่มี event ขยะ |
| 5. Mastery | Predict → Test → Feedback → Fading | ผู้เรียนอธิบายเหตุผลได้ ไม่ใช่แค่กดเลือก; PASS/RETRY; ถ้า RETRY วนกลับขั้นอธิบาย |
| 6. Verify & retain | consistency audit, QA.md, version, changelog | ข้อสรุปคงที่ทุกสื่อ; UI accessible; guard privacy before hosting |

Video: optional 60–90s when temporal process or motion significantly clarifies the idea; check storyboards against lesson model. Never imply video exists if only script/storyboard was produced.

## Pedagogy

1. **Staircase:** Concrete question → one mental model → equation/logic → example → edge case → realistic limitation.
2. **Mastery Gate:** User predicts before reveal. Criteria: concept + mechanism + failure mode (user must pass, not just tool-generated score).
3. **Fading:** Guided worked example → partial scaffold → no scaffold / own explanation.
4. **Active recall:** Brief recap, 2–3 retrieval questions, spaced review prompt when user wants it.
5. **Transfer:** New context, changed assumptions, external data test when safe.

## Scientific & engineering QA

- Reference systems: frame, epoch, axis, units, uncertainties, covariance, geodetic accuracy; never equate ENU propagation with an ITRF transformation.
- Coding: domain validation, pure mathematical kernel, independent numerical anchors, edge cases, reset, mobile input and JavaScript-disabled warning.
- Research: distinguish evidence and interpretation, verify claims against provided sources, note stale material or missing ground truth.
- Source data: never fabricate citations, study outcomes or experimental validation.
- Operationally sensitive systems (e.g. Bernese): strictly **read-only by default**. No run/reprocess or change without specific approval and change-control record.

## Content taxonomy and interactive component choice

- **Mathematics / Physics / Geodesy:** parameter sliders, plots, unit checks, error propagation.
- **GIS / Remote Sensing:** layer toggles, indices/histograms and synthetic map models.
- **Programming:** editable pseudo-inputs, traces, assertions, input-output comparisons; no untrusted execution.
- **Research methods:** causal diagrams, sampling variation demos, reproducibility checklist.
- **History / theory / argument:** evidence timeline, source-comparison tool, branching causality; do not fake quantitative inputs.
- **Language / writing:** interactive annotation, revision before/after, comprehension quiz.
- **Everyday topics:** identify real mechanism and honest constraints; do not add simulation where no defensible model exists.

## Publish / store

- Each lesson `lessons/<slug>/index.html` (standalone HTML) and, when published, optional `source.md`, `QA.md`, `assets/`.
- Site index provides discovery; relative URLs make it work under GitHub Pages project path.
- Public site is a *curated* safe subset; private sources and notes remain in private storage/local files.
- Every change should record BEFORE → AFTER, changed paths, numerical/interaction QA results, rollback and version.

## Content generation on the next learning request

If user says “สร้างเป็น IX Learning Studio” or asks to learn a complex new topic, start at Stage 1 automatically, without re-asking known global preferences. Offer only one clarification if materially necessary to define target outcome. Prefer the lowest sufficient artifact; deliver working HTML, not static mockups, when interaction adds understanding. Record what is tested and what is not.
