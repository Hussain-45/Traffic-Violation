# Optimized Git Branching & Contribution Workflow

This document defines the branching strategy, commit conventions, versioning milestones, and release workflows for the **Traffic Violation AI** project, optimized for long-term maintainability.

---

## 1. Branching Strategy & Lifecycle Policy

The repository maintains a strict branching policy to optimize collaboration and keep the repository history clean.

### Permanent Branches

- **`main`**: Production branch. Contains code verified as stable and ready for deployment. Directly tagged with release versions (e.g. `v1.0.0`).
- **`develop`**: Integration branch. All features are merged here for testing. Serves as the pre-production staging branch.

### Temporary Feature Branches (Future Policy)

All feature branches are **temporary**. They must exist only during the development lifecycle of their specific module and must be deleted immediately after a successful merge.

#### Benefits of Temporary Feature Branches
- **Cleaner Repository**: Prevents clutter from dozens of inactive or abandoned branches.
- **Easier Maintenance**: Reduces overhead when tracking outstanding tasks.
- **Fewer Stale Branches**: Eliminates the risk of developers pulling and working on outdated code.
- **Better Collaboration**: Promotes clear handoffs and visibility into active features.
- **Reduced Merge Conflicts**: Encourages short-lived branches that stay closely aligned with `develop`.

#### Step-by-Step Command Workflow

```bash
# 1. Update your local develop branch to match origin
git checkout develop
git pull origin develop

# 2. Spin off a new temporary feature branch
git checkout -b feature/<feature-name>

# 3. Implement, verify, and commit your changes
# (Make commits following conventional commit rules)
git add .
git commit -m "feat(<scope>): add description"

# 4. Push branch and open a Pull Request to merge into develop
git push origin feature/<feature-name>

# 5. After the PR is approved, squash-merged, and verified:
# Switch back to develop and pull the latest changes
git checkout develop
git pull origin develop

# 6. Delete the local temporary feature branch
git branch -d feature/<feature-name>

# 7. Delete the remote temporary feature branch
git push origin --delete feature/<feature-name>
```

---

## 2. Concrete Branch Lifecycle Examples

Each branch should exist only while the feature is under active development.

- **Step 9 — Seat Belt Detection**:
  - Branch: `feature/seatbelt-detection`
  - Lifecycle: Created before starting Step 9, and deleted immediately after merge to `develop` passes integration verification.
- **Step 10 — Mobile Phone Detection**:
  - Branch: `feature/mobile-phone-detection`
  - Lifecycle: Created before starting Step 10, deleted immediately after merge.
- **Step 11 — Traffic Light Detection**:
  - Branch: `feature/traffic-light-detection`
  - Lifecycle: Created before starting Step 11, deleted immediately after merge.

---

## 3. Merge Strategy

The flow of code moves strictly through the following pipeline:

```
Feature Branch (feature/*) ──> develop ──> Staging/Testing ──> main
```

> [!IMPORTANT]
> **Merge Restriction**: Never merge feature branches directly into `main`. All code changes must go through the staging validation loop in `develop` first.

---

## 4. GitHub Protection Recommendations

To maintain repository integrity, the following GitHub branch protection rules are recommended for team environments:

- **Protect `main` and `develop` branches**:
  - Block force pushes (`git push --force`).
  - Prevent deletion of these branches.
- **Require Pull Requests before merging**:
  - Direct commits to `main` and `develop` should be disabled.
- **Require successful verification**:
  - All status checks (such as unit test runs) must pass before a PR can be merged.
- **Require Reviews**:
  - Require at least one review approval from code owners.

---

## 5. Continuous Integration (CI) Activation Path

- **Workflow Status**: GitHub Actions (defined in `.github/workflows/ci.yml`) is currently in **placeholder mode**.
- **CI Activation Recommendation**: Do **NOT** enable active CI pipelines until the following core modules are stable and verified:
  1. Backend API
  2. Frontend Dashboard
  3. Testing Suite
  4. SQLite/PostgreSQL Database Integration
  5. Email Notification Automation
- *Rationale*: Enabling CI checks before core framework layers are fully stable leads to build noise and unnecessary action usage.

---

## 6. Commit Message Convention

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

## 7. Versioning & Release Milestones

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
