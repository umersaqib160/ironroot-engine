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

**You probably have this already.** In July the IronRoot Page and the
`ironrootstore` Instagram account were both verified inside the
**"Shopify: ironrootnl"** business portfolio. Check it rather than redo it:
business.facebook.com → Settings → Accounts → Pages / Instagram accounts. If both
are there, skip straight to Step 3.

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
   - `business_management` — **needed because your Page belongs to the
     "Shopify: ironrootnl" business portfolio.** Without it, Meta hides
     portfolio-owned Pages from the lookup in 4b and it comes back empty.
4. **Generate Access Token** and accept the prompts. When it asks which Pages
   and Instagram accounts to allow, choose IronRoot and ironrootstore.

You now have a **user** token that dies in about an hour. The order below
matters — the Page token you want must be fetched *with a long-lived user
token*, or it expires too.

**a) Make the user token long-lived**

App ID and App Secret are on the app dashboard under **App settings → Basic**.
Put this in the Explorer bar (it is a GET) and Submit:

    oauth/access_token?grant_type=fb_exchange_token&client_id=<APP_ID>&client_secret=<APP_SECRET>&fb_exchange_token=<THE_USER_TOKEN_FROM_STEP_3>

Copy the `access_token` from the result, paste it into the Explorer's token box
at the top, replacing the old one.

**b) The Page ID and the Page token**

    me/accounts?fields=id,name,access_token,instagram_business_account

Find IronRoot. From that entry:

- `id` → **META_PAGE_ID**
- `access_token` → **META_ACCESS_TOKEN** — because it was fetched with a
  long-lived user token, this Page token **does not expire**
- `instagram_business_account.id` → **META_IG_USER_ID**

**If IronRoot is not in the list** (the result is empty or it is missing), it is
the portfolio issue. Use this instead — same three fields, found through the
business:

    me/businesses?fields=name,owned_pages{id,name,access_token,instagram_business_account}

**If `instagram_business_account` is missing** from the IronRoot entry, the
Instagram account is not linked to the Page as a professional account — go back
to Step 2.

An earlier version of this guide said to run the exchange in (a) on the *Page*
token. That does not work — Meta only exchanges user tokens — and would have
left you with a token that died within the hour.

The Page token lasts until you change your Facebook password, remove the app, or
Meta forces you to log in again. If posting suddenly starts failing with an
authentication error, redo this step.

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
