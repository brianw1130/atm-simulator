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

test.describe("Main Menu Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAlice(page);
  });

  test("Side buttons display correct menu labels", async ({ page }) => {
    // Left side buttons should have menu options
    const leftButtons = page.getByTestId("side-buttons-left").locator("button");
    await expect(leftButtons).toHaveCount(4);

    // Right side buttons should have menu options
    const rightButtons = page.getByTestId("side-buttons-right").locator("button");
    await expect(rightButtons).toHaveCount(4);
  });

  test("Navigate to Balance Inquiry via side button", async ({ page }) => {
    const balanceBtn = page.getByTestId("side-btn-left-balance");
    await balanceBtn.click();
    await expect(page.getByText("Balance Inquiry")).toBeVisible({ timeout: 3000 });
  });

  test("Navigate to Withdrawal via side button", async ({ page }) => {
    const withdrawBtn = page.getByTestId("side-btn-left-withdrawal");
    await withdrawBtn.click();
    await expect(page.getByText("Withdrawal")).toBeVisible({ timeout: 3000 });
  });

  test("Logout returns to Welcome screen", async ({ page }) => {
    const logoutBtn = page.getByTestId("side-btn-right-logout");
    await logoutBtn.click();
    await expect(page.getByText("Welcome")).toBeVisible({ timeout: 3000 });
  });
});
