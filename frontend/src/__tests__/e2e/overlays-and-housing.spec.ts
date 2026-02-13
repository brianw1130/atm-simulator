import { test, expect } from "@playwright/test";

test.describe("Overlays and Housing Components", () => {
  test("Card slot indicator activates on login", async ({ page }) => {
    await page.goto("/");

    // Before login, indicator should have inactive class
    const indicator = page.getByTestId("card-slot-indicator");
    await expect(indicator).toHaveClass(/card-slot__indicator--inactive/);

    // Insert card
    const input = page.getByTestId("card-number-input");
    await input.fill("1000-0001-0001");
    await page.getByTestId("key-enter").click();

    // After card insertion, indicator should be active (no inactive class)
    await expect(indicator).not.toHaveClass(/card-slot__indicator--inactive/);
  });

  test("Keypad disabled on non-input screens", async ({ page }) => {
    await page.goto("/");

    // Insert card and login
    const input = page.getByTestId("card-number-input");
    await input.fill("1000-0001-0001");
    await page.getByTestId("key-enter").click();
    await expect(page.getByText("Enter PIN")).toBeVisible();
    await page.getByTestId("key-1").click();
    await page.getByTestId("key-2").click();
    await page.getByTestId("key-3").click();
    await page.getByTestId("key-4").click();
    await page.getByTestId("key-enter").click();

    // On main menu, keypad should be disabled
    await expect(page.getByText("Main Menu")).toBeVisible({ timeout: 5000 });
    const digit1 = page.getByTestId("key-1");
    await expect(digit1).toBeDisabled();
  });

  test("Physical keyboard mapping works", async ({ page }) => {
    await page.goto("/");

    // Insert card
    const input = page.getByTestId("card-number-input");
    await input.fill("1000-0001-0001");
    await page.keyboard.press("Enter");

    // Should be on PIN entry screen
    await expect(page.getByText("Enter PIN")).toBeVisible();

    // Type PIN via physical keyboard
    await page.keyboard.press("1");
    await page.keyboard.press("2");
    await page.keyboard.press("3");
    await page.keyboard.press("4");

    // Should show 4 filled PIN dots
    const filledDots = page.locator(".pin-dot--filled");
    await expect(filledDots).toHaveCount(4);
  });
});
