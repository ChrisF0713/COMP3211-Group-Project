# Software Requirements Specification — Personal Information Management (PIM) System

**COMP3211 Software Engineering, Fall 2026 — Group Project**
**Group:** `[GROUP NAME — TODO]` · **Members:** `[NAMES + STUDENT IDS — TODO]`

> [!warning] Placeholders to fill before submission
> Group name, member names/IDs, and the version-history author column are marked
> `[TODO]`. Everything else is complete. Convert this file to DOCX or PDF before
> zipping (Deliverable 1 requires DOC/DOCX/PDF).

---

## 1. Preface

### 1.1 Intended readers

This specification is written for three audiences:

- **The assessors (course instructor and demonstrators)**, who need to judge the validity, consistency, completeness, realism and verifiability of the requirements.
- **The developers of the system** (the group members), who derive the design document, the implementation and the unit-test plan from this document.
- **End users** — a person managing their own notes, tasks, events and contacts from a command line — who need to know what the system promises to do. Section 4 is deliberately written in client-readable language for this audience.

Readers are assumed to have read the course project description; knowledge of the implementation is *not* assumed.

### 1.2 Version history

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-11-16 | `[TODO]` | First complete draft covering US1–US11 |
| 1.0 | `[TODO]` | `[TODO]` | Baseline submitted with the deliverables |

---

## 2. Introduction

### 2.1 Need

Personal information today is scattered across loose text files, phone note apps and paper scraps. A user who wants to record a fleeting idea, a to-do with a deadline, a scheduled meeting with an alarm, or a friend's phone number has no single place where all of these live together, are searchable, and survive across sessions. The system exists to fill that gap: **one command-line tool in which all personal information records are created, browsed, searched, kept up to date, and stored for later use.**

### 2.2 Scope

**In scope.** The system is an interactive, menu-driven command-line application that:

- creates four kinds of personal information records (PIRs): plain-text notes, tasks, events and contacts (US1–US5);
- modifies, displays and deletes existing PIRs (US6, US8, US9);
- searches PIRs by type, by text, by time, and by logical combinations of these tests (US7);
- saves all PIRs to, and loads all PIRs from, a file with the `.pim` extension (US10, US11).

**Out of scope.** The system deliberately excludes:

- any graphical or web front end, and any online or multi-user capability (the project brief explicitly discourages additional features and grants no extra credit for them);
- concurrent editing, synchronisation between devices, or import from formats other than `.pim`;
- rich formatting inside record fields — every field is plain text, with timestamps in one fixed format.

