import os
import subprocess
import streamlit as st
from dotenv import load_dotenv
import tempfile
from groq import Groq

# Load environment variables
load_dotenv()
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def clone_repository(repo_url, clone_dir):
    try:
        subprocess.run(['git', 'clone', repo_url, clone_dir], check=True)
    except subprocess.CalledProcessError:
        return False
    return True

def limit_content(content, max_lines=10):
    """Limit the content to the first `max_lines` lines."""
    return "\n".join(content.splitlines()[:max_lines])

def summarize_file(file_path):
    """Summarize the contents of a file."""
    return f"This file contains functionality related to {os.path.basename(file_path)}."

def generate_readme(directory):
    readme_content = ""
    all_responses = []
    first_file = True  # Flag to track the first iteration

    # Add the required file extensions in the list
    file_extensions = ['.py', '.kt', '.java', '.c', '.cpp', '.txt']
    files_to_process = []

    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                files_to_process.append(os.path.join(root, file))

    for i in range(0, len(files_to_process), 2):
        for j in range(i, min(i + 2, len(files_to_process))):
            filename = files_to_process[j]

            # Decide whether to summarize or include content based on file size
            with open(filename, 'r') as file:
                content = file.read()
                # Limit content length
                if len(content.splitlines()) > 10:  # If more than 10 lines, summarize
                    content = summarize_file(filename)
                else:
                    content = limit_content(content)

                # Use different prompts for the first file and subsequent files
                if first_file:
                    prompt = f""""Generate a README for the following project details:

                 the readme file structure is 
                 ### project title
                 ### project description
                 ### Required libraries
                 ### steps to run
                 ### detailed explanation

                 here is the content:\n\n{content}
                    """
                    first_file = False  # Set the flag to False after the first iteration
                else:
                    prompt = f"""Provide a brief description for the project based on the following content:
                    Content from file: {content}

                    Please explain breifly with steps.
                    """

                try:
                    questions_response = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama3-8b-8192"
                    )
                    all_responses.append(questions_response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error generating README for {filename}: {e}")

    return '\n'.join(all_responses)

def main():
    st.title("GitHub README Generator")

    repo_url = st.text_input("Enter GitHub Repository URL:")
    if st.button("Generate README"):
        if repo_url:
            with tempfile.TemporaryDirectory() as temp_dir:
                if clone_repository(repo_url, temp_dir):
                    readme_content = generate_readme(temp_dir)

                    if readme_content:
                        # Save README to a .txt file
                        readme_file_path = os.path.join(temp_dir, 'README.txt')
                        with open(readme_file_path, 'w') as readme_file:
                            readme_file.write(readme_content)

                        # Provide download link for .txt file
                        with open(readme_file_path, 'rb') as f:
                            st.download_button("Download README.txt", f, file_name='README.txt')
                    else:
                        st.error("Failed to generate README content.")
                else:
                    st.error("Failed to clone the repository. Please check the URL.")
        else:
            st.error("Please enter a valid GitHub repository URL.")

if __name__ == "__main__":
    main()
