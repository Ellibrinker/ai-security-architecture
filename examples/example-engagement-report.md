---
title: Example Engagement Report (Anonymized)
note: >
  This report accompanies examples/security_model.example.json. It is a
  worked example showing how the methodology in docs/METHODOLOGY.md is
  applied in practice. Organization names, user identities, and the target
  URL are placeholders; the structure, statuses, and evidence descriptions
  mirror a real two-tenant document-collaboration SaaS engagement.
---

# Example Engagement: ExampleTeamDocs

**Target:** `https://example-teamdocs-app.test/` (placeholder)
**App type:** Team document-collaboration SaaS with organizations (tenants),
roles (Member / Admin), and shared documents.

## Scope and authorization

- Owner-authorized black-box exploration plus non-destructive active
  validation.
- Two owner-supplied test accounts were used: one **Member** in
  **Organization A**, one **Admin** in **Organization B**.
- No destructive actions were performed. No ID-enumeration was attempted
  against any tenant other than the two authorized organizations.

## Architecture summary

**Actors:** Anonymous visitor, Member (role-scoped to one org), Admin
(role-scoped to one org; adds Team/Invitations management over Member).

**Resources:** Document (title, body, author, org, created date; tenant
scoped), Team roster entry (tenant scoped), Invitation (tenant scoped).

**Relationships:** Document ownership (one author per document), user→org
membership (each tested account belonged to exactly one org), and tenant
boundaries on documents and rosters.

## Key authorization rules (atomic)

| Actor | Resource | Action | Condition | Effect | Status |
|---|---|---|---|---|---|
| Member | Document | Read | same org, any author | allow | OBSERVED |
| Member | Document | Create | own org | allow | OBSERVED |
| Member | Document | Update | own document | allow | OBSERVED |
| Member | Document | Update | same org, **not** own document, direct URL access | deny | CONFIRMED |
| Admin | Document | Read | **different org** (cross-tenant), direct ID access | deny | CONFIRMED |
| Admin | Document | Update | **different org** (cross-tenant), direct URL access | deny | CONFIRMED |
| Member | Invitation | Administer | direct `/invitations` URL access | deny | CONFIRMED |
| Admin | Invitation | Invite | own org | allow | OBSERVED (modal reachable; submission not exercised) |
| Member | Document | Delete | any | unknown | UNRESOLVED (no delete control found in the UI for any role) |

See `examples/security_model.example.json` for the full atomic rule set,
including conditions, confidence, and evidence pointers.

## Security invariants (evidence-scoped)

1. *A Member can read any document within their own organization, regardless
   of who authored it.* — `OBSERVED`
2. *A Member may only update a document they personally authored.* —
   `CONFIRMED` (actively tested: direct-URL edit of another member's document
   was rejected server-side, and the content was verified unchanged
   afterward)
3. *Documents belonging to one organization cannot be read or updated by an
   actor from a different organization.* — `PARTIALLY_CONFIRMED` (confirmed
   for one tenant direction; the reverse direction was not tested)
4. *Only Admin-role users may administer organization invitations; this is
   enforced server-side, not merely hidden in the UI.* — `PARTIALLY_CONFIRMED`
   (Member denial was actively confirmed; Admin's ability to actually
   complete an invitation end-to-end was not tested)

## Notable finding: UI/route hygiene gap (not a vulnerability)

Navigating directly to a document's edit URL when the current user cannot
actually modify that document (wrong author, or wrong tenant) renders an
edit-form shell instead of an immediate "not found" / "not authorized"
response — unlike the view route, which does return a clean not-found
response in the cross-tenant case. In every case tested, the underlying
**save** was still rejected server-side and produced no persisted change.
This is a low-severity UX / defense-in-depth gap (the route reveals its own
existence and, for same-tenant non-owned documents, pre-fills real content
into a form that cannot ultimately be saved) rather than a confirmed
authorization bypass.

## Coverage gaps

- No stateful resource/workflow (e.g. draft → published, invitation
  pending → accepted → revoked) was identified or tested.
- Cross-tenant isolation was tested in only one direction; the reverse
  direction was not exercised.
- Admin-vs-other-member-in-the-same-org document editing was never testable
  (the available Admin-accessible tenant had only one member).
- Whether a Delete action exists at all, for any role, remains unresolved —
  no delete control was found anywhere in the UI during this engagement.
- The Invite flow was observed as reachable but not submitted, so acceptance
  and resulting role assignment were never validated end-to-end.

## Conclusion

Every actively tested authorization hypothesis — ownership-based document
write control, cross-tenant document read/write isolation, and role-gated
admin routes — was **rejected** (the suspected gap did not exist): the
backend independently enforces these checks regardless of what the frontend
UI shows or hides. The only validated finding is the low-severity UI/route
hygiene gap described above.
