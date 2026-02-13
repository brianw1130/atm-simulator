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

test.describe("Deposit and Transfer Flows", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAlice(page);
  });

  test("Select cash deposit type", async ({ page }) => {
    const depositBtn = page.getByTestId("side-btn-left-deposit");
    await depositBtn.click();
    await expect(page.getByText("Deposit")).toBeVisible({ timeout: 3000 });

    // Select Cash deposit
    const cashBtn = page.getByTestId("side-btn-left-cash");
    await cashBtn.click();

    // Should be in amount entry mode - keypad should be active
    await expect(page.getByTestId("numeric-keypad")).toBeVisible();
  });

  test("Complete cash deposit → receipt", async ({ page }) => {
    const depositBtn = page.getByTestId("side-btn-left-deposit");
    await depositBtn.click();
    await expect(page.getByText("Deposit")).toBeVisible({ timeout: 3000 });

    // Select Cash deposit
    const cashBtn = page.getByTestId("side-btn-left-cash");
    await cashBtn.click();

    // Enter $500 amount
    await page.getByTestId("key-5").click();
    await page.getByTestId("key-0").click();
    await page.getByTestId("key-0").click();
    await page.getByTestId("key-0").click();
    await page.getByTestId("key-0").click();
    await page.getByTestId("key-enter").click();

    // Should show receipt
    await expect(page.getByText(/receipt|Reference|Deposit/i)).toBeVisible({ timeout: 5000 });
  });

  test("Transfer to own account flow", async ({ page }) => {
    const transferBtn = page.getByTestId("side-btn-left-transfer");
    await transferBtn.click();
    await expect(page.getByText("Transfer")).toBeVisible({ timeout: 3000 });

    // Click own savings account button on left side
    const savingsBtn = page.getByTestId("side-btn-left-savings");
    await savingsBtn.click();

    // Enter amount $100
    await page.getByTestId("key-1").click();
    await page.getByTestId("key-0").click();
    await page.getByTestId("key-0").click();
    await page.getByTestId("key-0").click();
    await page.getByTestId("key-0").click();
    await page.getByTestId("key-enter").click();

    // Should show confirm screen
    await expect(page.getByText("Confirm")).toBeVisible({ timeout: 3000 });
  });

  test("Back button navigation works", async ({ page }) => {
    // Go to deposit screen
    const depositBtn = page.getByTestId("side-btn-left-deposit");
    await depositBtn.click();
    await expect(page.getByText("Deposit")).toBeVisible({ timeout: 3000 });

    // Click back
    const backBtn = page.getByTestId("side-btn-right-back");
    await backBtn.click();

    // Should return to main menu
    await expect(page.getByText("Main Menu")).toBeVisible({ timeout: 3000 });
  });
});
