from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import os
import shutil

app = FastAPI()

# Setup templates and static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Get the current working directory
cwd = os.getcwd()

# Define folder paths based on `cwd`
source_folder = os.path.join(cwd, "Cloned_Project")
routers_destination = os.path.join(cwd, "src", "routers")
schemas_destination = os.path.join(cwd, "src", "schemas")

# Mapping of route names to directories
route_paths = {
    "routers": routers_destination,
    "schemas": schemas_destination,
    "cloned_project": source_folder
}

# Function to list files in a folder with an optional file extension filter
def list_files(folder_path: str, file_extension: Optional[str] = None) -> List[str]:
    all_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if not file_extension or file.endswith(file_extension):
                file_path = os.path.join(root, file)
                all_files.append(file_path)
    return all_files

# Function to read file content
def read_file_content(file_path: str) -> str:
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

# Function to copy selected files to a specified folder
def copy_selected_files(file_list: List[str], destination_folder: str):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    for file in file_list:
        file_name = os.path.basename(file)
        destination_path = os.path.join(destination_folder, file_name)
        shutil.copy(file, destination_path)


# Render the main page
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# API endpoint to list files in a specified route with an optional file extension
@app.get("/api/list-files/{route_name}")
async def list_files_endpoint(route_name: str, file_extension: Optional[str] = Query(None)):
    folder_path = route_paths.get(route_name)
    if not folder_path or not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Route folder not found")
    files = list_files(folder_path, file_extension)
    return {"files": files}

# API endpoint to retrieve file content
@app.get("/api/get-file-content")
async def get_file_content(file_path: str):
    content = read_file_content(file_path)
    return {"content": content}


# Endpoint to copy selected files to the 'routers' folder
@app.post("/copy-files-to-routers")
async def copy_files_to_routers(files: List[str]):
    if not os.path.exists(routers_destination):
        os.makedirs(routers_destination)
    try:
        copy_selected_files(files, routers_destination)
        return {"message": f"Copied {len(files)} files to '{routers_destination}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to copy selected files to the 'schemas' folder
@app.post("/copy-files-to-schemas")
async def copy_files_to_schemas(files: List[str]):
    if not os.path.exists(schemas_destination):
        os.makedirs(schemas_destination)
    try:
        copy_selected_files(files, schemas_destination)
        return {"message": f"Copied {len(files)} files to '{schemas_destination}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



