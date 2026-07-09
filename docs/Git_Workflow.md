# Git Branching & Contribution Workflow

This document defines the branching strategy, commit conventions, versioning milestones, and release workflows for the **Traffic Violation AI** project.

---

## 1. Branching Strategy

The repository utilizes a structured git branching strategy to ensure stability and code quality.

### Permanent Branches

- **`main`**: Production branch. Contains code verified as stable and ready for deployment. Directly tagged with release versions (e.g. `v1.0.0`).
- **`develop`**: Integration branch. All features are merged here for testing. Serves as the pre-release staging branch.

### Feature Branches

Created for developing individual modules or capabilities. Branched from `develop` and merged back into `develop`.

- **Naming Convention**: `feature/<module-name>`
- **Project Feature Branches**:
  - `feature/camera`
  - `feature/vehicle-detection`
  - `feature/vehicle-tracking`
  - `feature/pipeline-manager`
  - `feature/helmet-detection`
  - `feature/seatbelt-detection`
  - `feature/mobile-phone-detection`
  - `feature/traffic-light-detection`
  - `feature/wrong-side-detection`
  - `feature/triple-riding`
  - `feature/number-plate-detection`
  - `feature/ocr`
  - `feature/violation-engine`
  - `feature/evidence-generator`
  - `feature/database`
  - `feature/email-automation`
  - `feature/dashboard`
  - `feature/reports`
  - `feature/deployment`

---

## 2. Branch Protection & Merging Strategy

### Merges into `main`

- **Source Branch**: Must merge only from `develop` via a Pull Request.
- **Merge Requirements**:
  1. Successful unit test pass (`pytest` runs must complete with 0 failures).
  2. Verified code builds (no syntax or compilation errors).
  3. No merge conflicts.
  4. Fully reviewed and signed off by code owners.

### Merges into `develop`

- **Source Branch**: Feature branches (e.g., `feature/helmet-detection`).
- **Merge Strategy**: **Squash and Merge**. This flattens the commit history of a feature into a single clean commit on `develop`.
- **Merge Requirements**:
  - Pull Request template fully populated.
  - Passes code review.
  - Manual verification completed.

---

## 3. Commit Message Convention

Commits follow the **Conventional Commits** standard:

`type(scope): description`

### Types

- **`feat`**: A new feature (e.g., `feat(camera): add live camera streaming`)
- **`fix`**: A bug fix (e.g., `fix(yolo): resolve reconnect latency`)
- **`docs`**: Documentation changes (e.g., `docs(api): update endpoints`)
- **`refactor`**: Code changes that neither fix bugs nor add features (e.g., `refactor(pipeline): simplify registry`)
- **`test`**: Adding or modifying tests (e.g., `test(helmet): add test case for overlap matching`)

### Scopes

Must correspond to major scopes: `camera`, `vehicle`, `tracking`, `helmet`, `seatbelt`, `phone`, `signal`, `ocr`, `email`, `database`, `ui`, `pipeline`.

---

## 4. Versioning & Release Strategy

The project follows semantic versioning (`vMajor.Minor.Patch`) mapped to the following project milestones:

| Version | Milestone Description |
| :--- | :--- |
| **`v0.1.0`** | Base architecture & folders structure complete |
| **`v0.2.0`** | Camera feeds & raw YOLO detection pipeline |
| **`v0.3.0`** | Multi-object tracking and Pipeline Manager integration |
| **`v0.4.0`** | Helmet Detection module completed |
| **`v0.5.0`** | Seat Belt Detection module completed |
| **`v0.6.0`** | Mobile Phone Detection module completed |
| **`v0.7.0`** | Number Plate Detection module completed |
| **`v0.8.0`** | License Plate Text Recognition (OCR) completed |
| **`v0.9.0`** | Centralized Violation decision engine & reports completed |
| **`v1.0.0`** | Complete system deployment and release |
