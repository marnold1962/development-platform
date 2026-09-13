# devdesk study: what it is, what to keep, how the web version would look

| | |
|---|---|
| **Date** | 2026-09-13 |
| **Purpose** | Study before starting over. Nothing has been built or changed. |
| **Sources** | devdesk docs and DECISIONS (read by the documentation agent), devdesk code and tests (review agent), the Epic Tracker and Dev Planner templates and CSS on the EC2 (infrastructure agent, read-only). |
| **Decision needed** | Section 6: fresh code or keep the core. |

---

## 1. What devdesk is

A personal desktop app for running a development process: a request comes in, gets planned onto a roadmap in a sprint, is built, and is verified. It replaces Epic Tracker and Dev Planner, the two Flask apps on the former employer's AWS box, with no code and no data copied from them. Python, PySide6, one SQLite file under your home directory.

Built 2026-09-11 and 12: fifteen commits, tree clean, 264 tests passing. About 4,300 lines of core, 3,600 of Qt screens, 3,900 of tests.

The one rule that shaped it: the core never imports Qt, and a test enforces that. The core is the whole application; the window is a view over it. That was the plan from the start, "stage 1 is a working CLI with no GUI", and it is exactly what makes a web version cheap.

## 2. The domain, as built

Eleven tables in one migration. The ones that matter:

- **project**: title, business area and value, status (13 values), urgency, effort, priority, archived flag, dates.
- **request**: the intake grain. Kind (bug, enhancement, user story, repository), title, description, steps, url, priority, target repo, submitted by, status (new, in progress, closed), and an orthogonal verify state (pending, passed, failed) with verified by and at.
- **work_item**: the planning grain. One request becomes one or more items. Project, sprint (null means unscheduled), parent for a two-level hierarchy, kind, status (nine values), priority, story points, estimates, seven dates, position. Composite foreign keys stop an item sitting in another project's sprint or under a parent from another project.
- **sprint**: belongs to one project; name, goal, start and end, status, environment (dev, cert, prod).
- **comment** and **attachment**: each owned by exactly one of request, work item or project. Attachments are content-addressed blobs on disk, named by hash.
- **activity**: append-only log, enforced by trigger. **document**: research notes and SQL. **setting**.

Deliberate differences from the two originals, each recorded with its reason in DECISIONS: a real foreign key instead of a doubly-stored cross-link; null instead of reserved sprint rows 997 to 999; two unused columns dropped; stored statuses are identifiers, labels live in one vocabulary file; rows instead of JSON arrays; no users table, single user, no login.

## 3. The workflow, as built

Table-driven, one mutator. Request status runs new, in progress, closed, and can reopen. Verify state runs pending, passed, failed, and failed can redispatch. The actions: send to planner (creates a work item, moves the request to in progress), decline, ready to verify, verify passed, verify failed, redispatch, close, reopen.

Verification is the piece that ties the two grains together: when the last open work item for a request is marked done, the request's verify state becomes pending in the same transaction, and a human then says works or broken.

The CLI covers all of it: init, status, check, log, project, request, item, doc, backup, import, export, report, gc. The import loads a JSON dump of the original data, id-preserving, with the two originals' known defects kept on purpose. Nothing in the repo produces that dump.

## 4. Known gaps

- Marking an item done from the roadmap grid bypasses the verification hook; only the CLI path fires it. Pinned by a test as intended, but it means the "unlosable callback" is losable from the GUI.
- The settings dialog is not reachable from any menu.
- A `pending_attachment` table exists outside the schema list, so status, check and backup ignore it.
- The docs never list the full state sets; the code does. The only spec is the placeholder. There is no change history file.
- Document search is a plain LIKE.
- No CLI for sprints, comments or attachments.

## 5. The look you like, distilled

Both web apps are server-rendered Jinja with vanilla JavaScript, light theme, full-width pages, and colour used only in badges. Epic Tracker is custom CSS with Inter; Dev Planner is Bootstrap 5 with a large override sheet. The style guide below is what a new Flask and HTMX app follows to look like them.