**Fit.** The system is a personal productivity tool for a single user on one machine. It fits that "organisation" (the individual user's workflow) by being available wherever a console is available, storing everything in one portable file, and asking for no installation beyond a Python interpreter.

### 2.3 Overall description (brief)

The system follows the Model-View-Controller structure described in Section 5. All rule-bearing logic — field validation, search evaluation, file parsing — lives in the model, which is what Deliverable 4's unit tests exercise directly.

---

## 3. Glossary

| Term | Definition |
|---|---|
| **PIR** | Personal Information Record — one stored item (a note, task, event or contact), uniquely identified by an 8-character ID. |
| **PIM** | Personal Information Management — the domain of the system. |
| **Record type** | One of the four PIR kinds: `Note`, `Task`, `Event`, `Contact`. |
| **Text field** | A PIR field holding free text, searchable by "contains": `content` (Note), `description` (Task, Event), `name`, `address`, `mobile_number` (Contact). |
| **Time field** | A PIR field holding a timestamp, searchable by comparison: `deadline` (Task), `starting_time`, `alarm` (Event). |
| **Timestamp** | A point in time written exactly as `YYYY-MM-DD HH:MM`, e.g. `2026-11-20 18:00`. The only accepted format. |
| **Criterion** | A predicate over one PIR, built from the tests in US7 and the logical connectors `&&`, `||`, `!`. Defined formally in Section 6.4. |
| **`.pim` file** | A UTF-8 JSON file storing an ordered collection of PIRs (format in Section 6.6). |
| **MVC** | Model-View-Controller — the architectural pattern the system instantiates. |
| **Model** | The part of the system that owns data and rules and knows nothing about console input/output; it lives in the `model` package. |
| **shall / should** | `shall` marks a mandatory requirement; `should` marks a desirable one. Every use in this document follows that convention. |

---

## 4. User requirements definition

This section states what the system must do for its user, in client-readable language. Each numbered requirement is traced to the user stories in Appendix B of the project description; the detailed, testable form of every requirement is in Section 6.

### 4.1 Services

| ID | Requirement | Traces to |
|---|---|---|
| UR-1 | The system **shall** let the user create four kinds of PIRs — notes, tasks, events and contacts — each with the fields the user story names, in one menu-driven flow. | US1 |
| UR-2 | The system **shall** let the user create a note consisting of free text. | US2 |
| UR-3 | The system **shall** let the user create a task consisting of a description and a deadline. | US3 |
| UR-4 | The system **shall** let the user create an event consisting of a description, a starting time and an alarm time. | US4 |
| UR-5 | The system **shall** let the user create a contact consisting of a name, an address and a mobile number. | US5 |
| UR-6 | The system **shall** let the user change any one field of any existing PIR, identified by its ID. | US6 |
| UR-7 | The system **shall** let the user search PIRs with a criterion combining text-contains tests, time comparisons (`<`, `>`, `=`), record-type tests, and the connectors `&&`, `||`, `!`, with nesting. | US7 |
| UR-8 | The system **shall** let the user print the details of one specific PIR or of all PIRs. | US8 |
| UR-9 | The system **shall** let the user delete a specified PIR. | US9 |
| UR-10 | The system **shall** let the user store all PIRs in a file with the `.pim` extension. | US10 |
| UR-11 | The system **shall** let the user load PIRs from a `.pim` file and continue working with them. | US11 |

### 4.2 Non-functional user requirements

| ID | Requirement |
|---|---|
| UR-12 | The system **shall** keep every record safe from bad input: a mistake in typing a value, an ID or a filename must never corrupt stored data or crash the session. |
| UR-13 | The system **shall** feel responsive for a personal collection: any single operation on up to a thousand records completes within a second. |
| UR-14 | The system **shall** be usable from any console with no installation beyond a Python interpreter, using only the Python standard library. |

---

## 5. System architecture

The system is organised as **Model-View-Controller (MVC)**, instantiated as three Python packages plus a thin bootstrap script:

```text
main.py          bootstrap: wires the three layers, runs the loop
controller/      AppController: menu selection → one model operation → view output
view/            ConsoleView: every byte to or from the console
model/           the system model: record types, criteria, repository, .pim I/O
```

The dependency direction is one-way: **controller → model** and **controller → view**; the model imports neither of the other two. This is what makes the model unit-testable in isolation (Deliverable 4) and lets the presentation be replaced without touching the rules.

**Reused components.** The system reuses the Python standard library and nothing else: `json` (file format), `uuid` (record IDs), `datetime` (timestamp parsing/comparison), `abc` (abstract record base), `unittest` and `trace` (test harness and coverage). No third-party component is used, per the project brief.

The full design rationale, class structure and diagrams are the subject of the Design document (Deliverable 2).

---

## 6. System requirements specification

### 6.1 External interface: console

The system presents numbered menus. Convention throughout: entering `0` at any prompt goes back one level; the main menu's `12` exits.

**Main menu.** 1 Create a record · 2 Display all records · 3 Display one record · 4 Delete a record · 5 Modify a record · 6 Search by type · 7 Search by text · 8 Search by time · 9 Search with AND / OR / NOT · 10 Save records · 11 Load records · 12 Exit.

### 6.2 Functional requirements

Requirement IDs are grouped by user story. Rationale accompanies every requirement.

#### FR-1 Creating PIRs (US1–US5)

| ID | Requirement | Rationale |
|---|---|---|
| FR-1.1 | The system **shall** offer exactly the four record types Note, Task, Event, Contact in the create menu. | US1 names exactly these; a fixed set keeps the menu and file format stable. |
| FR-1.2 | A note **shall** consist of one field, `content`. The system **shall** reject creation when `content` is empty or only whitespace. | US2; an empty note carries no information, so accepting it would create junk records. |
| FR-1.3 | A task **shall** consist of `description` and `deadline`; both **shall** be required, and `deadline` **shall** be a valid timestamp. | US3; a task without a deadline cannot answer the time searches US7 defines. |
| FR-1.4 | An event **shall** consist of `description`, `starting_time` and `alarm`; all required, the times valid timestamps. | US4. |
| FR-1.5 | A contact **shall** consist of `name`, `address` and `mobile_number`; all required. A mobile number **shall** be stored as text, preserving a leading zero. | US5; phone numbers are identifiers, not quantities, and `0123…` must survive. |
| FR-1.6 | The system **shall** assign every created record a unique 8-character ID at creation time. | Every other story addresses records by ID; uniqueness is what makes those references sound. |
| FR-1.7 | The system **shall** accept a timestamp only in the form `YYYY-MM-DD HH:MM` and reject every other shape with an error message. | One format is what makes time comparisons (US7) and file round-trips well-defined. |
| FR-1.8 | At any prompt inside the create flow, entering `0` **shall** abandon the record without storing anything. | Lets the user back out of a mistake; half-entered records must not accumulate. |

#### FR-2 Modifying PIRs (US6)

| ID | Requirement | Rationale |
|---|---|---|
| FR-2.1 | The system **shall** let the user pick a record by ID and then one of that record type's fields to change. | US6 says "modify the data in existing PIRs"; field-level choice avoids retyping untouched fields. |
| FR-2.2 | The system **shall** validate a new field value with the same rules as creation, and **shall** reject an invalid value leaving the record unchanged. | A rejected edit must not be half-applied. |
| FR-2.3 | Requesting an ID that does not exist **shall** produce an error naming the ID, and change nothing. | Keeps the mistake visible instead of silently doing nothing. |

#### FR-3 Searching (US7)

| ID | Requirement | Rationale |
|---|---|---|
| FR-3.1 | A text test **shall** match a record when the named text field contains the given string, ignoring case on both sides. | Users cannot be expected to match capitalisation exactly. |
| FR-3.2 | A text test on a field the record type does not have **shall** not match that record. | A Note has no `name`; it must not satisfy a name test. |
| FR-3.3 | A time test **shall** match when the named time field is strictly before (`<`), strictly after (`>`), or exactly equal to (`=`) a given timestamp. | The three comparators of US7. |
| FR-3.4 | A type test **shall** match every record of the named type, ignoring case. | US7 lists record type as a criterion dimension. |
| FR-3.5 | The system **shall** combine criteria with `&&` (all operands must match) and `||` (at least one operand must match), each accepting two or more operands. | US7's logical connectors. |
| FR-3.6 | The system **shall** support negation `!`, which **shall** invert its single operand. | US7. |
| FR-3.7 | Criteria **shall** nest to any depth: any operand of `&&`/`||`/`!` may itself be any criterion. | Nested conditions like `type = Task && !(description contains "draft")` are natural queries. |
| FR-3.8 | A search **shall** list every matching record in creation order, or a "no matching records" message when none match. | An empty result must be distinguishable from a failed search. |
| FR-3.9 | The system **shall** accept every criterion expressible in the grammar of Section 6.4, and reject with an error message every ill-formed criterion attempt. | This is the verifiability clause that pairs the grammar with the tests. |

#### FR-4 Displaying PIRs (US8)

| ID | Requirement | Rationale |
|---|---|---|
| FR-4.1 | The system **shall** print, on one line per record, the type, ID and every field of the requested record or of all stored records. | US8 says "detailed information"; one line per record keeps lists readable. |
| FR-4.2 | When no records exist, the system **shall** print an explicit empty-state message. | Distinguishes an empty collection from a rendering failure. |

#### FR-5 Deleting PIRs (US9)

| ID | Requirement | Rationale |
|---|---|---|
| FR-5.1 | The system **shall** remove exactly the record named by the given ID and confirm the deletion. | US9. |
| FR-5.2 | Deleting a non-existent ID **shall** produce an error and delete nothing. | Mirrors FR-2.3. |

#### FR-6 Persisting PIRs (US10, US11)

| ID | Requirement | Rationale |
|---|---|---|
| FR-6.1 | The system **shall** write every stored record to a file whose name ends `.pim`, appending the extension when the user omits it. | US10 fixes the extension; the user should not have to type it. |
| FR-6.2 | The system **shall** load a `.pim` file and replace the in-memory collection with its contents, restoring record IDs exactly as stored. | US11; stable IDs are what make stored references meaningful across sessions. |
| FR-6.3 | Before a load replaces a non-empty collection, the system **shall** ask for confirmation, stating how many records will be replaced. | US11 does not forbid confirmation, and silent data loss is the worst failure a PIM can have. |
| FR-6.4 | A `.pim` file that is not valid JSON, is not a list, contains an unknown type, a missing field, a malformed timestamp, or a missing/non-string/repeated ID **shall** be rejected with an error naming the file and the offending record, and **shall not** change the current collection. | Parse-everything-before-replacing: a corrupt file must cost the user nothing. |
| FR-6.5 | A save immediately followed by a load **shall** reproduce the collection exactly: same types, same IDs, same field values, same order. | The round-trip fidelity requirement; stated with a threshold as NFR-1. |

#### FR-7 Session control and invalid input

| ID | Requirement | Rationale |
|---|---|---|
| FR-7.1 | The system **shall** exit cleanly when the user chooses exit, and also on Ctrl-C or end-of-input. | Ctrl-C is a normal way to leave a console program. |
| FR-7.2 | A non-numeric or out-of-range menu entry **shall** produce an error message and redisplay the menu, without exiting. | A typo must never terminate a session. |
| FR-7.3 | An empty value where a value is required **shall** be reported as an error; an empty filename for save or load **shall** be reported as an error. | Silent no-ops hide mistakes from the user. |

### 6.3 Non-functional requirements

Each requirement is stated so that a specific check can decide pass/fail. Reference machine: the development platform, Windows, Python 3.14 (`[confirm your dev version — TODO]`).

| ID | Requirement (shall) | How it is verified |
|---|---|---|
| NFR-1 | Saving any collection of up to 1,000 records and loading it back shall yield a collection deep-equal to the original: identical types, IDs, field values and order (round-trip fidelity: 0 records lost or altered). | Automated round-trip tests over all four types, empty and non-empty collections, and non-ASCII content. |
| NFR-2 | Any single menu operation (create, display, delete, modify, search, save, load) over a collection of 1,000 in-memory records shall complete in under 1 second on the reference machine. | Timed script over a generated 1,000-record collection; the linear search over 1,000 records is far inside the bound. |
| NFR-3 | Every malformed input enumerated in the invalid-input suite (bad menu entry, bad field value, bad timestamp, unknown ID, missing file, corrupt `.pim`, unknown type, missing/invalid/repeated ID) shall produce a single-line error message and leave all stored state unchanged, with no traceback reaching the user. | The unit-test suite runs each case and asserts both the message and unchanged state. |
| NFR-4 | The system shall run with the Python standard library only: no import outside the standard library and the system's own packages anywhere in the source. | Import scan of all source files. |
| NFR-5 | All model behaviour shall be testable without simulating console input or output: the `model` package shall contain no `print` or `input` call. | Text scan of `model/`; the model test suite runs without console redirection. |
| NFR-6 | The `.pim` format shall be human-readable: UTF-8, indented JSON, with non-ASCII text preserved exactly. | Inspection of a saved file; round-trip test with Chinese content. |

### 6.4 The US7 criterion grammar

US7's criteria are an expression language, so they are specified as one. The grammar defines **which criteria the system must accept** — the abstract space of predicates — not the keystrokes used to compose them (the project brief leaves the interaction specifics to us; Section 6.5 defines them).

```text
expression  ::= or-expr
or-expr     ::= and-expr { "||" and-expr }          -- lowest precedence
and-expr    ::= not-expr { "&&" not-expr }          -- binds tighter than ||
not-expr    ::= "!" not-expr | primary              -- binds tightest of all
primary     ::= "(" expression ")" | leaf
leaf        ::= text-test | time-test | type-test

text-test   ::= text-field "contains" string
time-test   ::= time-field ( "<" | ">" | "=" ) timestamp
type-test   ::= "type" "=" type-name

text-field  ::= "content" | "description" | "name" | "address" | "mobile_number"
time-field  ::= "deadline" | "starting_time" | "alarm"
type-name   ::= "Note" | "Task" | "Event" | "Contact"
timestamp   ::= YYYY "-" MM "-" DD " " HH ":" MM
string      ::= a non-empty sequence of characters
```

Precedence, from tightest to loosest: `!`, then `&&`, then `||`; brackets override. Examples (all in the language, hence all acceptable):

- `content contains "milk"`
- `deadline < 2026-11-20 18:00`
- `type = Task && description contains "report"`
- `!(type = Contact) || (starting_time > 2026-12-01 09:00 && alarm = 2026-12-01 08:30)`

**Rationale.** Writing the criteria as a grammar rather than prose is what makes FR-3.9 verifiable: a criterion is acceptable exactly when it has a derivation in this grammar. Every sentence of US7 is a production above; nothing outside US7 was added.

### 6.5 Interaction model: how a criterion is composed

The system composes criteria through a guided menu rather than typed expressions, which removes the whole class of syntax errors for the user. The mapping to the grammar is exact:

| Grammar construct | How the user composes it |
|---|---|
| `leaf` | Menu 9 → "Single test" → one of the three leaf menus |
| `text-test` | Leaf menu "Text field" → choose one of the five text fields → type the keyword |
| `time-test` | Leaf menu "Time field" → choose field → choose `before` / `after` / `equal` (rendered `<`, `>`, `=`) → type the timestamp |
| `type-test` | Leaf menu "Record type" → choose one of the four types |
| `&&` / `||` | Menu 9 → "AND (&&)" / "OR (||)" → compose the two (or more, by further nesting) operands through the same menu |
| `!` | Menu 9 → "NOT (!)" → compose the single operand |
| `(` `)` brackets | Implicit: the tree structure is the bracketing, so nesting needs no typing |

The menu therefore realises exactly the derivations of Section 6.4 — no more, no fewer. After composing, the system shows the criterion rendered back in the grammar's notation (brackets made explicit) before listing the matches, so the user can see what was asked. An ill-formed attempt — an unknown field, a bad timestamp, an empty keyword — is rejected at the moment it is entered (FR-3.9).

### 6.6 External interface: the `.pim` file

A `.pim` file is a UTF-8 JSON array, indented, one object per record in collection order. Each object carries a `"type"` discriminator, the record's `"pir_id"`, and every field of that type:

```json
[
    { "type": "Task", "pir_id": "a1b2c3d4",
      "description": "Submit project", "deadline": "2026-11-20 18:00" },
    { "type": "Note", "pir_id": "b2c3d4e5", "content": "買牛奶" }
]
```

Field sets per type (all required, all strings):

| Type | Fields |
|---|---|
| Note | `content` |
| Task | `description`, `deadline` |
| Event | `description`, `starting_time`, `alarm` |
| Contact | `name`, `address`, `mobile_number` |

**Reader obligations.** On load, the system validates every entry against the table above and the ID rules of FR-6.4; the enumerated rejection cases are exactly those of FR-6.4. This format is versioned by this document: any future change to it must update this section.

### 6.7 Traceability: user stories to requirements

| User story (Appendix B) | SRS requirements |
|---|---|
| US1 create different types of PIRs | FR-1.1, FR-1.6 |
| US2 create plain-text notes | UR-2, FR-1.2 |
| US3 create tasks | UR-3, FR-1.3 |
| US4 create events | UR-4, FR-1.4 |
| US5 create contacts | UR-5, FR-1.5 |
| US6 modify existing PIRs | UR-6, FR-2.1–FR-2.3 |
| US7 search by type/text/time/logic | UR-7, FR-3.1–FR-3.9, §6.4, §6.5 |
| US8 print one/all PIRs | UR-8, FR-4.1, FR-4.2 |
| US9 delete a PIR | UR-9, FR-5.1, FR-5.2 |
| US10 store PIRs in a `.pim` file | UR-10, FR-6.1, FR-6.5, §6.6 |
| US11 load PIRs from a `.pim` file | UR-11, FR-6.2–FR-6.4, §6.6 |

Every user story traces to at least one functional requirement; the implementation status of each is reported separately in the requirements coverage table at the root of the source code (Deliverable 3.e).
