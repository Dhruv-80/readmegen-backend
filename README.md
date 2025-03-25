# README: Generic README Generator

## 1. Overview

This project is a Flask-based API that generates README files for GitHub repositories.  It leverages the Google Gemini API (likely for natural language processing to create the README content) and the GitHub API to retrieve repository information. The generated README is cached for 24 hours to improve performance. The application is deployed using Vercel.

Refer https://github.com/Dhruv-80/readme-gen for frontend
## 2. Project Structure

* **`app.py`**: The main Flask application file containing the API endpoint `/generate-readme`. This file handles requests, interacts with the GitHub and Gemini APIs, manages caching, and returns the generated README content.
* **`.env.example`**:  A sample environment file showing the required variables: `GEMINI_API_KEY` and `GITHUB_API_KEY`.  This file should be copied and renamed to `.env` with your actual API keys.
* **`requirements.txt`**: Lists the project's dependencies, including Flask, Flask-CORS, the Google Generative AI library, PyGithub, and python-dotenv.
* **`vercel.json`**: A Vercel configuration file specifying the build process (using the `@vercel/python` builder) and routing for the application.  It also sets the `FLASK_ENV` environment variable to `production`.

<img width="1440" alt="Screenshot 2025-03-25 at 8 40 28 PM" src="https://github.com/user-attachments/assets/9c64301b-3b93-43a4-bc3d-cd909bedd95f" />
<img width="1440" alt="Screenshot 2025-03-25 at 8 41 00 PM" src="https://github.com/user-attachments/assets/272c0dc5-afb0-41ec-a704-6db86ee17fee" />



## 3. Installation

1. **Clone the repository:** `git clone <repository_url>`
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Create a `.env` file:** Copy `.env.example` and rename it to `.env`.  Replace the placeholder API keys with your actual Google Gemini and GitHub API keys.
4. **(Optional) Set up a Vercel deployment:** Follow Vercel's documentation to deploy this application.

## 4. Usage

The application exposes a single POST endpoint: `/generate-readme`.  To use it:

1. Send a POST request to `/generate-readme` with a JSON payload containing the `repo_name` field:

   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"repo_name": "owner/repository"}' http://localhost:PORT/generate-readme
   ```

   Replace `"owner/repository"` with the full name of the GitHub repository (e.g., "google/google-api-python-client").  Replace `PORT` with the port your application runs on (default is 5000).

2. The response will be a JSON object containing the generated README content or an error message.

   * Success:  The response will contain the `readme` field with the generated README content.
   * Error: The response will contain an `error` field describing the problem.


## 5. Contributing

Contributions are welcome! Please open an issue or submit a pull request.



## 6. Contact

For questions or feedback, please contact naadamunid@gmail.com


## 7. Acknowledgements

* **Flask:** A lightweight and flexible Python web framework.
* **Flask-CORS:** Enables Cross-Origin Resource Sharing (CORS).
* **Google Generative AI:** Provides large language model capabilities.
* **PyGithub:** A Python library for interacting with the GitHub API.
* **python-dotenv:**  Loads environment variables from a `.env` file.
* **Vercel:** Serverless platform for deploying the application.


