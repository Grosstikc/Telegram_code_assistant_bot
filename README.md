# Telegram Bot

A feature-rich Telegram bot built in Python that manages projects, tasks, reminders, weather updates, and more. This bot also integrates with a PostgreSQL database for persistent storage and can be deployed easily on Render.com.

## Features

- **Projects Management:**  
  Add, view, and delete projects.

- **Tasks Management:**  
  Add, view, update, and delete tasks with status updates.

- **Reminders:**  
  Set daily reminders.

- **Weather Updates:**  
  Get one-time weather reports or schedule daily weather updates.

- **Extras:**  
  Receive motivational quotes, use a Pomodoro timer, and more.

- **Interactive Inline Menus:**  
  Navigate using inline keyboards with "Back" and "Main Menu" options.

## Installation

### Prerequisites

- Python 3.8 or higher
- Git

### Clone the Repository

```bash
git clone https://github.com/yourusername/telegram-bot.git
cd telegram-bot
```

### Install Dependencies

Set up a virtual environment and install required packages:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Create a `.env` file (or use your preferred method) to securely set your environment variables. At a minimum, you'll need:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
- `DATABASE_URL`: Your PostgreSQL connection string (e.g., `postgres://username:password@host:port/database_name`).

Example `.env` file:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgres://username:password@host:port/database_name
```

Ensure your code loads these variables using a library like [python-dotenv](https://pypi.org/project/python-dotenv/).

## Running Locally

To run your bot locally, execute:

```bash
python -m bot.main
```

Your bot should now be running and accessible via Telegram.

## Deployment on Render.com

Follow these steps to deploy your Telegram bot on Render.com:

1. **Push Your Code to GitHub:**

   ```bash
   git add .
   git commit -m "Prepare bot for deployment"
   git push -u origin main
   ```

2. **Create a New Service on Render.com:**

   - Log in to [Render.com](https://render.com).
   - Click **New** and choose either a **Web Service** (if using webhooks) or a **Worker Service** (for background processing).
   - Connect your GitHub account and select the `telegram-bot` repository.

3. **Configure Build and Start Commands:**

   - **Build Command:**  
     Render automatically runs `pip install -r requirements.txt`.
   - **Start Command:**  
     Set the start command to:
     ```bash
     python -m bot.main
     ```
     Alternatively, create a `Procfile` with:
     ```
     worker: python -m bot.main
     ```

4. **Set Environment Variables on Render:**

   In the Render dashboard for your service, add:
   - `TELEGRAM_BOT_TOKEN`
   - `DATABASE_URL`

5. **Deploy:**

   Click **Create Service**. Render will build and deploy your bot automatically. Check Render's logs to verify a successful deployment.

## Database Sharing & Security

### Using a Single PostgreSQL Database for Multiple Projects

- **Connection Sharing:**  
  Both your web portfolio and your Telegram bot can use the same `DATABASE_URL` as long as their tables do not conflict.
  
- **Schema or Table Separation:**  
  To avoid conflicts, consider:
  - **Separate Schemas:** Create a separate schema for your bot (e.g., `bot`) by running:
    ```sql
    CREATE SCHEMA bot;
    ```
    Then modify your database initialization scripts to create tables under the `bot` schema (e.g., `CREATE TABLE bot.tasks (...)`).
  - **Table Prefixes:** Alternatively, prefix your bot’s table names (e.g., `bot_tasks`, `bot_projects`).

### Security Best Practices

- **Secrets Management:**  
  - Store sensitive data (tokens, connection strings) in environment variables.
  - Do not commit your `.env` file to your repository.
  
- **Webhook Security:**  
  - If using webhooks, ensure your endpoint uses HTTPS with a valid SSL certificate.
  - Validate incoming requests if possible.

- **Database Security:**  
  - Use parameterized queries to avoid SQL injection.
  - Use dedicated database users with minimal privileges for each project.
  - Regularly back up your PostgreSQL database using your provider’s backup features or tools like `pg_dump`.

- **Monitoring & Logging:**  
  - Monitor your Render logs and set up alerts for critical errors.
  - Implement robust error handling in your code.

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch with your feature or bug fix.
3. Commit your changes and push your branch.
4. Open a pull request describing your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
