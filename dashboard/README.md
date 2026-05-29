# Podex AI Dashboard

A Streamlit dashboard for browsing and searching your podcast library.

## Running Locally with Docker

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running
- A `.env` file in the `dashboard` directory

### Steps

1. Navigate to the `dashboard` directory:

   ```bash
   cd dashboard
   ```

2. Make the script executable (first time only):

   ```bash
   chmod +x run.sh
   ```

3. Run the script:

   ```bash
   ./run.sh
   ```

The script will:
1. Build the Docker image for `linux/amd64` (AWS-compatible)
2. Stop and remove any existing container
3. Start the container in the background on port `8501`

4. Open the app at [http://localhost:8501](http://localhost:8501)

### Stopping the Container

```bash
docker stop podcast-dashboard
```

## Environment Variables

The app expects a `.env` file in the `dashboard` directory (alongside `run.sh`). Create one based on your configuration:

```bash
cp .env.example .env
```
