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

test.describe("PIN Change Flow", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAlice(page);
  });

  test("Navigate to PIN change screen", async ({ page }) => {
    const pinChangeBtn = page.getByTestId("side-btn-right-pin-change");
    await pinChangeBtn.click();
    await expect(page.getByText(/PIN|Change/i)).toBeVisible({ timeout: 3000 });
  });

  test("PIN change screen has keypad enabled for input", async ({ page }) => {
    const pinChangeBtn = page.getByTestId("side-btn-right-pin-change");
    await pinChangeBtn.click();
    await expect(page.getByText(/PIN|Change/i)).toBeVisible({ timeout: 3000 });

    // Keypad should be active on PIN change screen
    const digit1 = page.getByTestId("key-1");
    await expect(digit1).toBeEnabled();
  });

  test("PIN change cancel returns to main menu", async ({ page }) => {
    const pinChangeBtn = page.getByTestId("side-btn-right-pin-change");
    await pinChangeBtn.click();
    await expect(page.getByText(/PIN|Change/i)).toBeVisible({ timeout: 3000 });

    // Cancel should return to menu
    const cancelBtn = page.getByTestId("side-btn-right-cancel");
    await cancelBtn.click();
    await expect(page.getByText("Main Menu")).toBeVisible({ timeout: 3000 });
  });
});