1. Font Inter 400 to 700; body 0.875 to 0.9rem; monospace 0.78rem for identifiers.
2. Page background `#f8f9fb`, surfaces white, text `#1e293b`, secondary `#64748b`, muted `#94a3b8`, borders `#e2e8f0`, inputs `#cbd5e1`.
3. Header: dark navy gradient `#0f1720` to `#1e3a5f`, 14px by 32px padding, white bold brand, links `#cbd5e1`.
4. Full-width content with 24px by 32px padding; forms capped near 760px.
5. Cards white, 1px `#e8eaed`, 12px radius, 24px padding, at most a 1px shadow.
6. Tables fixed layout; header `#f1f5f9`, uppercase 0.7rem letter-spaced `#475569`; body 0.85rem, 12px padding, hairline rows, hover `#f8fafc`, no striping; sticky header on long grids; sort and filter in the header.
7. Badges are 999px pills, 0.7rem semibold, soft tint with dark text, never solid, except one amber alert `#f59e0b`.
8. Status colours: new or planned amber `#fef3c7` on `#92400e`; in progress blue `#dbeafe` on `#1e40af`; testing purple `#f1ebfa` on `#59359a`; done green `#dcfce7` on `#166534`; blocked or failed red `#fef2f2` on `#b91c1c`; hold yellow `#fff8e1` on `#997404`; neutral `#f1f5f9` on `#475569`. Environments: dev `#e7eefb`, cert `#fdf1dc`, prod `#e2f2e7`.
9. Primary button `#1e3a5f`, hover `#1e40af`, white text, 8px radius; secondary white with `#cbd5e1` border; danger white with `#b91c1c` text.
10. Inputs 10px by 12px, 8px radius, focus `#3b82f6` with a 3px ring; labels uppercase 0.78rem; choice fields as radio pills.
11. Filters as segmented pill groups, active `#1e3a5f`.
12. Inline grid editing: cells transparent until hover, dirty `#fff3cd`, saved flash `#b7ecc8`, a fixed bottom-right saving pill.
13. Toasts top-right, solid green or red, gone in three seconds; empty states a dashed box with one call to action.
14. Destructive controls hidden until row hover, confirm before delete.
15. Emoji or inline SVG icons; spacing scale 4, 8, 12, 16, 24px.

The screens they organise: an Inbox table with pill filters above and select filters in the header, ranked rows tinted; an edit page with a dark back banner and contextual status cards; a Dashboard of stat tiles over three cards; a Roadmap of one card per sprint with an inline-editable header and a fixed-width grid with frozen first columns; a project detail page of click-to-edit fields with a notes thread.

## 6. The decision: fresh code, or keep the core

Two honest options.

**A. Start over entirely.** New Flask project from the platform template, new schema written from section 2, new services, new tests. Two to three weeks. You get a clean second design, and you rewrite 4,300 lines that were written two days ago and already pass 264 tests.

**B. Keep the core, replace the window.** New Flask project from the platform template, with devdesk's `core` package brought in unchanged: schema, migrations, repositories, services, states, vocabulary, backup, import, export, CLI. The web screens are written fresh in the style above, and the Qt screens are not carried over. About one week. The core was built for exactly this; the no-Qt rule exists so that a different front end could sit on it. The four gaps in section 4 get fixed on the way: the grid's status edit goes through the workflow mutator, settings get a page, `pending_attachment` joins the schema list, and the state sets get written into a spec.

I recommend B. It honours "start over" where it matters, the part you look at, and it does not throw away the part that is already correct and tested. It also means the same SQLite file and the same CLI keep working, so nothing you have entered is lost.

## 7. What the web version would be, under option B

- **Name and place.** A new platform project, kind service, created with `dev new flask as2`. Suggested name `devdesk-web`, or `devdesk` if the desktop app is retired.
- **Stack.** Flask, Jinja, HTMX, the style guide in section 5, SQLite through the existing core. Single user, no login, reached through the platform router and the ssh tunnel like everything else on AS2.
- **Data.** The SQLite file and blobs live on AS2 under the platform's deploy root, mounted read-write into the container. The core's backup command runs on a timer instead of at window start.
- **Screens, in build order.** Inbox with actions. Request detail and edit. Dashboard. Projects. Roadmap grid with inline editing over HTMX, the hardest screen and the one to do last. Documents. Sprints and settings as pages, not dialogs.
- **What is not built.** Nothing that reads or writes the two original apps. Nothing that needs a second user.

## 8. Open questions for you

1. Option A or B.
2. Does the desktop app keep running alongside for a while, on the same database file, or is it retired when the web version reaches parity?
3. Where does the database live day to day: on AS2 behind the router, or on the laptop with the web app run locally? The platform supports both; the answer decides whether `make run` or `dev deploy dev` is the daily path.
4. Is the imported original data needed in the web version from day one, or can it be re-imported later with the same dump?
