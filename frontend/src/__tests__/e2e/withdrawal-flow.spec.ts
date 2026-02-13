import { test, expect } from "@playwright/test";

async function loginAsAlice(page: import("@playwright/test").Page) {
  await page.goto("/");
  const input = page.getByTestId("card-input");
  await input.fill("1000-0001-0001");
  await page.getByTestId("key-enter").click();
  await expect(page.getByText("Enter Your PIN")).toBeVisible();
  await page.getByTestId("key-1").click();
  await page.getByTestId("key-2").click();
  await page.getByTestId("key-3").click();
  await page.getByTestId("key-4").click();
  await page.getByTestId("key-enter").click();
  await expect(page.getByText("Main Menu")).toBeVisible({ timeout: 5000 });
}

async function navigateToWithdrawal(page: import("@playwright/test").Page) {
  const withdrawBtn = page.getByTestId("side-btn-left-withdrawal");
  await withdrawBtn.click();
  await expect(page.getByText("Withdrawal")).toBeVisible({ timeout: 3000 });
}

test.describe("Withdrawal Flow", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAlice(page);
    await navigateToWithdrawal(page);
  });

  test("Quick withdraw $100 via side button → confirm screen", async ({ page }) => {
    const btn100 = page.getByTestId("side-btn-left--100");
    await btn100.click();
    await expect(page.getByText("Confirm")).toBeVisible({ timeout: 3000 });
    await expect(page.getByText("$100.00")).toBeVisible();
  });

  test("Custom amount via keypad → confirm screen", async ({ page }) => {
    // Type 260 via keypad
    await page.getByTestId("key-2").click();
    await page.getByTestId("key-6").click();
    await page.getByTestId("key-0").click();
    await page.getByTestId("key-0").click();
    await page.getByTestId("key-enter").click();

    await expect(page.getByText("Confirm")).toBeVisible({ timeout: 3000 });
  });

  test("Confirm withdrawal → receipt screen", async ({ page }) => {
    // Quick withdraw $100
    const btn100 = page.getByTestId("side-btn-left--100");
    await btn100.click();
    await expect(page.getByText("Confirm")).toBeVisible({ timeout: 3000 });

    // Click confirm
    const confirmBtn = page.getByTestId("side-btn-right-confirm");
    await confirmBtn.click();

    // Should show receipt
    await expect(page.getByText(/receipt|Reference/i)).toBeVisible({ timeout: 5000 });
  });

  test("Cancel returns to withdrawal screen", async ({ page }) => {
    // Quick withdraw $100
    const btn100 = page.getByTestId("side-btn-left--100");
    await btn100.click();
    await expect(page.getByText("Confirm")).toBeVisible({ timeout: 3000 });

    // Click cancel
    const cancelBtn = page.getByTestId("side-btn-right-cancel");
    await cancelBtn.click();

    // Should return to withdrawal
    await expect(page.getByText("Withdrawal")).toBeVisible({ timeout: 3000 });
  });
});
