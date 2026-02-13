import { test, expect } from "@playwright/test";

test.describe("Animation and UI Elements", () => {
  test("Card slot card element appears after login", async ({ page }) => {
    await page.goto("/");

    // Before login, card element should not be present
    await expect(page.getByTestId("card-slot-card")).not.toBeVisible();

    // Insert card
    const input = page.getByTestId("card-input");
    await input.fill("1000-0001-0001");
    await page.getByTestId("key-enter").click();

    // After card insertion, card element should appear
    await expect(page.getByTestId("card-slot-card")).toBeVisible({
      timeout: 3000,
    });
  });

  test("Cash dispenser flap element exists", async ({ page }) => {
    await page.goto("/");

    // Cash dispenser should have a flap element
    const flap = page.getByTestId("cash-dispenser-flap");
    await expect(flap).toBeVisible();
  });

  test("Screen bezel has CRT glow effect", async ({ page }) => {
    await page.goto("/");

    // Screen display should be visible with styling
    const display = page.getByTestId("screen-display");
    await expect(display).toBeVisible();

    // Verify the display has the screen-display class (which has the CRT glow)
    await expect(display).toHaveClass(/screen-display/);
  });
});
