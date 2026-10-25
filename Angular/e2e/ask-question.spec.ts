import { expect, test } from '@playwright/test';

const RESPONSE = {
  status: 'answer',
  clarification: null,
  message: null,
  intent: null,
  question_id: 'q-1',
  transcript: { text: 'How do I create a controller in Spring?', language: 'en' },
  answer: {
    text: 'Create the controller.\n```java\n@RestController\npublic class UserController {}\n```\nSpring wires it.',
    sources: [{ id: 's1', title: 'Spring Docs', url: 'https://spring.io', kind: 'documentation' }],
  },
};

test('record -> answer flow shows transcript, code block and sources', async ({ page, context }) => {
  await context.grantPermissions(['microphone']);
  await context.grantPermissions(['clipboard-read', 'clipboard-write']).catch(() => undefined);
  await page.route('**/v1/questions', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(RESPONSE) }),
  );

  await page.goto('/');
  await page.getByRole('button', { name: /Start listening/ }).click();
  await expect(page.getByRole('status')).toContainText('Listening');

  await page.getByRole('button', { name: 'Done, stop listening' }).click();

  await expect(page.getByText('How do I create a controller in Spring?')).toBeVisible();
  await expect(page.getByText('@RestController')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Spring Docs' }).first()).toBeVisible();

  await page.getByRole('button', { name: 'Copy code' }).click();
  await expect(page.getByRole('button', { name: 'Copy code' })).toContainText('Copied');
});

test('Escape cancels listening and returns to idle', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Control+Shift+M');
  await expect(page.getByRole('status')).toContainText('Listening');
  await page.keyboard.press('Escape');
  await expect(page.getByText('Try asking')).toBeVisible();
});
