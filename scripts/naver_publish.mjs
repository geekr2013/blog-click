import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const root = process.cwd();
const outbox = path.join(root, 'outbox');
const blogId = process.env.NAVER_BLOG_ID || 'hi_chk';
const id = process.env.NAVER_ID;
const pw = process.env.NAVER_PASSWORD;
if (!id || !pw) throw new Error('NAVER_ID and NAVER_PASSWORD are required.');

const days = fs.readdirSync(outbox).sort();
if (!days.length) throw new Error('No outbox folder found.');
const meta = JSON.parse(fs.readFileSync(path.join(outbox, days.at(-1), 'meta.json'), 'utf-8'));
const markdown = fs.readFileSync(path.join(root, meta.content_markdown), 'utf-8');
const coverPath = path.join(root, meta.cover_image);

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();
await page.goto('https://nid.naver.com/nidlogin.login');
await page.fill('input#id', id);
await page.fill('input#pw', pw);
await page.click('button#log\.login');
await page.waitForTimeout(4000);
await page.goto(`https://blog.naver.com/${blogId}?Redirect=Write`);
await page.waitForTimeout(4000);
await page.fill("input[placeholder='제목']", meta.title);
await page.locator('div.se-component.se-text.se-l-default').first().click();
await page.keyboard.type(markdown);
const fileInput = page.locator("input[type='file']");
if (await fileInput.count()) await fileInput.first().setInputFiles(coverPath);
await page.locator("button:has-text('발행')").first().click();
await page.waitForTimeout(1200);
await page.locator("button:has-text('발행')").last().click();
await page.waitForTimeout(2000);
await browser.close();
console.log('Publish completed');
