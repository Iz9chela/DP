# Function to read API key from a file
def load_api_key(filename: str) -> str:
    try:
        with open(filename, "r") as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error: Could not read API key file. {e}")
        exit(1)