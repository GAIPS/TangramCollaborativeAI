# Launching an Agent Server

This guide will walk you through setting up a Python environment, installing dependencies, and launching an agent server in the **TangramCollaborativeAI** project.

---

## 🔹 Step 1: Create a Python Virtual Environment

To ensure a clean workspace, it's best to create a Python virtual environment.

1. **Open a terminal** and navigate to the agent's directory:
   ```bash
   cd models/[agent_directory]
   ```
   Replace `[agent_directory]` with the actual agent's folder name.

2. **Create a virtual environment** inside the agent's directory:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - **On macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```
   - **On Windows (CMD)**:
     ```cmd
     venv\Scripts\activate
     ```
   - **On Windows (PowerShell)**:
     ```powershell
     venv\Scripts\Activate.ps1
     ```

---

## 🔹 Step 2: Install Requirements

Each agent has its own dependencies listed in a `requirements.txt` file inside its directory. Once the virtual environment is activated, install them with:

```bash
pip install -r requirements.txt
```

To verify the installation, run:

```bash
pip list
```

---

## 🔹 Step 3: Environment Variables

###The current implemented agents simpleGPTAgent and relationalAgentGPT expect an "OPENAI_API_KEY" Environment Variable to exist in the system, and to contain contain a valid openAI key.

---


## 🔹 Step 4: Launch the Agent Server

To start the agent server, you **must run the command from the `TangramCollaborativeAI` directory** (one level above `models`).

1. **Navigate to the project root**:
   ```bash
   cd ../../  # Go to TangramCollaborativeAI
   ```

2. **Run the agent server** using the following command structure:
   ```bash
   python -m models.[agent_directory].[agent_main_file]
   ```

   Replace:
   - `[agent_directory]` with the agent's folder name.
   - `[agent_main_file]` with the main script name (without `.py`).

## Available Agents

There are currently 3 Agents available to use, our most complex agent that utilizes spacial descriptions [relationalAgent](relationalAgent/description.md), our self reflective agent [simpleGPTAgent](simpleAgent/description.md) and a random playing agent corresponding to the default [template behaviour](templates/agentTemplate.py)

### Example:
To launch the **RelationalAgent**, use:
```bash
python -m models.relationalAgent.relationalAgentGPT
```
To launch the **SimpleGPTAgent**, use:
```bash
python -m models.simpleAgent.simpleGPTAgent
```
To launch the class default random behaviour, use:
```bash
python -m models.templates.agentTemplate
```
---

Now your agent server should be up and running! 

