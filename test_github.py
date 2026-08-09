from github_client import fetch_file_from_github
import os
content = fetch_file_from_github(
    owner="Kesavan-v-git",
    repo="Swiggy-Clone1",
    file_path="Swiggy/index.html",
    token=os.getenv("GITHUB_TOKEN")
)

print(content)