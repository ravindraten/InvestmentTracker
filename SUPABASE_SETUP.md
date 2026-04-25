# Supabase Backend Setup Guide

Follow these steps to enable real-time cloud syncing for your shared Investment Tracker.

## 1. Create a Supabase Project
1.  Go to [supabase.com](https://supabase.com) and sign in (or create a free account).
2.  Click **New Project** and select your organization.
3.  Name your project (e.g., `Investment Tracker`) and set a secure database password.
4.  Choose a region near you and click **Create New Project**. Wait about 1-2 minutes for it to initialize.

## 2. Initialize the Database Table
1.  In your Supabase Dashboard, look for the **SQL Editor** icon (square with `>_` symbol) on the left sidebar.
2.  Click **New Query** and paste the following SQL command:

```sql
-- Create the table to store your portfolio
create table portfolio_state (
  id text primary key,
  content jsonb,
  updated_at timestamp with time zone default now()
);

-- Enable Row Level Security (RLS)
alter table portfolio_state enable row level security;

-- Create a policy to allow anyone with the API key to read and write
-- (Simple setup for 2-person use)
create policy "Allow all access" on portfolio_state for all using (true) with check (true);
```

3.  Click **Run** (top right). You should see "Success. No rows returned."

## 3. Get Your API Credentials
1.  Click the **Project Settings** (gear icon) on the left sidebar.
2.  Go to the **API** tab.
3.  Under **Project API keys**, find the `anon / public` key and copy it.
4.  Under **Project URL**, copy the `URL`.

## 4. Update the App Code
Open `invest_shared.html` and scroll down to the `<script>` section (around line 1320). Fill in your copied credentials:

```javascript
// REPLACE THESE with your actual Supabase credentials
const SB_URL = 'https://your-project-id.supabase.co';
const SB_KEY = 'your-anon-key-here';
```

## 5. Verify
1.  Open `invest_shared.html` in your browser.
2.  Add a test entry.
3.  Refresh the page—if the entry is still there, it is successfully syncing to the cloud!
