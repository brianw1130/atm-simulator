import { test, expect } from "@playwright/test";

async function loginAsAlice(page: import("@playwright/test").Page) {
  await page.goto("/");
  const input = page.getByTestId("card-number-input");
  await input.fill("1000-0001-0001");
  await page.getByTestId("key-enter").click();
  await expect(page.getByText("Enter PIN")).toBeVisible();
  await page.getByTestId("key-1").click();
  await page.getByTestId("key-2").click();
  await page.getByTestId("key-3").click();
  await page.getByTestId("key-4").click();
  await page.getByTestId("key-enter").click();
  await expect(page.getByText("Main Menu")).toBeVisible({ timeout: 5000 });
}

test.describe("Error and Edge Cases", () => {
  test("Clear button resets PIN entry", async ({ page }) => {
    await page.goto("/");

    // Insert card
    const input = page.getByTestId("card-number-input");
    await input.fill("1000-0001-0001");
    await page.getByTestId("key-enter").click();
    await expect(page.getByText("Enter PIN")).toBeVisible();

    // Type some digits
    await page.getByTestId("key-1").click();
    await page.getByTestId("key-2").click();

    // Should have 2 filled dots
    let filledDots = page.locator(".pin-dot--filled");
    await expect(filledDots).toHaveCount(2);

    // Clear
    await page.getByTestId("key-clear").click();

    // Should have 0 filled dots
    filledDots = page.locator(".pin-dot--filled");
    await expect(filledDots).toHaveCount(0);
  });

  test("Multiple menu navigations in single session", async ({ page }) => {
    await loginAsAlice(page);

    // Navigate to withdrawal
    await page.getByTestId("side-btn-left-withdrawal").click();
    await expect(page.getByText("Withdrawal")).toBeVisible({ timeout: 3000 });

    // Go back
    await page.getByTestId("side-btn-right-back").click();
    await expect(page.getByText("Main Menu")).toBeVisible({ timeout: 3000 });

    // Navigate to deposit
    await page.getByTestId("side-btn-left-deposit").click();
    await expect(page.getByText("Deposit")).toBeVisible({ timeout: 3000 });

    // Go back
    await page.getByTestId("side-btn-right-back").click();
    await expect(page.getByText("Main Menu")).toBeVisible({ timeout: 3000 });

    // Navigate to balance
    await page.getByTestId("side-btn-left-balance").click();
    await expect(page.getByText("Balance Inquiry")).toBeVisible({
      timeout: 3000,
    });
  });

  test("Deposit check type selection", async ({ page }) => {
    await loginAsAlice(page);

    await page.getByTestId("side-btn-left-deposit").click();
    await expect(page.getByText("Deposit")).toBeVisible({ timeout: 3000 });

    // Select Check deposit type
    const checkBtn = page.getByTestId("side-btn-left-check");
    await checkBtn.click();

    // Should be in amount entry mode - keypad should be active
    await expect(page.getByTestId("numeric-keypad")).toBeVisible();
    const digit1 = page.getByTestId("key-1");
    await expect(digit1).toBeEnabled();
  });

  test("Cancel button on withdrawal confirm screen", async ({ page }) => {
    await loginAsAlice(page);

    // Navigate to withdrawal
    await page.getByTestId("side-btn-left-withdrawal").click();
    await expect(page.getByText("Withdrawal")).toBeVisible({ timeout: 3000 });

    // Quick withdraw $100
    const btn100 = page.getByTestId("side-btn-left--100");
    await btn100.click();
    await expect(page.getByText("Confirm")).toBeVisible({ timeout: 3000 });

    // Cancel
    const cancelBtn = page.getByTestId("side-btn-right-cancel");
    await cancelBtn.click();

    // Should return to withdrawal
    await expect(page.getByText("Withdrawal")).toBeVisible({ timeout: 3000 });
  });

  test("Escape key functions as cancel on PIN entry", async ({ page }) => {
    await page.goto("/");

    // Insert card
    const input = page.getByTestId("card-number-input");
    await input.fill("1000-0001-0001");
    await page.getByTestId("key-enter").click();
    await expect(page.getByText("Enter PIN")).toBeVisible();

    // Press Escape to cancel
    await page.keyboard.press("Escape");

    // Should return to welcome screen
    await expect(page.getByText("Welcome")).toBeVisible({ timeout: 3000 });
  });
});
