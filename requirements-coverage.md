# Requirements Coverage Report

COMP3211 Software Engineering — Group Project

Every user story, user requirement, functional requirement and non-functional requirement in the SRS, with where it is implemented and the test that demonstrates it.

Test names refer to `tests/test_model.py` and `tests/test_controller.py` (159 tests, all passing). Model line coverage is 100.0% (628/628); see `coverage_report.txt`.

## 1. User stories

| Story | Summary | Status | Where | Verified by |
|---|---|---|---|---|
| US1 | Create different types of PIRs | Implemented | `model/pir.py`, four subclasses; `AppController.create_record` | `test_note_fields`, `test_task_fields_and_details`, `test_event_fields_and_details`, `test_contact_fields_and_details` |
| US2 | Create plain-text notes | Implemented | `model/note.py` (`content`) | `test_note_fields`, `test_create_note` |
| US3 | Create tasks with description and deadline | Implemented | `model/task.py` (`description`, `deadline`) | `test_task_fields_and_details`, `test_create_task` |
| US4 | Create events with description, start and alarm | Implemented | `model/event.py` | `test_event_fields_and_details`, `test_create_event` |
| US5 | Create contacts with name, address and mobile | Implemented | `model/contact.py` | `test_contact_fields_and_details`, `test_create_contact` |
| US6 | Modify data in existing PIRs | Implemented | `PIMRepository.update` → `PIR.set_field`; menu 5 | `test_update_changes_one_field`, `test_modify_updates_a_field` |
| US7 | Search by criteria with contains, time comparison and connectives | Implemented | `model/criteria.py`; `PIMRepository.search`; menus 6–9 | `test_text_contains_is_case_insensitive`, `test_time_compare_before`, `test_nesting_is_supported` |
| US8 | Print a specific PIR or all PIRs | Implemented | `PIMRepository.all` / `get`; `ConsoleView.show_records`; menus 2–3 | `test_display_all_shows_stored_record`, `test_display_one_by_id` |
| US9 | Delete a specified PIR | Implemented | `PIMRepository.delete`; menu 4 | `test_delete_removes_record`, `test_delete_unknown_id` |
| US10 | Store PIRs in a `.pim` file | Implemented | `Storage.save`; `PIMRepository.save`; menu 10 | `test_round_trip_preserves_every_type`, `test_save_reports_path` |
| US11 | Load PIRs from a `.pim` file | Implemented | `Storage.load`; `PIMRepository.load`; menu 11 | `test_round_trip_preserves_every_type`, `test_load_restores_records` |

**All 11 user stories are implemented.**

## 2. User requirements

These are the SRS statements owned by the customer; each is realised by the functional requirements below it.

| ID | Status | Where | Verified by |
|---|---|---|---|
| UR-1 | Implemented | `model/pir.py`, four subclasses; `AppController.create_record` | `test_note_fields`, `test_task_fields_and_details`, `test_event_fields_and_details`, `test_contact_fields_and_details` |
| UR-2 | Implemented | `model/note.py` (`content`) | `test_note_fields`, `test_create_note` |
| UR-3 | Implemented | `model/task.py` (`description`, `deadline`) | `test_task_fields_and_details`, `test_create_task` |
| UR-4 | Implemented | `model/event.py` | `test_event_fields_and_details`, `test_create_event` |
| UR-5 | Implemented | `model/contact.py` | `test_contact_fields_and_details`, `test_create_contact` |
| UR-6 | Implemented | `PIMRepository.update` → `PIR.set_field`; menu 5 | `test_update_changes_one_field`, `test_modify_updates_a_field` |
| UR-7 | Implemented | `model/criteria.py`; `PIMRepository.search`; menus 6–9 | `test_text_contains_is_case_insensitive`, `test_time_compare_before`, `test_nesting_is_supported` |
| UR-8 | Implemented | `PIMRepository.all` / `get`; `ConsoleView.show_records`; menus 2–3 | `test_display_all_shows_stored_record`, `test_display_one_by_id` |
| UR-9 | Implemented | `PIMRepository.delete`; menu 4 | `test_delete_removes_record`, `test_delete_unknown_id` |
| UR-10 | Implemented | `Storage.save`; `PIMRepository.save`; menu 10 | `test_round_trip_preserves_every_type`, `test_save_reports_path` |
| UR-11 | Implemented | `Storage.load`; `PIMRepository.load`; menu 11 | `test_round_trip_preserves_every_type`, `test_load_restores_records` |
| UR-12 | Implemented | `PIMError` hierarchy; validation in `PIR` and `Storage` | `test_repository_load_keeps_old_records_when_file_is_bad`, `test_non_utf8_file_is_reported_as_pim_error` |
| UR-13 | Implemented | Linear operations over `_records`; no index rebuild | `test_all_preserves_insertion_order` (timing measured separately, §3) |
| UR-14 | Implemented | Standard library only; `main.py` runs from a clean copy | Import scan; clean-folder extraction run |

