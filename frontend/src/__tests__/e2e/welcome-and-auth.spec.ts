import { test, expect } from "@playwright/test";

test.describe("Welcome and Authentication", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("ATM frame renders with all housing components", async ({ page }) => {
    await expect(page.getByTestId("atm-frame")).toBeVisible();
    await expect(page.getByTestId("screen-bezel")).toBeVisible();
    await expect(page.getByTestId("screen-display")).toBeVisible();
    await expect(page.getByTestId("card-slot")).toBeVisible();
    await expect(page.getByTestId("cash-dispenser")).toBeVisible();
    await expect(page.getByTestId("receipt-printer")).toBeVisible();
    await expect(page.getByTestId("numeric-keypad")).toBeVisible();
    await expect(page.getByTestId("side-buttons-left")).toBeVisible();
    await expect(page.getByTestId("side-buttons-right")).toBeVisible();
  });

  test("Welcome screen accepts card number input", async ({ page }) => {
    await expect(page.getByText("Welcome")).toBeVisible();
    const input = page.getByTestId("card-number-input");
    await expect(input).toBeVisible();
    await input.fill("1000-0001-0001");
    await expect(input).toHaveValue("1000-0001-0001");
  });

  test("PIN entry via numeric keypad clicks", async ({ page }) => {
    // Insert card
    const input = page.getByTestId("card-number-input");
    await input.fill("1000-0001-0001");
    await page.getByTestId("key-enter").click();

    // Should be on PIN entry screen
    await expect(page.getByText("Enter PIN")).toBeVisible();

    // Click digits on keypad
    await page.getByTestId("key-1").click();
    await page.getByTestId("key-2").click();
    await page.getByTestId("key-3").click();
    await page.getByTestId("key-4").click();

    // Should show 4 filled PIN dots
    const filledDots = page.locator(".pin-dot--filled");
    await expect(filledDots).toHaveCount(4);
  });

  test("Successful login flow (card → PIN → main menu)", async ({ page }) => {
    // Insert card
    const input = page.getByTestId("card-number-input");
    await input.fill("1000-0001-0001");
    await page.getByTestId("key-enter").click();

    // Enter PIN
    await expect(page.getByText("Enter PIN")).toBeVisible();
    await page.getByTestId("key-1").click();
    await page.getByTestId("key-2").click();
    await page.getByTestId("key-3").click();
    await page.getByTestId("key-4").click();
    await page.getByTestId("key-enter").click();

    // Should reach main menu
    await expect(page.getByText("Main Menu")).toBeVisible({ timeout: 5000 });
  });

  test("Failed PIN shows error message", async ({ page }) => {
    // Insert card
    const input = page.getByTestId("card-number-input");
    await input.fill("1000-0001-0001");
    await page.getByTestId("key-enter").click();

    // Enter wrong PIN
    await expect(page.getByText("Enter PIN")).toBeVisible();
    await page.getByTestId("key-9").click();
    await page.getByTestId("key-9").click();
    await page.getByTestId("key-9").click();
    await page.getByTestId("key-9").click();
    await page.getByTestId("key-enter").click();

    // Should show error
    await expect(page.locator(".screen-error")).toBeVisible({ timeout: 5000 });
  });
});
