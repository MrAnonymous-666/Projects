# Smart Task Management System — Full Stack Setup

## Folder structure (organized for VS Code / GitHub navigation)
```
task-manager/
  frontend/          -> index.html (HTML + CSS + JS all in one file)
    index.html
    config.js          -> SINGLE PLACE to set the API URL (web/desktop/mobile all read this)
    manifest.json     -> makes it an installable PWA
    service-worker.js -> offline app-shell caching
    icon-192.png / icon-512.png

  database/           -> everything related to MongoDB
    connection.js      -> connects to MongoDB
    User.js             -> user schema/model
    Task.js              -> task schema/model

  api/                 -> everything related to the REST API routes
    authRoutes.js        -> /api/auth/register, /api/auth/login
    taskRoutes.js          -> /api/tasks (GET/POST/PUT/DELETE)

  middleware/
    authMiddleware.js     -> verifies JWT token on protected routes

  desktop/               -> Electron wrapper for Windows/Mac/Linux apps
    main.js
    package.json

  mobile/                 -> Capacitor wrapper for Android/iOS apps
    capacitor.config.json
    package.json

  server.js              -> starts the Express server (entry point)
  package.json            -> backend dependencies
  .env.example             -> copy to .env and fill in your own values
  .gitignore                -> keeps node_modules and .env out of GitHub
```

## What changed from your original version
- Tasks now live in **MongoDB** instead of `localStorage`, so they're saved
  permanently and accessible across devices.
- Added **login/register** with JWT authentication — each user only sees
  their own tasks.
- Frontend now talks to the backend via `fetch()` calls to a REST API.

## 1. Set up MongoDB (free)
1. Go to https://www.mongodb.com/cloud/atlas and create a free account.
2. Create a free (M0) cluster.
3. Under "Database Access", create a user with a password.
4. Under "Network Access", allow access from anywhere (0.0.0.0/0) for
   development.
5. Click "Connect" -> "Drivers" and copy the connection string. It looks like:
   `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/`

## 2. Configure the backend
```bash
cp .env.example .env
```
Open `.env` and paste your MongoDB connection string into `MONGO_URI`
(add `taskmanager` as the database name at the end of the URL), and set
`JWT_SECRET` to any long random string.

## 3. Install and run the backend
```bash
npm install
npm run dev
```
You should see `MongoDB connected` and `Server running on port 5000`.

## 4. Run the frontend
Just open `frontend/index.html` in your browser (or serve it with the
VS Code "Live Server" extension). It's already configured to call
`http://localhost:5000/api`.

## 5. Test it
1. Open the page, click "Need an account? Register", create a user.
2. You'll be logged in automatically and can start adding tasks.
3. Refresh the page — you're still logged in and tasks persist.
4. Open the app in a different browser or incognito window, register a
   second user — they'll have a completely separate task list.

## API Reference
| Method | Endpoint                    | Auth required | Description               |
|--------|------------------------------|---------------|-----------------------------|
| POST   | /api/auth/register           | No            | Create a new account        |
| POST   | /api/auth/login               | No            | Log in, get JWT token       |
| POST   | /api/auth/forgot-password       | No            | Request a 6-digit OTP by email |
| POST   | /api/auth/reset-password          | No            | Verify OTP, set a new password |
| GET    | /api/tasks                          | Yes           | Get your tasks               |
| POST   | /api/tasks                            | Yes           | Create a task                 |
| PUT    | /api/tasks/:id                          | Yes           | Update/complete a task        |
| DELETE | /api/tasks/:id                            | Yes           | Delete a task                  |

All protected routes require a header:
`Authorization: Bearer <token>`

## Setting up "Forgot Password" (Email OTP)
This uses Gmail's free SMTP to send OTP emails - no paid service needed.

1. Use a Gmail account (create a free one if you don't want to use your
   personal one for this).
2. Turn on 2-Step Verification on that Google account:
   https://myaccount.google.com/security
3. Once 2-Step Verification is on, go to:
   https://myaccount.google.com/apppasswords
4. Create an App Password (choose "Mail" as the app). Google gives you a
   16-character password - copy it.
5. In your `.env` file, set:
   ```
   EMAIL_USER=your_gmail_address@gmail.com
   EMAIL_PASS=the_16_character_app_password
   ```
   **Important**: `EMAIL_PASS` is the App Password Google generated, NOT
   your normal Gmail login password. Your real Gmail password will not
   work here and Google will reject it.
6. Restart the backend (`npm run dev`). Test it: on the login screen,
   click "Forgot Password?", enter a registered email, and check that
   inbox for the OTP.

**Free tier limit:** Gmail SMTP allows roughly 500 emails/day for free -
more than enough for a college project or small user base. If you ever
outgrow this, free tiers of Brevo (300 emails/day) or Resend are drop-in
alternatives that only require changing `database/emailService.js`.

**Security note already built in:** the `/forgot-password` endpoint
always returns the same message whether or not the email exists in the
database. This is intentional - it stops someone from using this form to
check which emails have accounts on your app.

## Pushing this to GitHub
```bash
cd task-manager
git init
git add .
git commit -m "Initial commit: Smart Task Manager full stack"
```
Then create an empty repo on GitHub (no README/gitignore, since you
already have them), and:
```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```
Because of `.gitignore`, your real `.env` (with secrets) and `node_modules`
will NOT be uploaded — anyone cloning your repo just copies
`.env.example` to `.env` and fills in their own values, exactly like you
did in Step 2.

