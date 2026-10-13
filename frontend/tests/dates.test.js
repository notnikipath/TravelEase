import assert from "node:assert/strict";
import test from "node:test";
import { dateAfterDays } from "../src/dates.js";

test("tomorrow is the next local calendar day just after midnight", () => {
  assert.equal(dateAfterDays(1, new Date(2026, 9, 14, 0, 10)), "2026-10-15");
});

test("dates cross a year boundary", () => {
  assert.equal(dateAfterDays(1, new Date(2026, 11, 31, 0, 10)), "2027-01-01");
});

test("leap day and the input date are preserved", () => {
  const date = new Date(2028, 1, 28, 0, 10);
  assert.equal(dateAfterDays(1, date), "2028-02-29");
  assert.equal(date.getDate(), 28);
});
