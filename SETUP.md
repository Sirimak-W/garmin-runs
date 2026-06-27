# คู่มือ: ดึงข้อมูล Garmin → ดูบน iPhone (ฟรี ด้วย GitHub Actions + Pages)

ระบบนี้ดึงผลการวิ่งจาก Garmin อัตโนมัติทุกวัน เซฟเป็น CSV/JSON เก็บใน repo
แล้วเสิร์ฟเป็นหน้าเว็บที่เปิดดูบน iPhone ได้ พร้อมปุ่มโหลด CSV — **ไม่มีค่าใช้จ่าย**

```
GitHub Actions (cron รายวัน)
  └─ รัน garmin_pull.py  (อ่าน user/pass จาก GitHub Secrets)
       └─ เซฟ docs/runs.csv + runs.json + meta.json → commit เข้า repo
            └─ GitHub Pages เสิร์ฟ docs/index.html
                 └─ เปิดบน iPhone Safari → ตาราง/กราฟ + ปุ่มโหลด CSV
```

---

## โครงสร้างไฟล์

```
garmin-pages/
├── garmin_pull.py              # สคริปต์ดึงข้อมูล (รันบน Actions)
├── .github/workflows/pull.yml  # ตั้งเวลา + รันมือ
└── docs/                       # โฟลเดอร์ที่ Pages เสิร์ฟ
    ├── index.html              # หน้าเว็บ (มือถือ)
    ├── runs.json               # ข้อมูลที่หน้าเว็บอ่าน
    ├── runs.csv                # ไฟล์โหลดเก็บ
    └── meta.json               # กำกับ: ดึงเมื่อไหร่ ช่วงวันไหน
```

> ไฟล์ `runs.*` และ `meta.json` ที่ให้มาเป็นข้อมูล **ตัวอย่าง** เพื่อให้หน้าเว็บ
> แสดงได้ทันที พอ Actions รันจริงครั้งแรกจะถูกเขียนทับด้วยข้อมูลของคุณ

---

## ขั้นตอนติดตั้ง (ทำครั้งเดียว)

