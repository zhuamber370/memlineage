> Documentation Status: Confirmed Design
> Last synced: 2026-03-04

# Home Database Backup/Restore UI Design (v1)

Date: 2026-03-04
Status: Confirmed
Scope: Home dashboard UI + interaction design only (no implementation code in this document)

## 1. Context

Current MemLineage UI has no direct operator entry for runtime database backup/restore.
For local-first operations, users need a simple and explicit control point from Home.

Confirmed product direction in this design session:
1. Entry stays on Home page (no standalone backup page).
2. Backup output is download-only to local machine (no server-side retention list).
3. Restore input is local file picker upload.
4. Restore mode is direct overwrite of current database.

## 2. Product Goal

Provide a compact, low-frequency operations panel on Home that allows users to:
1. Download a fresh database backup file locally in one click.
2. Restore database from a selected local backup file.
3. Understand the overwrite risk before restore execution.

## 3. Confirmed Boundaries

1. This phase only designs and delivers UI/UX for backup and restore.
2. No backup history browser in UI.
3. No scheduled or automatic backup in this phase.
4. No pre-restore preview/diff in this phase.
5. Restore is immediate overwrite after explicit confirmation.

## 4. Non-Goals

1. Cloud object storage backup sync.
2. Multi-version server retention policy.
3. Cross-environment migration assistant.
4. Data-level selective restore.

## 5. Information Architecture

Placement:
- Home page adds one new card section: `Database Safety`.

Card structure:
1. Header area
   - Title: `Database Safety`
   - Subtitle: `Backup download and direct restore (overwrite current DB).`
2. Two action zones in one card
   - Left: `Backup`
   - Right: `Restore`

Desktop layout:
- Two-column split inside the card (`Backup | Restore`).

Mobile layout:
- Single-column stacked blocks (`Backup` above `Restore`).

## 6. Interaction Design

### 6.1 Backup Flow

Controls:
- Primary button: `Create Backup & Download`

Behavior:
1. User clicks button.
2. Button enters loading state (`Backing up...`) and disables repeat click.
3. On success:
   - Browser starts file download immediately.
   - Show success note with `filename / size / timestamp` if available.
4. On failure:
   - Show inline error message.
   - Button returns to enabled state.

### 6.2 Restore Flow

Controls:
- File picker button/input: `Choose Backup File`
- Readonly selected file summary: `name / size / modified`
- Risk acknowledgment checkbox:
  - `I understand this will overwrite current data.`
- Danger button: `Restore Now`

Enable rules:
- `Restore Now` is enabled only when:
  1) one file is selected, and
  2) acknowledgment checkbox is checked, and
  3) no restore request is running.

Execution behavior:
1. User clicks `Restore Now`.
2. Browser confirmation dialog appears:
   - `Confirm restore? This will overwrite current database and cannot be undone.`
3. If canceled: no request sent.
4. If confirmed:
   - Enter loading state (`Restoring...`)
   - Disable restore controls until completion.
5. Success:
   - Show success notice (`Restore completed`).
   - Provide optional hint: `Please refresh task/knowledge/changes pages.`
6. Failure:
   - Show inline error with backend message mapping.

## 7. Visual and Copy Guidelines

Tone:
- Operational, explicit, low-ambiguity.

Color semantics:
1. Backup action uses normal primary button style.
2. Restore action uses danger-emphasis style.
3. Warning text under restore uses danger color token.

Required warning copy (always visible in Restore block):
- `Restore will overwrite the current database immediately.`

I18n keys to add (planned):
- `home.dbSafety.title`
- `home.dbSafety.subtitle`
- `home.dbSafety.backup.title`
- `home.dbSafety.backup.action`
- `home.dbSafety.backup.running`
- `home.dbSafety.backup.success`
- `home.dbSafety.backup.failed`
- `home.dbSafety.restore.title`
- `home.dbSafety.restore.pickFile`
- `home.dbSafety.restore.selectedFile`
- `home.dbSafety.restore.warn`
- `home.dbSafety.restore.ack`
- `home.dbSafety.restore.action`
- `home.dbSafety.restore.running`
- `home.dbSafety.restore.confirm`
- `home.dbSafety.restore.success`
- `home.dbSafety.restore.failed`

## 8. State Model (UI)

Backup state:
- `idle`
- `running`
- `success`
- `error`

Restore state:
- `idle`
- `ready` (file selected + ack checked)
- `running`
- `success`
- `error`

Shared constraints:
1. Backup and restore actions are independent.
2. During restore running, restore controls are locked.
3. During backup running, backup trigger is locked.

## 9. Error Handling

Error classes surfaced in UI:
1. Network/API unavailable.
2. Invalid backup file format.
3. Restore rejected by backend validation.
4. Server-side I/O failure.

Display policy:
- Show concise human message plus optional detail line.
- Keep message local to the action zone (backup errors in backup block, restore errors in restore block).

## 10. Accessibility and UX Safety

1. All controls keyboard accessible.
2. Loading and result messages announced with semantic status text.
3. Danger button has explicit text (no icon-only affordance).
4. Confirmation is text-based and contains overwrite wording.
5. File picker accepts explicit backup extension pattern when available.

## 11. Acceptance Criteria

1. Home page renders `Database Safety` card without requiring route changes.
2. Backup button triggers downloadable file flow and shows running/success/error states.
3. Restore requires both file selection and acknowledgment before enable.
4. Restore always asks final confirmation before request.
5. Restore success and failure both produce clear inline feedback.
6. UI remains usable on desktop and mobile breakpoints.
7. Existing Home task/knowledge interactions remain unaffected.

## 12. Risks and Mitigations

1. Risk: accidental destructive restore.
   - Mitigation: checkbox + final confirm dialog + danger styling + explicit warning copy.
2. Risk: user selects wrong file.
   - Mitigation: selected file summary visible before submit.
3. Risk: large file upload delay appears frozen.
   - Mitigation: explicit running text and disabled controls while restoring.

## 13. Rollout

1. Implement UI card and local state handling on Home.
2. Wire to backend backup/restore endpoints.
3. Verify end-to-end with local backup file generation and restore cycle.
4. Update release notes and operator docs after acceptance.