## 3. Functional requirements

| ID | Status | Where | Verified by |
|---|---|---|---|
| FR-1.1 | Implemented | `CREATE_OPTIONS` in `app_controller.py` | `test_create_note`, `test_create_task`, `test_create_event`, `test_create_contact` |
| FR-1.2 | Implemented | `PIR._validate_field` rejects blank text | `test_note_rejects_empty_content` |
| FR-1.3 | Implemented | `Task.TIME_FIELDS`; `parse_timestamp` | `test_task_rejects_bad_deadline` |
| FR-1.4 | Implemented | `Event._validate_alarm_before_start`; both time fields required | `test_event_rejects_bad_alarm`, `test_event_rejects_an_alarm_after_the_start`, `test_event_rejects_an_alarm_at_the_start`, `test_event_edit_cannot_break_the_ordering` |
| FR-1.5 | Implemented | `Contact`; mobile kept as `str` | `test_contact_keeps_leading_zero` |
| FR-1.6 | Implemented | `PIR.__init__` (`uuid4()[:8]`) | `test_identity_is_generated_and_unique` |
| FR-1.7 | Implemented | `parse_timestamp` round-trips through `strftime` | `test_accepts_the_documented_format`, `test_rejects_unpadded_fields` |
| FR-1.8 | Implemented | `_ask_value` returns `None` on `0` | `test_create_stores_nothing_when_the_user_backs_out`, `test_backing_out_of_create_stores_nothing` |
| FR-1.9 | Implemented | `_ask_value` re-asks until the value passes `_check_value` | `test_create_reasks_after_a_bad_timestamp` |
| FR-2.1 | Implemented | `modify_record` offers `record.FIELDS` | `test_modify_updates_a_field` |
| FR-2.2 | Implemented | `PIR.set_field` validates before writing; the prompt re-asks | `test_update_rejects_unknown_field_and_leaves_record_intact`, `test_modify_reasks_after_a_bad_value` |
| FR-2.3 | Implemented | `RecordNotFoundError` | `test_modify_unknown_id` |
| FR-3.1 | Implemented | `TextContains.matches` (`casefold`) | `test_text_contains_is_case_insensitive` |
| FR-3.2 | Implemented | `get_field` returns `None` for absent fields | `test_text_contains_skips_records_without_the_field` |
| FR-3.3 | Implemented | `TimeCompare.matches` | `test_time_compare_before`, `test_time_compare_after`, `test_time_compare_equal_is_inclusive` |
| FR-3.4 | Implemented | `TypeIs.matches` | `test_type_is_matches_class` |
| FR-3.5 | Implemented | `And` / `Or`, positional operands | `test_and_requires_all_operands`, `test_or_requires_one_operand` |
| FR-3.6 | Implemented | `Not` | `test_not_inverts_its_operand` |
| FR-3.7 | Implemented | Composites accept criteria as operands | `test_nesting_is_supported`, `test_three_level_nesting` |
| FR-3.8 | Implemented | `search` preserves order; empty message from `show_records` | `test_all_preserves_insertion_order`, `test_search_by_text_miss` |
| FR-3.9 | Implemented | Every grammar production is accepted; ill-formed input raises | `test_malformed_forms_are_rejected`, `test_missing_comparator_after_time_field`, `test_search_reports_a_malformed_expression` |
| FR-4.1 | Implemented | `PIR.get_summary()` per type; `ConsoleView.show_records` | `test_summary_is_a_single_line_for_every_type`, `test_summary_truncates_a_long_field`, `test_summary_keeps_a_short_field_intact` |
| FR-4.2 | Implemented | `PIR.get_details()` per type; `ConsoleView.show_record` wraps a long value | `test_details_are_multiline_and_complete`, `test_details_keep_every_field` |
| FR-4.3 | Implemented | `show_records(..., "No records have been created yet.")` | `test_display_all_when_empty` |
| FR-5.1 | Implemented | `PIMRepository.delete` | `test_delete_removes_record` |
| FR-5.2 | Implemented | `RecordNotFoundError` | `test_delete_unknown_id` |
| FR-6.1 | Implemented | `with_extension` appends the extension or rejects another one | `test_extension_is_appended`, `test_other_extensions_are_rejected`, `test_extension_match_is_case_insensitive`, `test_save_returns_path_used` |
| FR-6.2 | Implemented | `Storage.load`; `from_dict` restores `pir_id` | `test_to_dict_and_from_dict_round_trip` |
| FR-6.3 | Implemented | Confirmation prompt in `load_records` | `test_load_with_records_asks_before_replacing`, `test_load_declined_keeps_current_records`, `test_load_with_empty_memory_does_not_confirm` |
| FR-6.4 | Implemented | Seven validation rules in `Storage.load` | `test_wrong_top_level_shape_is_rejected`, `test_non_object_entry_is_rejected`, `test_unusable_id_in_file_is_rejected`, `test_duplicate_id_in_file_is_rejected`, `test_unknown_type_is_rejected`, `test_missing_field_is_rejected`, `test_invalid_timestamp_in_file_is_rejected` |
| FR-6.5 | Implemented | Round-trip by construction | `test_round_trip_preserves_every_type`, `test_empty_collection_round_trips`, `test_non_ascii_survives` |
| FR-7.1 | Implemented | `main.main` catches `KeyboardInterrupt` / `EOFError` | `test_exit_by_menu_number`, `test_exit_by_zero` |
| FR-7.2 | Implemented | `_read_main_choice`, `ask_choice` | `test_non_numeric_choice_is_reported`, `test_out_of_range_choice_is_reported` |
| FR-7.3 | Implemented | Empty-value error in `_ask_value`; empty-filename errors | `test_save_empty_filename_is_reported`, `test_load_empty_filename_is_reported` |

