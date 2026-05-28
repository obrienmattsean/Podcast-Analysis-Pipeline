ENV_FILE="../.env"

echo "Building Docker image for Streamlit dashboard..."
docker buildx build --platform linux/amd64 --provenance=false -t podcast-dashboard:latest .

echo "Running Streamlit dashboard container..."
docker rm -f podcast-dashboard || true
docker run -d --name podcast-dashboard -p 8501:8501 --restart unless-stopped --env-file $ENV_FILE podcast-dashboard:latest
echo "Streamlit dashboard is running at http://localhost:8501"