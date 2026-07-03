import os
import sys
import datetime
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adjust python path to find backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import Base
from backend.app.models import User, Location, Camera, Vehicle, Violation, Payment, FineRule, ActivityLog

CSV_PATH = r"C:\Users\Jaspreet\OneDrive\Desktop\Indian_Traffic_Violations.csv"
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "traffic_system.db"))

STATE_COORDS = {
    "Delhi": (28.6139, 77.2090),
    "Karnataka": (15.3173, 75.7139),
    "Maharashtra": (19.7515, 75.7139),
    "Punjab": (31.1471, 75.3412),
    "Uttar Pradesh": (26.8467, 80.9462),
    "West Bengal": (22.9868, 87.8550),
    "Tamil Nadu": (11.1271, 78.6569),
    "Gujarat": (22.2587, 71.1924)
}

VIOLATION_TYPE_MAP = {
    "No Helmet": "no_helmet",
    "Signal Jumping": "red_light_jump",
    "Over-speeding": "overspeeding",
    "Using Mobile Phone": "phone_usage",
    "No Seatbelt": "no_seatbelt",
    "Driving Without License": "no_license",
    "Wrong Parking": "wrong_parking",
    "Overloading": "overloading"
}

def seed_database():
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at {CSV_PATH}")
        return

    print(f"Reading CSV from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} records. Connecting to SQLite database at {DB_PATH}...")

    engine = create_engine(f"sqlite:///{DB_PATH}")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Ensure default admin / officer exists
        default_user = db.query(User).filter(User.username == "admin").first()
        if not default_user:
            default_user = User(
                username="admin",
                email="admin@smartcity.gov.in",
                full_name="Enforcement System Administrator",
                password_hash="pbkdf2:sha256:150000$mock_hash", # placeholder
                role="admin",
                status="active"
            )
            db.add(default_user)
            db.commit()
            db.refresh(default_user)

        # 2. Seed Locations & Cameras
        locations_cache = {}
        cameras_cache = {}
        for state, coords in STATE_COORDS.items():
            loc = db.query(Location).filter(Location.name == state).first()
            if not loc:
                loc = Location(
                    name=state,
                    description=f"{state} Smart Enforcement Zone",
                    risk_level="medium",
                    lat=coords[0],
                    lng=coords[1]
                )
                db.add(loc)
                db.commit()
                db.refresh(loc)
            locations_cache[state] = loc

            # Register camera for this location
            cam_id = f"CAM-{state[:3].upper()}-01"
            cam = db.query(Camera).filter(Camera.id == cam_id).first()
            if not cam:
                cam = Camera(
                    id=cam_id,
                    name=f"{state} High-Speed CCTV",
                    location_id=loc.id,
                    location=state,
                    status="online",
                    health_status="good",
                    lat=coords[0] + 0.005,
                    lng=coords[1] + 0.005
                )
                db.add(cam)
                db.commit()
                db.refresh(cam)
            cameras_cache[state] = cam

        print("Seeding vehicle and violation logs...")
        count = 0
        for index, row in df.iterrows():
            # Parse vehicle type
            v_type_raw = str(row["Vehicle_Type"]).lower()
            v_type = "car"
            if "scooter" in v_type_raw or "motorcycle" in v_type_raw or "bike" in v_type_raw:
                v_type = "motorcycle"
            elif "truck" in v_type_raw:
                v_type = "truck"
            elif "bus" in v_type_raw:
                v_type = "bus"
            elif "auto" in v_type_raw or "rickshaw" in v_type_raw:
                v_type = "auto"

            # Parse plate
            vlt_id = str(row["Violation_ID"])
            state_code = str(row["Registration_State"])[:2].upper()
            plate = f"{state_code}-{vlt_id[-6:]}"

            # 3. Add or retrieve Vehicle
            veh = db.query(Vehicle).filter(Vehicle.license_plate == plate).first()
            if not veh:
                # Deterministic brand based on index
                brands = ["Tata", "Maruti Suzuki", "Hyundai", "Mahindra", "Honda", "Yamaha", "Bajaj"]
                veh_brand = brands[index % len(brands)]
                veh = Vehicle(
                    license_plate=plate,
                    type=v_type,
                    brand=veh_brand,
                    color=str(row["Vehicle_Color"]),
                    owner_name=f"Owner_{vlt_id[-6:]}",
                    status="valid" if str(row["License_Validity"]) == "Valid" else "suspended"
                )
                db.add(veh)
                db.flush()

            # 4. Map Violation Type
            raw_v_type = str(row["Violation_Type"])
            viol_type = VIOLATION_TYPE_MAP.get(raw_v_type, "traffic_infraction")

            # DateTime parsing
            date_str = str(row["Date"])
            time_str = str(row["Time"])
            try:
                dt_obj = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except:
                dt_obj = datetime.datetime.utcnow()

            # Location and Camera check
            loc_name = str(row["Location"])
            camera = cameras_cache.get(loc_name)
            if not camera:
                # Default fallback
                camera = cameras_cache.get("Delhi")

            # Check if violation already exists
            existing_viol = db.query(Violation).filter(Violation.officer_notes == f"Audit ID: {vlt_id}").first()
            if not existing_viol:
                viol = Violation(
                    vehicle_id=veh.id,
                    camera_id=camera.id,
                    type=viol_type,
                    timestamp=dt_obj,
                    location=loc_name,
                    fine_amount=float(row["Fine_Amount"]),
                    status="paid" if str(row["Fine_Paid"]) == "Yes" else "pending",
                    confidence_score=0.96,
                    officer_notes=f"Audit ID: {vlt_id}",
                    evidence_image_path=f"data/uploads/evidence_{vlt_id}.jpg"
                )
                db.add(viol)
                db.flush()

                # 5. Add Payment if Paid
                if str(row["Fine_Paid"]) == "Yes":
                    pay_method = "upi"
                    raw_pay_method = str(row["Payment_Method"]).lower()
                    if "cash" in raw_pay_method:
                        pay_method = "cash"
                    elif "card" in raw_pay_method:
                        pay_method = "credit_card"

                    txn_id = f"TXN-{vlt_id}"
                    existing_pay = db.query(Payment).filter(Payment.transaction_id == txn_id).first()
                    if not existing_pay:
                        payment = Payment(
                            violation_id=viol.id,
                            amount=viol.fine_amount,
                            payment_date=dt_obj + datetime.timedelta(hours=2), # paid shortly after
                            transaction_id=txn_id,
                            payment_method=pay_method,
                            status="completed"
                        )
                        db.add(payment)

            count += 1
            if count % 500 == 0:
                db.commit()
                print(f"Processed {count} records...")

        db.commit()
        print(f"Successfully finished database seeding! Total imported/processed records: {count}")

        # Add Activity Log
        log = ActivityLog(
            user_id=default_user.id,
            action=f"Seeded {count} structured violation records from Indian_Traffic_Violations.csv"
        )
        db.add(log)
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Transaction rolled back due to error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
