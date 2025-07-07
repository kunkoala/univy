<a href="https://next-starter-skolaczk.vercel.app/">
<img src="/public/opengraph-image.jpg" alt="thumbnail">
</a>
<p align="center">
  <a href="#-features"><strong>Features</strong></a> ·
  <a href="#-deployment"><strong>Deployment</strong></a> ·
  <a href="#-getting-started"><strong>Getting started</strong></a> ·
  <a href="#%EF%B8%8F-scripts-overview"><strong>Scripts overview</strong></a> ·
  <a href="#-contribution"><strong>Contribution</strong></a> ·
  <a href="#%EF%B8%8F-support"><strong>Support</strong></a>
</p>

## 🎉 Features
- 🚀 Next.js 15 (App router)
- ⚛️ React 19
- 📘 Typescript
- 🎨 Tailwind CSS 4 - Class sorting, merging and linting
- 🛠️ Shadcn/ui - Customizable UI components
- 💵 Stripe - Payment handler
- 🔒 Next-auth - Easy authentication library for Next.js (GitHub provider)
- 🛡️ Drizzle - ORM for node.js
- 🔍 Zod - Schema validation library
- 🧪 Jest & React Testing Library - Configured for unit testing
- 🎭 Playwright - Configured for e2e testing
- 📈 Absolute Import & Path Alias - Import components using `@/` prefix
- 💅 Prettier - Code formatter
- 🧹 Eslint - Code linting tool
- 🐶 Husky & Lint Staged - Run scripts on your staged files before they are committed
- 🔹 Icons - From Lucide
- 🌑 Dark mode - With next-themes
- 📝 Commitlint - Lint your git commits
- 🤖 Github actions - Lint your code on PR
- ⚙️ T3-env - Manage your environment variables
- 🗺️ Sitemap & robots.txt
- 💯 Perfect Lighthouse score
- 💾 Neon database

## 🎯 Getting started
### 1. Clone this template in one of three ways

1. Using this repository as template

   ![use-this-template-button](https://github.com/Skolaczk/next-starter/assets/76774237/f25c9a29-41de-4865-aa38-c032b9346169)

2. Using `create-next-app`

   ```bash
   npx create-next-app -e https://github.com/Skolaczk/next-starter my-project-name
   ```

3. Using `git clone`

   ```bash
   git clone https://github.com/Skolaczk/next-starter my-project-name
   ```
### 2. Install dependencies

```bash
npm install
```

### 3. Set up environment variables
Create `.env` file and set env variables from `.env.example` file.

### 4. Prepare husky
It is required if you want husky to work

```bash
npm run prepare
```

### 5. Run the dev server

You can start the server using this command:

```bash
npm run dev
```

and open http://localhost:3000/ to see this app.

## 📁 Project structure

```bash
.
├── .github                         # GitHub folder
├── .husky                          # Husky configuration
├── prisma                          # Prisma schema and migrations
├── public                          # Public assets folder
└── src
    ├── __tests__                   # Unit and e2e tests
    ├── actions                     # Server actions
    ├── app                         # Next JS App (App Router)
    ├── components                  # React components
    ├── lib                         # Functions and utilities
    ├── styles                      # Styles folder
    └── env.mjs                     # Env variables config file
```

## ⚙️ Scripts overview
The following scripts are available in the `package.json`:
- `dev`: Run development server
- `build`: Build the app
- `start`: Run production server
- `preview`: Run `build` and `start` commands together
- `lint`: Lint the code using Eslint
- `lint:fix`: Fix linting errors
- `format:check`: Checks the code for proper formatting
- `format:write`: Fix formatting issues
- `typecheck`: Type-check TypeScript without emitting files
- `test`: Run unit tests
- `test:watch`: Run unit tests in watch mode
- `e2e`: Run end-to-end tests
- `e2e:ui`: Run end-to-end tests with UI
- `postbuild`: Generate sitemap
- `prepare`: Install Husky for managing Git hooks

## 🤝 Contribution
To contribute, please follow these steps:
1. Fork the repository.
2. Create a new branch.
3. Make your changes, and commit them.
4. Push your changes to the forked repository.
5. Create a pull request.


## Database Setup (with Drizzle ORM)

This project uses [Drizzle ORM](https://orm.drizzle.team/) for database schema management and migrations.

### Codebase-First Approach

If you make changes to the database schema (e.g., edit `src/lib/schema.ts`):

1. **Install Drizzle Kit (if not already):**
   ```bash
   npm install -D drizzle-kit
   # or
   yarn add -D drizzle-kit
   ```

2. **Update your schema in `src/lib/schema.ts`.**

3. **Push schema changes to your database:**
   ```bash
   npx drizzle-kit push
   ```
   This will automatically update your database to match your codebase schema (rapid prototyping).

4. **(Optional) Generate migration files:**
   If you want to generate SQL migration files instead, use:
   ```bash
   npx drizzle-kit generate
   # Then apply with:
   npx drizzle-kit migrate
   ```

For more details, see the official Drizzle migration documentation:  
https://orm.drizzle.team/docs/migrations 