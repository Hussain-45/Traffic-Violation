# 📡 REST API Documentation

The backend exposes a structured API with JWT Bearer Token authentication. All paths are prefixed with `/api/v1`.

---

## 🔒 1. Authentication Router (`/auth`)

### `POST /auth/login`
- **Description**: Authenticate credentials and fetch JWT access token.
- **Content-Type**: `application/x-www-form-urlencoded`
- **Payload**:
  ```json
  { "username": "admin", "password": "password" }
  ```
- **Response**:
  ```json
  {
    "access_token": "ey...",
    "token_type": "bearer",
    "role": "admin",
    "full_name": "Super Admin"
  }
  ```

---

## 🚦 2. Violations Router (`/violations`)

### `GET /violations`
- **Description**: Advanced search and filter query.
- **Parameters**: `page`, `limit`, `sort_by`, `status`, `type`, `location`, `start_date`, `end_date`.
- **Response**:
  ```json
  {
    "items": [
      {
        "id": 1,
        "type": "red_light_jump",
        "location": "Connaught Place",
        "fine_amount": 2000.0,
        "status": "pending",
        "timestamp": "2026-07-02T12:00:00"
      }
    ],
    "total": 1, "page": 1, "pages": 1
  }
  ```

### `POST /violations/upload`
- **Description**: Process media file upload (YOLOv8 + OCR inference + DB commit).
- **Content-Type**: `multipart/form-data`
- **Parameters**: `file`, `camera_id`
- **Response**:
  ```json
  {
    "success": true,
    "violations_count": 1,
    "ai_result": {
      "detected_image_path": "data/uploads/images/...",
      "vehicles": [{ "plate": "DL3CAB9081", "is_stolen": false, "speed": 45.0 }],
      "accident_detected": false
    }
  }
  ```

---

## 💳 3. Fine challan Management (`/fines`)

### `POST /fines/{violation_id}/pay`
- **Description**: Process challan settlement transaction.
- **Payload**:
  ```json
  { "amount": 1000.0, "payment_method": "upi" }
  ```
- **Response**:
  ```json
  { "success": true, "transaction_id": "TXN-9081", "status": "completed" }
  ```

---

## 🔔 4. Notifications Router (`/notifications`)

### `GET /notifications/unread-count`
- **Response**:
  ```json
  { "count": 3 }
  ```
