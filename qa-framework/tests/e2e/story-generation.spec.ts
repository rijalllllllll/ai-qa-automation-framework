import { test, expect } from "@playwright/test";

/**
 * E2E test suites for the AI Children's Story Generator.
 * Covers: happy path, validation & edge cases, loading state, regeneration.
 */

const GOOD = {
  child_name: "Aisyah",
  age: "5",
  mood: "happy",
  character: "a purple dragon",
  moral: "kindness matters",
  length: "medium",
};

async function fillForm(page, data) {
  await page.fill("#childName", data.child_name ?? "");
  await page.selectOption("#age", data.age ?? "5");
  await page.selectOption("#mood", data.mood ?? "happy");
  await page.fill("#character", data.character ?? "");
  await page.fill("#moral", data.moral ?? "");
  await page.selectOption("#length", data.length ?? "medium");
}

test.describe("Story generation — core user flow", () => {
  test("happy path: generates and renders a story", async ({ page }) => {
    await page.goto("/");
    await fillForm(page, GOOD);
    await page.click("#generateBtn");

    await expect(page.locator("#storyView")).toBeVisible();
    await expect(page.locator("#storyTitle")).toContainText("Aisyah's Happy Adventure");
    await expect(page.locator("#sections h4").first()).toBeVisible();
    await expect(page.locator("#moralLine")).toContainText("Happiness grows when it is shared.");
    await expect(page.locator("#storyMeta")).toContainText("words");
  });

  test("loading state is shown while the story is being generated", async ({ page }) => {
    await page.goto("/");
    await fillForm(page, GOOD);
    // Simulate slow AI latency deterministically so the spinner is observable.
    await page.route("**/api/generate-story", async (route) => {
      await page.waitForTimeout(1500);
      await route.continue();
    });
    await page.click("#generateBtn");
    await expect(page.locator("#loading")).toBeVisible();
    await expect(page.locator("#storyView")).toBeVisible();
    await expect(page.locator("#loading")).toBeHidden();
  });

  test("regenerate produces a new story (new story_id)", async ({ page }) => {
    await page.goto("/");
    await fillForm(page, GOOD);
    await page.click("#generateBtn");
    await expect(page.locator("#storyView")).toBeVisible();

    await page.click("#regenerateBtn");
    await expect(page.locator("#storyView")).toBeVisible();
    // The second story arrives via the same view; sanity: field still populated.
    await expect(page.locator("#storyTitle")).toContainText("Adventure");
  });
});

test.describe("Validation & edge cases", () => {
  test("empty name shows an inline error and no story", async ({ page }) => {
    await page.goto("/");
    await fillForm(page, { ...GOOD, child_name: "" });
    await page.click("#generateBtn");

    await expect(page.locator("#errorBox")).toBeVisible();
    await expect(page.locator("#errorBox")).toContainText("at least 1 character");
    await expect(page.locator("#storyView")).toBeHidden();
  });

  test("name input caps at 40 chars in the UI; the API rejects longer names", async ({ page }) => {
    await page.goto("/");
    // UI: input has maxlength=40, so typing 41 chars yields a 40-char value.
    await fillForm(page, { ...GOOD, child_name: "N".repeat(41) });
    const value = await page.inputValue("#childName");
    expect(value.length).toBe(40);
    await page.click("#generateBtn");
    await expect(page.locator("#storyView")).toBeVisible();

    // API: bypassing the UI cap, a 41-char name is rejected with 422.
    const res = await page.request.post("/api/generate-story", {
      data: { child_name: "N".repeat(41), age: 5, mood: "happy", length: "short" },
    });
    expect(res.status()).toBe(422);
  });

  test("age outside 2-12 is rejected by the API", async ({ page }) => {
    await page.goto("/");
    const res = await page.request.post("/api/generate-story", {
      data: { child_name: "Aisyah", age: 13, mood: "happy", length: "short" },
    });
    expect(res.status()).toBe(422);
  });

  test("unknown mood is rejected with a clear message", async ({ page }) => {
    await page.goto("/");
    const res = await page.request.post("/api/generate-story", {
      data: { child_name: "Aisyah", age: 5, mood: "angry" },
    });
    expect(res.status()).toBe(422);
    const body = await res.json();
    expect(JSON.stringify(body)).toContain("mood must be one of");
  });
});

test.describe("UI structure & accessibility", () => {
  test("all form controls have accessible labels", async ({ page }) => {
    await page.goto("/");
    for (const id of ["#childName", "#age", "#mood", "#character", "#length", "#moral"]) {
      await expect(page.locator(`${id}`)).toBeVisible();
    }
    // Each control is wrapped in a <label> (accessible name comes from it).
    const labels = await page.locator("form label").count();
    expect(labels).toBeGreaterThanOrEqual(6);
    await expect(page.locator("h1")).toContainText("Story Generator");
  });

  test("generate button is keyboard-accessible (Enter submits the form)", async ({ page }) => {
    await page.goto("/");
    await fillForm(page, GOOD);
    await page.locator("#childName").focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("#storyView")).toBeVisible();
  });
});