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

test.describe("Balance Inquiry and Statement Flows", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAlice(page);
  });

  test("Navigate to balance inquiry and see balance display", async ({
    page,
  }) => {
    const balanceBtn = page.getByTestId("side-btn-left-balance");
    await balanceBtn.click();
    await expect(page.getByText("Balance Inquiry")).toBeVisible({
      timeout: 3000,
    });

    // Should display account information with a dollar amount
    await expect(page.locator(".screen-display")).toContainText(/\$/);
  });

  test("Balance inquiry back button returns to main menu", async ({
    page,
  }) => {
    const balanceBtn = page.getByTestId("side-btn-left-balance");
    await balanceBtn.click();
    await expect(page.getByText("Balance Inquiry")).toBeVisible({
      timeout: 3000,
    });

    const backBtn = page.getByTestId("side-btn-right-back");
    await backBtn.click();
    await expect(page.getByText("Main Menu")).toBeVisible({ timeout: 3000 });
  });

  test("Navigate to statement screen", async ({ page }) => {
    const statementBtn = page.getByTestId("side-btn-right-statement");
    await statementBtn.click();
    await expect(page.getByText("Statement")).toBeVisible({ timeout: 3000 });
  });

  test("Statement screen has date range buttons", async ({ page }) => {
    const statementBtn = page.getByTestId("side-btn-right-statement");
    await statementBtn.click();
    await expect(page.getByText("Statement")).toBeVisible({ timeout: 3000 });

    // Left side should have date range options
    const leftButtons = page
      .getByTestId("side-buttons-left")
      .locator("button");
    const visibleButtons = await leftButtons.filter({ hasText: /.+/ }).count();
    expect(visibleButtons).toBeGreaterThanOrEqual(2);
  });

  test("Statement screen back button returns to menu", async ({ page }) => {
    const statementBtn = page.getByTestId("side-btn-right-statement");
    await statementBtn.click();
    await expect(page.getByText("Statement")).toBeVisible({ timeout: 3000 });

    const backBtn = page.getByTestId("side-btn-right-back");
    await backBtn.click();
    await expect(page.getByText("Main Menu")).toBeVisible({ timeout: 3000 });
  });
});
