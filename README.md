# Surface Watch

A React + Express + MongoDB web security dashboard. The scanner makes one bounded public-site GET request and reports TLS/certificate status, response security headers, cookie attributes, and basic server-header disclosure. It does not crawl, inject payloads, try credentials, or exploit vulnerabilities.

The scanner is split into simple parts: `server/scanner.js` runs the scan, `server/scanner/request.js` safely fetches the page, and `server/scanner/report.js` checks the response and creates the report.

## Run locally

1. Install Node.js 20 or newer.
2. Run `npm install`.
3. Copy `.env.example` to `.env`, then set `MONGODB_URI` to a MongoDB Atlas connection string and `SESSION_SECRET` to a long random value.
4. Run `npm run dev` and open the Vite URL printed in the terminal (normally `http://127.0.0.1:5173`).

New users can register from the dashboard. Account records and login sessions are stored in the connection's default database. Each account's scan history is stored in its own `surface_user_<user-id>` database, in a `scans` collection. The Atlas database user must be allowed to create and read/write these per-user databases; keep its connection string private in `.env`.

Reports saved before account support remain in the previous shared `scans` collection and are not automatically assigned to a new account.

## Production build

Run `npm run build`, then `npm start`. Set `SESSION_SECRET` before production use. The Express server serves the built React app and API on `PORT` (default `3001`).

## Scope and safety

The server binds to loopback only. Only HTTP/HTTPS URLs resolving exclusively to globally routable IP addresses are accepted. Each redirect is revalidated, and outbound sockets are pinned to a validated address to prevent DNS rebinding. Response reads are capped at 512 KiB and requests time out after 10 seconds. Use only against websites you own or are authorized to assess. Findings are configuration indicators, not a full penetration test.
