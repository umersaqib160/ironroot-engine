# IronRoot n8n Automation — Setup Guide
*Self-hosted n8n on Hetzner | Updated: June 2026*

---

## What This Does

You send a product photo to your Telegram bot → n8n generates Instagram, Facebook, and TikTok captions using Claude AI → sends the draft back to you in Telegram → you approve with ✅ → n8n automatically posts to Instagram and Facebook.

---

## Prerequisites

Before starting, you need:
- [ ] n8n running on your Hetzner server (assume you have this)
- [ ] A Telegram Bot token (you've done this before)
- [ ] Anthropic API key (get at console.anthropic.com)
- [ ] Meta Business Manager account + Facebook Page + Instagram Business account
- [ ] Meta Developer App with `instagram_basic`, `instagram_content_publish`, `pages_manage_posts` permissions

---

## Step 1 — Telegram Bot Setup

1. Open Telegram, message **@BotFather**
2. Send `/newbot`, name it "IronRoot Content Bot" (or similar)
3. Copy the **bot token** — save it as `TELEGRAM_BOT_TOKEN` in n8n credentials
4. Send `/start` to your new bot
5. Get your personal **chat ID**:
   - Message the bot anything
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Find `"chat":{"id": XXXXXXXXX}` — that's your chat ID
   - Save it as `TELEGRAM_CHAT_ID` in n8n env variables

---

## Step 2 — Anthropic API

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. In n8n: **Settings → Credentials → New → Header Auth**
   - Name: `Anthropic API`
   - Header name: `x-api-key`
   - Header value: your API key
4. Also add a second header credential or use Generic HTTP:
   - `anthropic-version: 2023-06-01`

---

## Step 3 — Meta Graph API Setup

### 3a. Create a Meta App
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create a new App → type: Business
3. Add products: **Instagram Graph API** and **Pages API**

### 3b. Get a Long-Lived Page Access Token
1. In the Graph API Explorer, select your app
2. Generate a User Access Token with these permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `instagram_basic`
   - `instagram_content_publish`
3. Exchange for a long-lived token (valid 60 days):
   ```
   GET https://graph.facebook.com/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id=YOUR_APP_ID
     &client_secret=YOUR_APP_SECRET
     &fb_exchange_token=SHORT_LIVED_TOKEN
   ```
4. Then get your Page Access Token (never expires):
   ```
   GET https://graph.facebook.com/me/accounts?access_token=LONG_LIVED_USER_TOKEN
   ```
5. Save the **Page Access Token** and your **Instagram Business Account ID** (found in Meta Business Settings → Instagram accounts → Account ID)

### 3c. Store in n8n
In n8n credentials, create a **Generic HTTP** credential or store as environment variables:
- `META_PAGE_ACCESS_TOKEN`
- `META_PAGE_ID`
- `INSTAGRAM_BUSINESS_ACCOUNT_ID`

---

## Step 4 — Import the n8n Workflow

Import `n8n_workflow.json` (in this same folder) directly into your n8n instance:
1. Open n8n → **Workflows → Import from File**
2. Select `n8n_workflow.json`
3. Update all credential references to match what you created above
4. Activate the workflow

---

## Step 5 — How to Use It

**Sending content for approval:**
1. Open Telegram, go to your IronRoot bot
2. Send any product photo (from your phone or forward from anywhere)
3. Wait ~15 seconds
4. You'll receive a formatted message with all 4 content versions

**Approving content:**
- Reply `✅` to schedule and post
- Reply `✏️ [your feedback]` to regenerate with adjustments (e.g., "✏️ make it shorter and more urgent")
- Reply `❌` to discard

**What gets posted automatically:**
- Instagram photo post with caption
- Facebook page post with caption + store link
- TikTok: you receive the script + image ready for manual recording (until video automation is added)

---

## Step 6 — Posting Schedule Logic

When you approve, n8n checks what slots are already filled and schedules to the next open slot:

| Priority | Platform | Time (EST) |
|----------|----------|------------|
| 1 | Instagram | Mon/Wed/Fri at 9am |
| 2 | Facebook | Mon/Wed/Fri at 10am (30 min after IG) |
| 3 | Instagram (2nd) | Tue/Thu/Sat at 12pm |
| 4 | Facebook (2nd) | Tue/Thu at 1pm |

This is managed via a simple Google Sheet or Airtable (free) acting as a schedule tracker — n8n reads it before scheduling each post.

---

## Troubleshooting

**"Telegram not receiving messages"**: Make sure your n8n webhook URL is publicly accessible. On Hetzner, ensure port 5678 (or your custom port) is open and the webhook is registered.

**"Meta API returning 190 error"**: Your access token has expired. Regenerate it (see Step 3b). Consider setting a monthly calendar reminder to refresh it.

**"Claude API not responding"**: Check your API key in n8n credentials. Also verify you have credits in your Anthropic account.

**"Instagram container stuck in IN_PROGRESS"**: Wait 30 seconds between creating the container and publishing. The workflow already has a Wait node for this.

---

## Costs

| Service | Cost |
|---------|------|
| n8n (self-hosted, Hetzner) | ~€5–10/mo (your existing server) |
| Anthropic Claude API | ~$0.01–0.05 per content batch (very cheap) |
| Meta Ads | €300/mo (your budget) |
| Runway/Pika (optional, for video) | $12–15/mo |
| **Total excl. ads** | ~€15–25/mo |
