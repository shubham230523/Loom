# Model Context Protocol (MCP): Connecting AI to Your Data

The **Model Context Protocol (MCP)** is an open standard that enables AI models to securely and efficiently access external data sources and tools. Instead of copy-pasting data into a chat window, MCP allows your AI assistant to "browse" your databases, check your GitHub issues, or read your Figma designs directly.

## Why MCP is a Game-Changer
- **Real-Time Context:** The AI sees the current state of your database or project management tool.
- **Eliminates Manual Sync:** No more manual exports of logs or schemas.
- **Actionable Insights:** The AI can query data to answer complex questions (e.g., "Why is this specific user record failing validation?").

---

## Step 1: Connect to Local Databases (PostgreSQL / SQLite)

Connecting your AI to a database allows it to understand your schema and even run diagnostic queries.

### Setup (using MCP PostgreSQL Server):
1. **Install the MCP Server:**
   ```bash
   npm install -g @modelcontextprotocol/server-postgres
   ```
2. **Configure in IDE (e.g., Cursor/Claude Desktop):**
   Add the following to your MCP settings:
   ```json
   {
     "mcpServers": {
       "postgres": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:password@localhost:5432/database"]
       }
     }
   }
   ```
3. **Usage:**
   > "Look at the `orders` table in my local DB. Write a SQL query to find the top 5 customers by revenue in the last 30 days."

---

## Step 2: Integrate with Figma APIs

Enable your AI to "see" your design tokens, component properties, and layout structures.

### Setup:
1. **Get a Figma Personal Access Token:** From your Figma account settings.
2. **Configure MCP Figma Server:**
   ```json
   {
     "mcpServers": {
       "figma": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-figma"],
         "env": {
           "FIGMA_ACCESS_TOKEN": "your_token_here"
         }
       }
     }
   }
   ```
3. **Usage:**
   > "Read the 'Button' component from my Figma file. Generate the CSS variables for its primary and secondary states."

---

## Step 3: Connect to GitHub PRs and Issues

Let your AI help you manage your repository by reading issues and drafting pull request descriptions.

### Setup:
1. **Generate a GitHub Classic Token:** With `repo` scopes.
2. **Configure MCP GitHub Server:**
   ```json
   {
     "mcpServers": {
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
         }
       }
     }
   }
   ```
3. **Usage:**
   > "List all open issues labeled 'bug' in this repo. Summarize the root cause discussed in issue #123."

---

## Pro Tip: Security & Privacy
- **Read-Only Access:** Always use read-only credentials for databases.
- **Token Scoping:** Limit the scope of your GitHub and Figma tokens to only the repositories and files needed.
- **Local MCP Servers:** You can write your own custom MCP servers to expose internal internal tools safely to your AI co-pilot.
