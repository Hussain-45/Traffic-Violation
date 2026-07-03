# 📘 STVDS User Operations Manual

This guide describes how to operate the **Smart Traffic Violation Detection System (STVDS)** command panels.

---

## 🔑 1. Authentication Credentials

The seeder initializes two roles by default:
- **👮 Officer Access**:
  - *Username*: `officer`
  - *Password*: `officer123`
  - *Rights*: View CCTV feeds, review violations database, process payments, export logs.
- **🛡️ Admin Access**:
  - *Username*: `admin`
  - *Password*: `admin123`
  - *Rights*: Modify fine rules, edit AI thresholds, add camera streams, delete records, view activity audits.

---

## 📺 2. CCTV Command Room Operations

The **CCTV Command Room** screen contains several custom controls:
1. **Face Blur (Anonymization)**: Toggling this checkbox blurs all driver cockpit faces inside the video canvas to preserve privacy.
2. **Night Vision Mode**: Applies an infrared CSS green-matrix visual lens directly onto the stream player.
3. **Weather Sensor Matrix**: Select from **Sunny**, **Rainy** (falling canvas precipitation lines), or **Foggy** (smog mist overlays).
4. **Road Damage Scanner**: Toggling this highlights structural anomalies (potholes/cracks) in yellow directly over lane coords.
5. **Connection Toggle**: Toggle individual cameras Online/Offline. Offline status triggers a critical connection system notification automatically.

---

## 💳 3. Fine Challan Settlement

To process a violation fee:
1. Navigate to the **Fine Management** page.
2. Search for the target Vehicle Plate or Challan ID.
3. Click **Settle Challan** to open the payment drawer.
4. Select **UPI**, **Debit Card**, or **Cash** and submit the transaction.
5. Click **Print Receipt** to compile and view the official challan receipt containing the time, camera location, offence type, and unique Transaction ID.

---

## 📁 4. AI Media Upload

To run YOLOv8 target classifications on files:
1. Navigate to **AI Media Upload**.
2. Drag and drop traffic images/videos.
3. The AI extracts license plates, maps speeds, runs checks for 8 core violations, checks for stolen vehicle flags, and displays the processed frame.
