# NYPTI AI Decision Summarizer

This application is a containerized backend service that automatically finds, filters, and summarizes court decisions from an existing MongoDB database. It is designed to run as a robust "Data Factory," processing a large backlog of decisions and monitoring for new ones as they arrive.

## Core Features

-   **Automated Processing:** Connects to a MongoDB database and processes documents in a continuous loop until no work is left.
-   **Intelligent Filtering:** Automatically identifies and skips non-criminal cases (i.e., not "People v...") to save on processing costs, marking them as `skipped_not_criminal`.
-   **Structured AI Analysis:** Executes a multi-step AI pipeline using the Google Gemini API to generate a high-quality, structured summary with sourced, verbatim quotes.
-   **Persistent Logging:** Creates a timestamped log file for each run, recording the IDs of all successfully summarized decisions.
-   **Cost Estimation:** Provides a detailed summary report upon completion, including the number of documents processed/skipped and the total estimated cost based on token usage.

## Prerequisites

-   Docker must be installed and running on the host machine.
-   Network access to the production MongoDB instance.
-   The MongoDB instance must contain a database (e.g., `nypti_database`) with a collection (e.g., `decisions`).

### Required Data Schema

The application expects each document in the `decisions` collection to have the following fields:
-   `_id`: A unique identifier for the decision (e.g., `2024.01234`).
-   `raw_html_text`: A string containing the full HTML content of the decision.
-   `is_summarized`: A **boolean** flag. The script will only process documents where this value is `false`.

## Configuration

The application is configured entirely through a `.env` file. Create a file named `.env` in the root of this project before running.

**Important:** The file must contain raw key-value pairs without any quotation marks.

### Required Environment Variables

| Variable | Description | Example Value |
| :--- | :--- | :--- |
| `MONGO_URL` | **Required.** The full connection string for the MongoDB database. Replace `<your-mongo-host>` with the actual hostname or IP of the database server. | `mongodb://<your-mongo-host>:27017/nypti_database` |
| `GEMINI_API_KEY`| **Required.** The API key for the Google Gemini service. | `AIzaSy...` |

## How to Build

To build the Docker image, navigate to the project's root directory in your terminal and run the following command. This will create an image named `nypti-summarizer`.

```bash
docker build -t nypti-summarizer .
```

## How to Run

Before running, create a `logs` directory in the project folder. The application will save its output logs here.

```bash
mkdir logs
```

Run the container using the following command. You must connect the container to a network that can reach your MongoDB server.

```bash
docker run --rm --env-file .env --network <your_docker_network> -v "$(pwd)/logs:/app/logs" nypti-summarizer
```

### Key Command Flags

-   `--rm`: Automatically removes the container when it stops.
-   `--env-file .env`: Loads the configuration variables from the `.env` file.
-   `--network <your_docker_network>`: **(CRITICAL)** You must replace `<your_docker_network>` with the name of a Docker network that has access to your MongoDB instance. For a database running on the same host, `--network host` is often the simplest option.
-   `-v "$(pwd)/logs:/app/logs"`: Mounts the local `logs` folder into the container, allowing the script to save its log file directly to your machine.

## Scaling Strategy (For Production)

This container is designed as a **single, stateless worker**. This is intentional.

For processing a large backlog (e.g., 300,000 decisions), the strategy is to run many of these containers **in parallel**. An orchestration service like **AWS Batch** or **Amazon ECS** should be used to manage this. The orchestrator would be responsible for starting hundreds of instances of this container, which will work together to process the queue of documents until no work is left.