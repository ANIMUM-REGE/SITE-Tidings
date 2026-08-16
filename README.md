# Tidings — site

> Marketing and support site for Tidings: Birthdays & Occasions.

Static site for the app in [`APP-Occasions`](https://github.com/ANIMUM-REGE/APP-Occasions).
Part of the Perpetua app fleet (`VNTR-Perpetua`).

## Hosting

Served at **[tidings.family](https://tidings.family)** via GitHub Pages (`CNAME` committed at the repo root).

## Pages

- `index.html`
- `privacy.html`
- `support.html`
- `sms-opt-in.html`
- `privacy_label.json`

## App status

Tidings is ✅ live on both the App Store and Google Play.

> Status drifts — **re-verify rather than trust this line.**
> `VNTR-Perpetua/company/state/app-fleet-status-2026-08-15.md` (as verified 2026-08-15)
> carries the fleet-wide picture and the method to re-derive it.

## SMS compliance

`sms-opt-in.html` is the carrier-facing opt-in disclosure for the Tidings sender (`+1 833 895 4577`). It is a **compliance artifact**, not marketing — A2P registration references it. Do not remove or relocate it without checking the sender's registration.

## Editing

Plain HTML, no build step — edit and commit. Keep privacy/support URLs stable: they
are referenced from live App Store and Play listings, and a broken support URL is a
review-rejection trigger.
