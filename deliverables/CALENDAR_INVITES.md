# Calendar invites (.ics) — Closing Agent Manufacturing

**Contact:** James Gallagher · 610-393-1102 · Jgallagher10@gmail.com  
**Company:** Industrial and Molecular Solutions / PTC Inc  
**Timezone:** America/Tijuana (PT) for display; ICS event times are stored/emitted in UTC (`Z`)  
**Date:** 2026-09-24 PT

---

## What this does

When you **Schedule** a meeting in Closing Agent:

1. The meeting is saved (status `Scheduled`, approval `pending` like before).
2. An **invite email draft** is created automatically (`status=Draft`, `approval_status=pending`) and linked via `emails.meeting_id`.
3. A standards **`.ics`** calendar file can be downloaded anytime from the meeting card or `GET /meetings/{id}/ics`.

Nothing is auto-sent. Approving and **Mark Sent** only updates status in Closing Agent — it does **not** deliver real email or push to Google Calendar.

---

## How James uses it (dashboard)

1. Open **Meetings** → **Schedule Meeting** (pick contact, title, date/time, duration, location).
2. Toast: *Meeting scheduled — invite draft sent to Approvals*.
3. On the meeting card:
   - **Download .ics** — save the invite and open it in Outlook / Google Calendar / Apple Calendar.
   - Invite approval pill / status line shows if the draft is still pending.
4. Open **Approvals** → review the invite email (and the meeting itself) → **Approve**.
5. Open **Emails** → **Mark Sent** when you have actually sent the invite from your mailbox (optional tracking step).

### Opening the `.ics`

| App | How |
|-----|-----|
| **Outlook** | Double-click the `.ics` or File → Open → Calendar |
| **Google Calendar** | Settings → Import & export → Import, or open the file and choose Google Calendar |
| **Apple Calendar** | Double-click the `.ics` (macOS/iOS) |

Organizer is always James Gallagher (`Jgallagher10@gmail.com`). Attendee is the contact email when present.

---

## NDA gate

Invite copy reuses the same NDA check as outreach (`_contact_nda_signed`):

- **No signed NDA:** subject/body frame the call as **discovery / Mutual NDA only**. No specs, drawings, or pricing. Agenda generation already forces an NDA-first bullet.
- **NDA signed:** normal technical-fit invite language is allowed (optional AI polish when API keys are set; template fallback otherwise).

---

## API summary

| Method | Path | Notes |
|--------|------|--------|
| `POST` | `/meetings` | Creates meeting + pending invite email. Response includes `id`, `agenda`, `email_id`, `ics_url`. |
| `GET` | `/meetings` | Includes `ics_url`, `invite_email_id`, `invite_approval_status`, `invite_email_status`. |
| `GET` | `/meetings/{id}/ics` | `text/calendar` attachment `{safe_title}.ics` |
| `GET` | `/meetings/{id}/invite` | JSON: `ics` text + suggested subject/body / linked `email_id` |

ICS fields: `UID` = `{meeting_id}@closing-agent`, `METHOD:REQUEST`, `STATUS:CONFIRMED`, `DTSTART`/`DTEND` UTC `Z`, `ORGANIZER`, optional `ATTENDEE`, `LOCATION`, `DESCRIPTION` (agenda + organizer contact).

---

## Follow-ups (not in this change)

- Google Calendar API sync / free-busy
- Actually attaching the `.ics` bytes to a real outbound SMTP/Gmail send
- Recurrence (`RRULE`) and updates (`SEQUENCE` / `METHOD:CANCEL`)

