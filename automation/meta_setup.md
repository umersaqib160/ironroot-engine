# Connecting Instagram and Facebook

Everything on the engine side is built. What is left is account setup, and only
you can do it — it needs your logins, and Claude never enters credentials.

Budget about 40 minutes. Do it in one sitting; the steps depend on each other.

At the end you will have three values to paste into GitHub. Keep a notepad open.

---

## Before you start

You need a **Facebook Page** for IronRoot, and an **Instagram professional
account** (Business or Creator) linked to it. Instagram will not let anything
publish through the API from a personal account, and it requires the Page even
if you never post to Facebook.

If you already have both and they are linked, skip to Step 3.

---

## Step 1 — The Facebook Page

1. facebook.com → Menu → **Pages** → **Create new Page**
2. Name: **IronRoot**. Category: *Kitchen/Cooking Supplies* (or similar).
3. Add the logo and the store link. It does not need to be pretty today.

## Step 2 — Instagram, as a professional account

1. In the Instagram app: **Settings → Account type and tools → Switch to
   professional account**
2. Choose **Business**. Category: *Product/Service*.
3. Still in there: **Link a Facebook Page** → pick the IronRoot Page.

Check it took: on the Page, **Settings → Linked accounts → Instagram** should
show your account.

## Step 3 — A Meta developer app

1. developers.facebook.com → **My Apps** → **Create App**
2. Use case: **Other** → type: **Business**
3. Name it `IronRoot Publisher`. Contact email: yours.
4. On the dashboard, **Add products**: add **Instagram** and **Facebook Login
   for Business**.

Leave the app in **Development** mode. It can already act on Pages and
Instagram accounts that you administer, which is all we need. App Review is for
acting on *other people's* accounts.

## Step 4 — The three values

Open the **Graph API Explorer**: developers.facebook.com/tools/explorer

1. Top right, **Meta App**: choose `IronRoot Publisher`.
2. **User or Page Token** → **Get User Access Token**.
3. Tick these permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `instagram_basic`
   - `instagram_content_publish`
4. **Generate Access Token** and accept the prompts. Choose the IronRoot Page
   when it asks which Pages to allow.

Now run three queries in the Explorer — type the path into the bar and press
Submit.

**a) Your Page ID and its token**

    me/accounts

Find IronRoot in the result. Copy its `id` — that is **META_PAGE_ID**. Copy its
`access_token` too; the next step needs it.

**b) The Instagram account ID**

Paste the Page's `access_token` into the token box first, then run:

    <META_PAGE_ID>?fields=instagram_business_account

The `id` inside `instagram_business_account` is **META_IG_USER_ID**.

**c) A token that does not expire in an hour**

The token you have lasts about an hour. Swap it for a long-lived one:

    oauth/access_token?grant_type=fb_exchange_token&client_id=<APP_ID>&client_secret=<APP_SECRET>&fb_exchange_token=<THE_PAGE_TOKEN>

App ID and App Secret are on the app dashboard under **App settings → Basic**.

Take the `access_token` from the result — that is **META_ACCESS_TOKEN**.

A long-lived *Page* token obtained this way does not expire on a timer, but it
does die if you change your Facebook password, remove the app, or Meta forces a
re-auth. If posting suddenly starts failing with an auth error, redo this step.

## Step 5 — Put them in GitHub

github.com/umersaqib160/ironroot-engine → **Settings → Secrets and variables →
Actions → New repository secret**. Three of them, names exactly:

| Name | What it is |
|------|-----------|
| `META_PAGE_ID` | from step 4a |
| `META_IG_USER_ID` | from step 4b |
| `META_ACCESS_TOKEN` | from step 4c |

---

## Step 6 — Prove it works before it matters

**Actions → Daily post → Run workflow.** Leave *dry run* ticked, set the date to
a day that has a post — `2026-10-02`, say.

It will print the image URL and both captions and send nothing. Open the image
URL in a browser: if it does not load for you, Instagram cannot load it either,
and that is the single most common reason this fails.

Then untick *dry run* and run it again on the same date. That posts for real —
on purpose. Better to find a broken token on a Thursday in September than on the
morning of 2 October.

If something is wrong, it opens an issue with the log. Re-running is always
safe: what has already gone out is recorded and skipped.

---

## What happens after that

Nothing, from you. The schedule runs at 15:00 UTC every day, posts the item due
that date, and does nothing on the days with none.

To stop it: create a file called `engine/HALT` in the repo. Delete it to resume.

## Notes

- **The repo has to stay public.** Instagram fetches the image from the repo's
  own raw URL. Make the repo private and posting breaks.
- **Approval is enforced.** A month without an `APPROVED` file posts nothing,
  and that file is written only when you comment `approve` on its issue.
- **Nothing posts twice.** Each publish is recorded in `posted.json`.
