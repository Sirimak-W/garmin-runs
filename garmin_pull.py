"""
garmin_pull.py
ดึงข้อมูลการวิ่งจาก Garmin Connect แล้วเซฟเป็น runs.csv + runs.json
ออกแบบให้รันบน GitHub Actions (อ่าน credential จาก environment / Secrets)

รันในเครื่อง (ทดสอบ):
    pip install garminconnect pandas
    export GARMIN_EMAIL="you@example.com"
    export GARMIN_PASSWORD="yourpassword"
    python garmin_pull.py --days 120

Output:
    docs/runs.csv   — สำหรับโหลดเก็บ
    docs/runs.json  — สำหรับหน้าเว็บอ่านไปแสดง
    docs/meta.json  — ข้อมูลกำกับ (ดึงเมื่อไหร่ ช่วงวันไหน)
"""

import os
import json
import argparse
from datetime import date, datetime, timedelta, timezone

import pandas as pd
from garminconnect import Garmin

OUT_DIR = "docs"  # GitHub Pages เสิร์ฟจากโฟลเดอร์ docs/


def authenticate() -> Garmin:
    """ล็อกอิน Garmin โดยอ่าน credential จาก env (GitHub Secrets)."""
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    token = os.getenv("GARMIN_TOKEN")  # ทางเลือก: base64 token หากตั้งค่าไว้

    if not (email and password) and not token:
        raise SystemExit("ต้องตั้ง GARMIN_EMAIL + GARMIN_PASSWORD (หรือ GARMIN_TOKEN)")

    client = Garmin(email, password)
    # ถ้ามี token store จาก garth จะ resume session ได้ (เลี่ยง MFA/rate limit)
    if token:
        try:
            client.garth.loads(token)
            client.garth.refresh_oauth()
            return client
        except Exception:
            pass  # fallback ไปล็อกอินปกติ
    client.login()
    return client


def _r(v, n=1):
    """ปัดเศษถ้าเป็นตัวเลข ไม่งั้นคืน None (กันค่า field ที่ Garmin ไม่ได้บันทึก)."""
    return round(v, n) if isinstance(v, (int, float)) else None


def to_run(a: dict) -> dict:
    """แปลง activity ดิบเป็น record แบน 1 แถวต่อ 1 การวิ่ง."""
    dist_km = (a.get("distance", 0) or 0) / 1000
    dur_min = (a.get("duration", 0) or 0) / 60
    pace = round(dur_min / dist_km, 3) if dist_km > 0 else None
    return {
        "date": (a.get("startTimeLocal") or "")[:10],
        "distance_km": round(dist_km, 2),
        "duration_min": round(dur_min, 2),
        "pace_min_km": pace,
        "avg_hr": a.get("averageHR"),
        "max_hr": a.get("maxHR"),
        # cadence (ก้าว/นาที)
        "avg_cadence": _r(a.get("averageRunningCadenceInStepsPerMinute"), 0),
        "max_cadence": _r(a.get("maxRunningCadenceInStepsPerMinute"), 0),
        # ฟิตเนส: VO2max + training effect
        "vo2max": _r(a.get("vO2MaxValue"), 1),
        "aerobic_te": _r(a.get("aerobicTrainingEffect"), 1),
        "anaerobic_te": _r(a.get("anaerobicTrainingEffect"), 1),
        # พลัง + ความเร็ว (Garmin เก็บ speed เป็น m/s → แปลงเป็น km/h)
        "avg_power": _r(a.get("avgPower"), 0),
        "max_power": _r(a.get("maxPower"), 0),
        "avg_speed_kmh": _r((a.get("averageSpeed") or 0) * 3.6, 2) if a.get("averageSpeed") else None,
        "max_speed_kmh": _r((a.get("maxSpeed") or 0) * 3.6, 2) if a.get("maxSpeed") else None,
        # running dynamics (ฟอร์มการวิ่ง)
        "stride_length_cm": _r(a.get("avgStrideLength"), 1),
        "ground_contact_ms": _r(a.get("avgGroundContactTime"), 0),
        "vertical_oscillation_cm": _r(a.get("avgVerticalOscillation"), 1),
        "elevation_gain_m": round(a.get("elevationGain", 0) or 0, 1),
        "calories": a.get("calories"),
        "activity_name": a.get("activityName", "Run"),
    }


def pull(days: int, start_arg: str | None, end_arg: str | None):
    """ดึงข้อมูลตามช่วงวัน: ใช้ start/end ถ้ามี ไม่งั้นใช้ days ย้อนหลัง."""
    if start_arg and end_arg:
        start, end = start_arg, end_arg
    else:
        start = (date.today() - timedelta(days=days)).isoformat()
        end = date.today().isoformat()

    client = authenticate()
    activities = client.get_activities_by_date(start, end, activitytype="running")
    runs = [to_run(a) for a in activities if (a.get("distance") or 0) > 0]
    runs.sort(key=lambda r: r["date"])
    return runs, start, end


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=120, help="จำนวนวันย้อนหลัง")
    p.add_argument("--start", help="วันเริ่ม YYYY-MM-DD (ใช้คู่กับ --end)")
    p.add_argument("--end", help="วันสิ้นสุด YYYY-MM-DD")
    args = p.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    runs, start, end = pull(args.days, args.start, args.end)

    # เซฟ JSON (หน้าเว็บอ่าน)
    with open(f"{OUT_DIR}/runs.json", "w", encoding="utf-8") as f:
        json.dump(runs, f, ensure_ascii=False, indent=2)

    # เซฟ CSV (โหลดเก็บ)
    pd.DataFrame(runs).to_csv(f"{OUT_DIR}/runs.csv", index=False)

    # เซฟ meta — บอกว่าดึงเมื่อไหร่ ช่วงไหน
    meta = {
        "pulled_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "range_start": start,
        "range_end": end,
        "count": len(runs),
        "total_km": round(sum(r["distance_km"] for r in runs), 1),
    }
    with open(f"{OUT_DIR}/meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"ดึง {len(runs)} runs ({start} → {end}) เซฟลง {OUT_DIR}/")


if __name__ == "__main__":
    main()
