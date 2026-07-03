import datetime
import random
from sqlalchemy.orm import Session
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import User, Camera, Vehicle, Violation, FineRule, Payment, ActivityLog, Location, Setting
from backend.app.auth.jwt import get_password_hash
from backend.app.ai.detector import generate_random_plate, VEHICLE_BRANDS, VEHICLE_COLORS, VIOLATION_LABELS

def seed_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if users already exist
        if db.query(User).count() > 0:
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # 1. Users
        users = [
            User(
                username="admin",
                email="admin@smarttraffic.gov.in",
                full_name="Super Admin",
                password_hash=get_password_hash("admin123"),
                role="admin",
                status="active"
            ),
            User(
                username="officer",
                email="officer@smarttraffic.gov.in",
                full_name="Officer Rajesh Kumar",
                password_hash=get_password_hash("officer123"),
                role="officer",
                status="active"
            )
        ]
        db.add_all(users)
        db.commit()

        # 2. Locations
        locations = [
            Location(name="Connaught Place", description="Central commercial hub", risk_level="high", lat=28.6304, lng=77.2177),
            Location(name="India Gate Circle", description="Tourist circular landmark", risk_level="medium", lat=28.6129, lng=77.2295),
            Location(name="Rajouri Garden", description="West Delhi shopping sector", risk_level="medium", lat=28.6415, lng=77.1245),
            Location(name="AIIMS Crossing", description="Major ring road interchange", risk_level="high", lat=28.5672, lng=77.2100),
            Location(name="Karol Bagh", description="East Metro market crossing", risk_level="low", lat=28.6441, lng=77.1895)
        ]
        db.add_all(locations)
        db.commit()

        # 3. Settings
        settings_items = [
            Setting(key="ai_mode", value="simulated", description="AI Execution Mode (active, simulated)"),
            Setting(key="confidence_threshold", value="0.45", description="YOLO/OCR Confidence Threshold limit"),
            Setting(key="speed_limit", value="60.0", description="City Speed Limit in KM/H")
        ]
        db.add_all(settings_items)
        db.commit()

        # Fetch locations for camera foreign keys mapping
        cp_loc = db.query(Location).filter(Location.name == "Connaught Place").first()
        ig_loc = db.query(Location).filter(Location.name == "India Gate Circle").first()
        rg_loc = db.query(Location).filter(Location.name == "Rajouri Garden").first()
        ax_loc = db.query(Location).filter(Location.name == "AIIMS Crossing").first()
        kb_loc = db.query(Location).filter(Location.name == "Karol Bagh").first()

        # 4. Cameras
        cameras = [
            Camera(
                id="CAM-001",
                name="Connaught Place Outer Ring",
                location_id=cp_loc.id if cp_loc else None,
                location="Connaught Place, New Delhi",
                ip_address="192.168.10.51",
                status="online",
                health_status="good",
                lat=28.6304,
                lng=77.2177
            ),
            Camera(
                id="CAM-002",
                name="India Gate Circle",
                location_id=ig_loc.id if ig_loc else None,
                location="Rajpath, New Delhi",
                ip_address="192.168.10.52",
                status="online",
                health_status="good",
                lat=28.6129,
                lng=77.2295
            ),
            Camera(
                id="CAM-003",
                name="Rajouri Garden Intersection",
                location_id=rg_loc.id if rg_loc else None,
                location="Rajouri Garden, New Delhi",
                ip_address="192.168.10.53",
                status="online",
                health_status="warning",
                lat=28.6415,
                lng=77.1245
            ),
            Camera(
                id="CAM-004",
                name="AIIMS Crossing Main Feed",
                location_id=ax_loc.id if ax_loc else None,
                location="Ring Road, AIIMS, New Delhi",
                ip_address="192.168.10.54",
                status="offline",
                health_status="critical",
                lat=28.5672,
                lng=77.2100
            ),
            Camera(
                id="CAM-005",
                name="Karol Bagh Market CCTV 3",
                location_id=kb_loc.id if kb_loc else None,
                location="Karol Bagh, New Delhi",
                ip_address="192.168.10.55",
                status="online",
                health_status="good",
                lat=28.6441,
                lng=77.1895
            )
        ]
        db.add_all(cameras)
        db.commit()

        # 5. Fine Rules
        fine_rules = [
            FineRule(violation_type="red_light_jump", amount=2000.0, description="Red light signal violation"),
            FineRule(violation_type="wrong_lane", amount=1000.0, description="Driving in designated wrong/bus lane"),
            FineRule(violation_type="overspeeding", amount=1000.0, description="Exceeding posting speed limit limits"),
            FineRule(violation_type="no_helmet", amount=500.0, description="Two-wheeler rider riding without helmet"),
            FineRule(violation_type="no_seatbelt", amount=500.0, description="Four-wheeler driver driving without seatbelt"),
            FineRule(violation_type="triple_riding", amount=1000.0, description="Triple riding on two-wheeler"),
            FineRule(violation_type="mobile_usage", amount=1500.0, description="Using mobile cell phone while driving"),
            FineRule(violation_type="illegal_parking", amount=500.0, description="Parking vehicle in restricted yellow lines"),
            FineRule(violation_type="against_traffic", amount=2000.0, description="Driving opposite to direction of traffic"),
            FineRule(violation_type="stop_line_crossing", amount=500.0, description="Crossing stop line during red signal light")
        ]
        db.add_all(fine_rules)
        db.commit()

        # 6. Vehicles & 7. Violations
        violations_count = 70
        v_types = list(VIOLATION_LABELS.keys())
        
        # Generate some mock vehicles
        vehicles_pool = []
        owner_names = [
            "Amit Sharma", "Priya Patel", "Rajesh Kumar", "Sunita Rao", 
            "Vikram Singh", "Neha Gupta", "Karan Malhotra", "Sneha Iyer",
            "Anil Verma", "Pooja Reddy", "Manish Joshi", "Shalini Sen"
        ]
        
        vehicle_types = ["car", "motorcycle", "truck", "bus", "auto"]
        
        for _ in range(40):
            v_type = random.choice(vehicle_types)
            brand = random.choice(VEHICLE_BRANDS[v_type])
            color = random.choice(VEHICLE_COLORS)
            plate = generate_random_plate()
            
            vehicle = Vehicle(
                license_plate=plate,
                type=v_type,
                brand=brand,
                color=color,
                owner_name=random.choice(owner_names),
                status=random.choice(["valid", "valid", "valid", "expired", "stolen"])
            )
            db.add(vehicle)
            db.flush()
            vehicles_pool.append(vehicle)
            
        db.commit()
        
        # Build violations
        current_time = datetime.datetime.utcnow()
        cameras_pool = db.query(Camera).filter(Camera.status == "online").all()
        
        for i in range(violations_count):
            # Distribute violations in the last 15 days
            days_ago = random.randint(0, 14)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            timestamp = current_time - datetime.timedelta(
                days=days_ago, hours=hours_ago, minutes=minutes_ago
            )
            
            vehicle = random.choice(vehicles_pool)
            camera = random.choice(cameras_pool)
            
            viol_type = random.choice(v_types)
            # Match vehicle type for realistic violations
            if viol_type in ["no_helmet", "triple_riding"]:
                vehicle = [v for v in vehicles_pool if v.type == "motorcycle"][0]
            elif viol_type == "no_seatbelt":
                vehicle = [v for v in vehicles_pool if v.type == "car"][0]
                
            rule = db.query(FineRule).filter(FineRule.violation_type == viol_type).first()
            fine_amount = rule.amount
            
            status = random.choices(["pending", "paid", "resolved"], weights=[60, 30, 10])[0]
            
            violation = Violation(
                vehicle_id=vehicle.id,
                camera_id=camera.id,
                type=viol_type,
                timestamp=timestamp,
                location=camera.location,
                fine_amount=fine_amount,
                status=status,
                confidence_score=round(random.uniform(0.75, 0.99), 2),
                officer_notes="Auto-detected by AI system." if status != "resolved" else "Reviewed and settled."
            )
            db.add(violation)
            db.flush()
            
            # If paid, add a Payment record
            if status == "paid":
                payment = Payment(
                    violation_id=violation.id,
                    amount=fine_amount,
                    payment_date=timestamp + datetime.timedelta(hours=random.randint(1, 48)),
                    transaction_id=f"TXN-{random.randint(100000000, 999999999)}",
                    payment_method=random.choice(["upi", "credit_card", "debit_card"]),
                    status="completed"
                )
                db.add(payment)

        # 8. Notifications
        from backend.app.models import Notification
        mock_notifs = [
            Notification(
                user_id=admin_user.id,
                title="System Boot Completed",
                message="Smart Traffic Violation Detection System (STVDS) is fully configured and online.",
                type="system",
                is_read=True
            ),
            Notification(
                user_id=admin_user.id,
                title="Camera Offline warning: CAM-004",
                message="Critical connection timeout at AIIMS Crossing Main Feed. Diagnostic health marked critical.",
                type="camera",
                is_read=False
            ),
            Notification(
                user_id=admin_user.id,
                title="Official fine policy modified",
                message="Super Admin updated the fine tariff guidelines for Overspeeding to ₹1,000.",
                type="officer",
                is_read=False
            )
        ]
        db.add_all(mock_notifs)

        # Audit logs for seeding
        log = ActivityLog(
            user_id=admin_user.id,
            action="System initialized and seeded mock historical dataset."
        )
        db.add(log)
        db.commit()
        print("Database seeding completed successfully.")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