### 1. สร้าง GitHub repo
- สร้าง repo ใหม่ (เช่น `garmin-runs`) แล้วอัปโหลดไฟล์ทั้งหมดขึ้นไป
- **เรื่องความเป็นส่วนตัว** ⚠️ — เลือกอย่างใดอย่างหนึ่ง:
  - **Public repo** → Pages ฟรีทุกบัญชี แต่ข้อมูลวิ่งจะ "เปิดเผยต่อสาธารณะ"
  - **Private repo** → ข้อมูลไม่เปิดเผย แต่ Pages ต้องเป็นบัญชี **GitHub Pro**
  - ถ้าไม่อยากให้ข้อมูล public และไม่อยากจ่าย Pro → ดู [ทางเลือก Colab](#ถ้าไม่อยากให้ข้อมูลเปิดเผย) ท้ายไฟล์

### 2. ใส่ credential เป็น Secrets (ปลอดภัย ไม่โผล่ในโค้ด)
ไปที่ **repo → Settings → Secrets and variables → Actions → New repository secret**
เพิ่ม 2 ตัว:

| ชื่อ Secret | ค่า |
|---|---|
| `GARMIN_EMAIL` | อีเมล Garmin ของคุณ |
| `GARMIN_PASSWORD` | รหัสผ่าน Garmin |

> Secrets ถูกเข้ารหัส ไม่แสดงใน log และคนอื่นเห็น repo ก็มองไม่เห็นค่า

### 3. เปิด GitHub Pages
ไปที่ **repo → Settings → Pages**
- Source: **Deploy from a branch**
- Branch: **main** · Folder: **/docs**
- กด Save → รอสักครู่จะได้ URL หน้าตา `https://<username>.github.io/<repo>/`

### 4. เปิดสิทธิ์ให้ Actions เขียน repo ได้
ไปที่ **Settings → Actions → General → Workflow permissions**
เลือก **Read and write permissions** → Save
(จำเป็น เพราะ workflow ต้อง commit ไฟล์ผลลัพธ์กลับเข้า repo)

### 5. ทดสอบรันครั้งแรก
ไปที่แท็บ **Actions → Pull Garmin Runs → Run workflow**
- กรอก `days` เช่น `120` แล้วกดรัน
- รอจน job เขียว → เปิด URL ของ Pages บน iPhone

---

## การใช้งานประจำวัน

- **อัตโนมัติ** — workflow รันเองทุกวัน 08:00 น. (เวลาไทย) ดึงข้อมูลล่าสุดมาอัปเดตหน้าเว็บ
- **เปิดบน iPhone** — เปิด URL Pages ใน Safari → กด **Share → Add to Home Screen**
  จะได้ไอคอนเหมือนแอป เปิดดูได้เร็ว
- **โหลด CSV** — กดปุ่ม "⬇︎ โหลด CSV" → ไฟล์เซฟลงแอป **Files** ของ iPhone ได้เลย

### ดึงข้อมูลช่วงวันที่เจาะจง
แท็บ **Actions → Run workflow** แล้วกรอก:
- `start` = `2026-01-01`
- `end` = `2026-03-31`

หน้าเว็บจะมีแถบบนสุดบอกชัดว่า **"ข้อมูลช่วง [วันเริ่ม – วันสิ้นสุด]"** และ
**"ดึงล่าสุด [วันเวลา]"** เพื่อให้รู้เสมอว่ากำลังดูข้อมูลของช่วงไหน

---

## ปรับแต่งที่เจอบ่อย

| อยากทำ | แก้ที่ |
|---|---|
| เปลี่ยนเวลา cron | `pull.yml` → `cron: "0 1 * * *"` (เป็น UTC; ไทย = +7) |
| เปลี่ยนช่วงดึง default | `pull.yml` → `days` default `"120"` |
| เปลี่ยนเป้า pace บนกราฟ | `index.html` → `GOAL_PACE = 7.5` |
| เปลี่ยน metric ที่ดึง | `garmin_pull.py` → ฟังก์ชัน `to_run()` |

---

## ข้อควรรู้ / ข้อจำกัด

- **`garminconnect` เป็น library ไม่เป็นทางการ** — ถ้า Garmin เปลี่ยน endpoint
  อาจพังต้องอัปเดตเวอร์ชัน (pin ไว้แล้วเพื่อกันพังเอง)
- **MFA** — ถ้าเปิด 2-factor บน Garmin การล็อกอินอัตโนมัติบน server จะยุ่ง
  ทางแก้: ล็อกอินในเครื่องครั้งแรกให้ `garth` เซฟ token แล้วเอา token ใส่เป็น
  Secret ชื่อ `GARMIN_TOKEN` (สคริปต์รองรับไว้แล้ว)
- **Rate limit** — อย่าตั้ง cron ถี่เกินไป วันละครั้งพอ
- **GitHub Actions ฟรี** — repo public ใช้ได้ไม่จำกัด; repo private มีโควต้านาที/เดือน
  (งานนี้ใช้แค่ไม่กี่นาที/วัน ไม่เกินโควต้าฟรีแน่นอน)

---

## ถ้าไม่อยากให้ข้อมูลเปิดเผย

ถ้าไม่โอเคกับ public repo และไม่อยากจ่าย GitHub Pro มี 2 ทางฟรี:
1. **Google Colab** — เปิด notebook ใน Safari บน iPhone กด Run ดึงข้อมูล แล้วโหลด CSV
   (รันเอง ไม่ auto แต่ไม่เปิดเผยข้อมูลเลย)
2. **รันในเครื่อง** — รัน `garmin_pull.py` บน Mac แล้ว AirDrop CSV เข้า iPhone

บอกได้ถ้าอยากให้ทำเวอร์ชัน Colab ให้
