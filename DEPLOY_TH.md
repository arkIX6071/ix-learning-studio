# เผยแพร่ IX Learning Studio ผ่าน GitHub Pages (ขั้นตอนที่ยังไม่ได้ทำ)

**สำคัญ:** GitHub Pages เป็นเว็บไซต์สาธารณะ แม้ source repository บางแผนจะตั้งเป็น Private ก็ไม่ได้หมายความว่าเว็บไซต์เป็น Private. ห้ามเผยแพร่ข้อมูลจาก RTSD / ข้อมูลบุคคล / งานวิจัยที่ยังไม่อนุญาต

1. ลงชื่อเข้าใช้ GitHub ในบัญชีที่ต้องการใช้งาน
2. สร้าง repository ชื่อ `ix-learning-studio` แยกจาก `pyproj`; แนะนำ `Public` เฉพาะเนื้อหาสังเคราะห์ในชุดนี้
3. สร้าง `README.md` ระหว่างสร้าง repository หรือเตรียม `main` branch ไว้
4. นำ **ไฟล์และโฟลเดอร์ข้างใน ZIP** เข้า repository root: `index.html`, `lessons/`, `WORKFLOW_TH.md`, ... (ไม่ใช่ ZIP ไฟล์เดี่ยว)
5. ไป `Settings` → `Pages` → `Build and deployment` → `Source: Deploy from a branch` → `main` / `(root)` → `Save`
6. หลัง deploy สำเร็จ เว็บไซต์จะใช้ URL ลักษณะ `https://<user>.github.io/ix-learning-studio/` แต่ **ห้ามถือว่า URL ใช้งานได้จนกว่าจะตรวจจริง**
7. เปิด URL นั้นบน Chrome iPad ลองลาก Slider, แก้ช่องตัวเลข, Reset, เปิดบทเรียน 2 และใช้ Learning Library search
8. สำหรับบทใหม่ เพิ่มไฟล์ที่ผ่าน QA และอัปเดต catalog; ไม่อัปโหลด source/notes ที่เป็นความลับ

เอกสาร GitHub ที่ใช้ตรวจขั้นตอน: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
