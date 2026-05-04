# Investment Tracker Setup

## Supabase Auth Setup (Required for invest_shared.html)

### 1. Enable Authentication

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project: `XXX`
3. Go to **Authentication** → **Providers** → **Email**
4. Enable **Email** provider

### 2. Create Users

1. Go to **Authentication** → **Users**
2. Click **Add user**
3. Enter email and password for each user (e.g., ravi@example.com)

### 3. Test User (No Auth Required)

The app includes a special **Test User** (`testuser@gmail.com`) that bypasses Supabase authentication entirely:

- **No setup required** - just login with `testuser@gmail.com` (any password works)
- **Dummy data** - pre-loaded with sample investments from `dummy_data.json`
- **Local storage** - data is saved to browser localStorage, not Supabase
- **Edit access** - test user can add/edit/delete their own dummy investments
- **Isolated view** - only sees the "Test User" tab with their own data

To customize the dummy data, edit `dummy_data.json` before logging in as test user.

### 3. Enable Row Level Security (Recommended)

1. Go to **SQL Editor**
2. Run this query:

```sql
-- Enable RLS on the table
ALTER TABLE portfolio_state ENABLE ROW LEVEL SECURITY;

-- Allow only authenticated users to access their data
CREATE POLICY "Auth users can access" ON portfolio_state
FOR ALL USING (auth.uid() IS NOT NULL);
```

### 4. Deploy to GitHub Pages

1. Create a `docs` folder in your repo
2. Copy `invest_shared.html` to `docs/index.html`
3. Go to repo **Settings** → **Pages**
4. Select `docs` folder as source
5. Your site will be at: `https://username.github.io/repo-name/`

## Features

- **Real authentication** - Not just a PIN, actual Supabase Auth
- **Cloud sync** - Data syncs across devices
- **Multiple users** - Can create separate accounts for Ravi and Supriya
- **Test User mode** - No-auth demo user with dummy data, perfect for testing

## Troubleshooting

### "Login failed" error
- Check email/password is correct
- Verify Email provider is enabled in Supabase

### "Sync Error" on login
- Check RLS policy is set correctly
- Verify `portfolio_state` table exists

### Data not loading
- Check browser console (F12) for errors
- Verify Supabase project is not paused