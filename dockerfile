# Step 1: Start from an official NVIDIA base image that already has Python, PyTorch, and CUDA 12.1.
FROM nvcr.io/nvidia/pytorch:23.10-py3

# Step 2: Set the working directory inside the container.
WORKDIR /app

# Step 3: Copy only the list of requirements first.
# This is a Docker optimization technique.
COPY requirements.txt .

# Step 4: Install all the Python libraries from your list.
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Now, copy all your project files (Python scripts, model files, etc.) into the container.
COPY . .

# Step 6: Define the command that will run when the container starts.
# Replace 'main.py' with the actual name of your main Python script if it's different.
CMD ["python", "app.py"]

# docker run --gpus all -it --rm traffic-ai