## 4. Non-functional requirements

| ID | Status | Evidence |
|---|---|---|
| NFR-1 | Implemented | Round-trip tests over four types, the empty set and non-ASCII content. `test_round_trip_preserves_every_type`, `test_non_ascii_survives` |
| NFR-2 | Implemented | Every operation is linear in the number of records. Measured on a 1,000-record collection on the reference machine: save 2.9 ms, load 6.3 ms, compound search 0.33 ms, single add 0.02 ms, get 0.01 ms — all far inside the 1 s bound **Note:** Timing is an observation, not an assertion; no test asserts a bound. |
| NFR-3 | Implemented | Each invalid-input case asserts a message and unchanged state. `test_repository_load_keeps_old_records_when_file_is_bad`, `test_non_utf8_file_is_reported_as_pim_error` |
| NFR-4 | Implemented | Imports limited to `json`, `uuid`, `datetime`, `abc`, `sys`. Import scan of every shipped module |
| NFR-5 | Implemented | `model/` contains no `print` or `input`. `tests/test_model.py` runs with no console redirection |
| NFR-6 | Implemented | `json.dump(..., indent=4, ensure_ascii=False)`. `test_non_ascii_survives` |

## 5. Summary

| Category | Total | Implemented | Partial | Not implemented |
|---|---|---|---|---|
| User stories | 11 | 11 | 0 | 0 |
| User requirements | 14 | 14 | 0 | 0 |
| Functional requirements | 34 | 34 | 0 | 0 |
| Non-functional requirements | 6 | 6 | 0 | 0 |
| **Total** | **65** | **65** | **0** | **0** |

## 6. Deliberate scope exclusions

These are not gaps: the brief rules them out, so implementing them earns no credit.

| Excluded | Reason |
|---|---|
| Graphical user interface | "not recommended to add additional features, e.g., a GUI or support for online use… will not get you extra credit" |
| Web or multi-user access | Same clause |
| Third-party libraries | "should only invoke Java/Python standard libraries" |
| Undo / history | Not required by any user story |

## 7. Known limitations within scope

1. `0` is reserved at every prompt, so the literal text `0` cannot be stored or searched for. At the main menu `0` exits rather than going back.
2. A `save` over an existing `.pim` file replaces it without confirmation, while `load` does confirm. Asymmetric by decision.
3. Empty input during record creation abandons the whole record and returns to the main menu, rather than re-asking that one field.