## Deploying (optional, makes it demo-able from anywhere)
- **Backend**: Render.com or Railway.app (free tier) — connect your GitHub
  repo, set the same environment variables there.
- **Frontend**: Netlify or Vercel (free) — but update `API_URL` in
  `index.html` to your deployed backend URL first.

## Ideas to push it further for extra credit
- Add due-date reminder emails (Nodemailer + a daily cron job)
- Add a stats/analytics page (tasks completed per week)
- Add task sharing/assignment between users
- Add file attachments per task (Multer + cloud storage)

## Now it's a PWA (installable app)
Your frontend now has `manifest.json`, `service-worker.js`, and app icons.
This means it can be **installed like a real app** on phones, tablets, and
desktops — no App Store needed.

**Important:** service workers require HTTPS (or `localhost`). It will NOT
work if you just double-click `index.html` (a `file://` URL). Serve it
properly:
```bash
cd frontend
npx serve .
```
Then open the printed `http://localhost:xxxx` URL.

### To install it:
- **Android (Chrome)**: open the site -> tap the "Install App" button that
  appears, or use the browser menu -> "Add to Home screen"
- **iPhone (Safari)**: open the site -> tap Share -> "Add to Home Screen"
  (iOS doesn't support the auto-prompt, this manual step is required)
- **Desktop (Chrome/Edge)**: an install icon appears in the address bar, or
  use the "Install App" button

Once installed, it opens in its own window with no browser bar, has a home
screen/app-drawer icon, and the app shell loads instantly (even briefly
offline) — task data itself still needs internet since it comes live from
your API.

### Want a real Android APK (installable from Play Store or as a file)?
Once deployed (frontend + backend both live on the internet, not
localhost), you can wrap this same PWA into a native Android app in a few
commands using **Capacitor**:
```bash
npm install @capacitor/core @capacitor/cli
npx cap init "Smart Task Manager" "com.yourname.taskmanager"
npx cap add android
npx cap open android
```
This opens the project in Android Studio, where you can run it on an
emulator/phone or build a signed `.apk`/`.aab` for the Play Store. No code
rewrite needed — same HTML/CSS/JS.

## One app, all 5 platforms (Android, iOS, Windows, Mac, Linux)
You don't need to rebuild anything — the same `frontend/` folder becomes
every native app. The pattern is:
- **Capacitor** (`mobile/` folder, already set up) -> Android + iOS
- **Electron** (`desktop/` folder, already set up) -> Windows + Mac + Linux
- All of them just load your existing `frontend/index.html`

### Step 0 (required first): deploy your backend, then update ONE file
A native app on someone's phone or laptop can't reach `localhost:5000` —
that only exists on your dev machine. Deploy the `backend` (the root
`server.js` + `api/` + `database/` + `middleware/`) to Render.com or
Railway.app (free tier), then open `frontend/config.js` and change the
one line:
```js
const API_URL = "https://your-app-name.onrender.com/api";
```
That's it — web, PWA, desktop, and mobile all read from this same file,
so you only ever update it in this one place.

### Windows / Mac / Linux — the `desktop/` folder (already set up)
```bash
cd desktop
npm install
npm start          # test it as a desktop app right now
```
To produce installers:
```bash
npm run build:win     # -> dist/*.exe  (run this on Windows, or use CI)
npm run build:mac     # -> dist/*.dmg  (must be run on a Mac)
npm run build:linux   # -> dist/*.AppImage and .deb
```
`electron-builder` can only reliably build Mac installers on a Mac, and
Windows installers are best built on Windows. If you only have one OS,
GitHub Actions (free) can build all three — ask me if you want that
workflow file.

### Android / iOS — the `mobile/` folder (already set up)
```bash
cd mobile
npm install
npm run add:android      # generates the android/ native project
npm run add:ios          # generates the ios/ native project (Mac only)
npm run sync              # copies frontend/ into both native projects
npm run open:android        # opens Android Studio -> Run or Build APK
npm run open:ios              # opens Xcode -> Run or Archive (Mac only)
```
Whenever you change anything in `frontend/`, re-run `npm run sync` inside
`mobile/` to push those changes into the native projects.

- Android: works on Windows/Mac/Linux, needs Android Studio installed.
- iOS: **must** be built on a Mac with Xcode — an Apple platform
  requirement, not something any tool can bypass. If you don't have a
  Mac, cloud Mac services (e.g. MacStadium, GitHub Actions macOS
  runners) can build it for you.
- To publish (not required for a college practical — running it on an
  emulator/your own device is enough): Android needs a one-time $25
  Google Play registration, iOS needs a $99/year Apple Developer account.

### Summary table
| Platform | Tool       | Can build on           | Output              |
|----------|-----------|--------------------------|----------------------|
| Android  | Capacitor | Windows/Mac/Linux        | `.apk` / `.aab`       |
| iOS      | Capacitor | Mac only (Xcode)         | `.ipa`                 |
| Windows  | Electron  | Windows (best)            | `.exe`                |
| Mac      | Electron  | Mac only (best)           | `.dmg`                 |
| Linux    | Electron  | Windows/Mac/Linux         | `.AppImage` / `.deb`  |
