import os
import shutil
import subprocess

# Configuration
JUCE_REPO_URL = "https://github.com/juce-framework/JUCE.git"
# Replace with the path to your template folder
TEMPLATE_FOLDER = "/Users/benspector/Frameworks/JUCE/examples/CMake/AudioPlugin"
# Replace with the desired output folder
TARGET_FOLDER = "/Users/benspector/Work/JUCE_projects"
# Replace with the desired project name
PROJECT_NAME = "MyJUCEProject"
# Replace with the desired product name, that will be displayed in the DAW
PRODUCT_NAME = "My JUCE Project"
# Replace with the desired manufacturer code and plugin code
PLUGIN_MANUFACTURER_CODE = "MyCo"
PLUGIN_CODE = "Dem0"

# Function to clone JUCE


def clone_juce(target_project_path):
    juce_path = os.path.join(target_project_path, "JUCE")
    if not os.path.exists(juce_path):
        print(f"Cloning JUCE into {juce_path}...")
        subprocess.run(["git", "clone", JUCE_REPO_URL, juce_path], check=True)
    else:
        print("JUCE already cloned.")

# Function to copy and modify files


def copy_and_modify_template(template_path, target_path, project_name):
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template folder not found: {template_path}")

    print(f"Copying template folder from {template_path} to {target_path}...")
    shutil.copytree(template_path, target_path, dirs_exist_ok=True)

    # Modify files in the copied folder
    for root, _, files in os.walk(target_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".cpp") or file.endswith(".h"):
                with open(file_path, "r") as f:
                    content = f.read()
                # Replace "TemplateProject" with the new project name
                content = content.replace("TemplateProject", project_name)
                # Replace "AudioPluginAudioProcessor" with "$(PROJECT_NAME)AudioProcessor"
                content = content.replace(
                    "AudioPluginAudioProcessor", f"{project_name}AudioProcessor")
                with open(file_path, "w") as f:
                    f.write(content)
            elif file.endswith("CMakeLists.txt"):
                with open(file_path, "r") as f:
                    content = f.read()
                # Uncomment "add_subdirectory(JUCE)"
                content = content.replace(
                    "# add_subdirectory(JUCE)", "add_subdirectory(JUCE)")
                # Replace the project name in the CMakeLists.txt
                content = content.replace("TemplateProject", project_name)
                # Replace "AUDIO_PLUGIN_EXAMPLE" with the project name
                content = content.replace("AUDIO_PLUGIN_EXAMPLE", project_name)
                content = content.replace("Audio Plugin Example", PRODUCT_NAME)
                content = content.replace("PLUGIN_MANUFACTURER_CODE Juce", "PLUGIN_MANUFACTURER_CODE" + " " +
                                          PLUGIN_MANUFACTURER_CODE)
                content = content.replace("PLUGIN_CODE Dem0", "PLUGIN_CODE" + " " +
                                          PLUGIN_CODE)
                with open(file_path, "w") as f:
                    f.write(content)

# Function to create the project


def create_project():
    target_project_path = os.path.join(TARGET_FOLDER, PROJECT_NAME)

    if os.path.exists(target_project_path):
        print(f"Target project folder already exists: {target_project_path}")
        return

    # Copy and modify the template
    copy_and_modify_template(
        TEMPLATE_FOLDER, target_project_path, PROJECT_NAME)

    # Clone JUCE into the project folder
    clone_juce(target_project_path)

    print(
        f"Project {PROJECT_NAME} created successfully at {target_project_path}.")


if __name__ == "__main__":
    create_project()
