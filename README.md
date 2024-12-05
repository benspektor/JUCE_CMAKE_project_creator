# JUCE_CMAKE_project_creator

This Python script automates the creation of a JUCE-based audio plugin project using CMake. It simplifies the process by cloning the JUCE framework, copying a project template, and customizing the configuration.

## Features
- Clones the JUCE framework from GitHub.
- Copies a JUCE template project to a new location.
- Configures project-specific details such as project name, product name, manufacturer code, and plugin code.
- Outputs a ready-to-use JUCE project configured with CMake.

## Requirements
- Python 3.x
- Git installed and accessible in the system PATH.
- A JUCE project template directory available on your machine.

## Configuration
The script uses the following configuration variables:

- `JUCE_REPO_URL`: URL of the JUCE Git repository.
- `TEMPLATE_FOLDER`: Path to the JUCE project template folder (e.g., an example audio plugin project).
- `TARGET_FOLDER`: Path to the directory where the new project will be created.
- `PROJECT_NAME`: Name of the new project.
- `PRODUCT_NAME`: Display name for the plugin in the DAW.
- `PLUGIN_MANUFACTURER_CODE`: Custom manufacturer code for the plugin.
- `PLUGIN_CODE`: Unique code for the plugin.

Update these variables in the script to match your desired configuration.

## Usage
1. Clone this repository or copy the script to your local environment.
2. Open the script and update the configuration variables:
    - `TEMPLATE_FOLDER`
    - `TARGET_FOLDER`
    - `PROJECT_NAME`
    - `PRODUCT_NAME`
    - `PLUGIN_MANUFACTURER_CODE`
    - `PLUGIN_CODE`
3. Run the script:

    ```bash
    python JUCE_CMAKE_project_creator.py
    ```

4. The script will:
    - Copy the template project to the specified `TARGET_FOLDER`.
    - Replace placeholder values in the template with your configured values.
    - Clone the JUCE framework into the new project folder.

## Output
- A new folder will be created in `TARGET_FOLDER` with the name specified in `PROJECT_NAME`.
- The folder contains:
  - The customized JUCE project files.
  - The JUCE framework cloned as a subdirectory.

## Example
**Configuration:**
```python
TEMPLATE_FOLDER = "/Users/benspector/Frameworks/JUCE/examples/CMake/AudioPlugin"
TARGET_FOLDER = "/Users/benspector/Work/JUCE_projects"
PROJECT_NAME = "MyJUCEProject"
PRODUCT_NAME = "My JUCE Project"
PLUGIN_MANUFACTURER_CODE = "MyCo"
PLUGIN_CODE = "Dem0"
```

**Command:**
```bash
python create_juce_project.py
```

**Result:**
The script generates a new folder named `MyJUCEProject` under `/Users/benspector/Work/JUCE_projects` with all configurations applied.

## Notes
- Ensure that the `TEMPLATE_FOLDER` points to a valid JUCE example project.
- Update the `PLUGIN_MANUFACTURER_CODE` and `PLUGIN_CODE` to ensure they are unique for your plugin.
- If the target project folder already exists, the script will not overwrite it.

## License
This script is provided "as is" without warranty of any kind. Use it at your own risk.

