import base64
import requests
import sqlite3
from datetime import datetime, timedelta
import json

def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  task_id TEXT,
                  event_type TEXT,
                  metadata TEXT,
                  timestamp TEXT)''')
    conn.commit()
    return conn
conn = init_db()

def get_latest_history():
    conn = sqlite3.connect('tasks.db')  # Replace with your actual database name
    cursor = conn.cursor()
    
    # Assuming your table is named 'tasks' and has columns 'id', 'task', 'priority'
    cursor.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT 1")
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result  # Return the task description
    else:
        return "No priority task found"

def add_history_entry(conn, task_id, event_type, metadata):
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata_json = json.dumps(metadata)
    c.execute('INSERT INTO history (task_id, event_type, metadata, timestamp) VALUES (?, ?, ?, ?)',
              (task_id, event_type, metadata_json, timestamp))
    conn.commit()

def get_current_task_from_db():
    conn = sqlite3.connect('tasks.db')  # Replace with your actual database name
    cursor = conn.cursor()
    
    # Assuming your table is named 'tasks' and has columns 'id', 'task', 'priority'
    cursor.execute("SELECT * FROM tasks WHERE priority = 1 ORDER BY id LIMIT 1")
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result  # Return the task description
    else:
        return "No priority task found"
    
def get_pending_tasks_from_db():
    conn = sqlite3.connect('tasks.db')  # Replace with your actual database name
    cursor = conn.cursor()
    
    # Select all tasks from the database
    cursor.execute("SELECT * FROM tasks WHERE priority = 0 and done = 0")
    tasks = cursor.fetchall()
    
    conn.close()
    
    return tasks

def format_tasks(tasks):
    formatted_tasks = ""
    for task in tasks:
        # Use the second (index 1) and third (index 2) items from each task tuple
        formatted_tasks += f"- {task[1]}: {task[2]}\n"
    return formatted_tasks.strip()

def check_user_focus(api_key, current_task, other_planned_tasks, history, image_path):
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # Encode the image
    image_base64 = encode_image(image_path)

    # Define the om_prompt
    om_prompt = f"""
You're a progress monitor that helps with the user staying on track with their tasks. You look at the current focus task that the user has chosen to work on, current screenshot of their laptop and the task timeline so-far.

Current Task in focus: {current_task}

Other planned tasks:

{other_planned_tasks}

History of the user so far:
{history}

Instructions:
Given the history, current user screen determine if the user is doing the work on relevant tasks or not. If they're not working on the focus task, trigger a pop up.

Show new text and typing text for the pop-up each time. Try to keep these texts within 10 words each.

Output format options: JSON

option 1: Trigger pop up for not focusing on the main priority task and/or doing unproductive stuff. (when focused_productive==0) Note: Even if productive == 1 and focused_productive == 0, trigger pop-up because they're switching contexts and not focusing on the focus task. Other plsnned 
{{
    "metadata": {{
        "whats_on_the_screen": "<explain what the user is doing by looking at the current screen and linking it to the task that they're supposed to be doing. Ex: If its a youtube video, mention the video title and all. Also do internal thought on what the values for focused_productive and productive should be with reasons>",
        "focused_productive": <int 1 if they are working on the focus task, 0 otherwise. Even if they're working on other planned tasks, as the focus is teh focus task, you should give this as 0.>,
        "productive": <int 1 if they are either working on the task in focus or one of the planned tasks or something related to work e-mail and all>,
        "mood": "<bot mood can be one of `sad` for first time losing focus, `disappointed` for repeating the mistake twice, `angry` for three or more times.>",
        "text": "<the text to show in the pop up to communicate what the user is doing and tell them to get back to the focus task. Ex: I don't think watching this youtube documentary on african gorillas will help you with writing the user onboarding UI. GET BACK TO WORK. Note: don't use just the same i don't think... GET BACK to ... structure. Get creative and come up with some funny, sassy responses for this and the typinng text below>",
        "typing_text": "<the user is given a typing challenge where they have to type the text verbatim to remove the pop-up. This text should be the next steps that the user should do to get back to their tasks. Ex: I will immediately close the youtube documentary tab and get back to the code editor for the UI task. Note: Get creative, be funny and sassy. don't give same stuff again and again.>",
        "prominent_application": "<The most prominent application that is visible, in small case and underscore. Ex: visual_studio_code or youtube>"
    }},
    "event_type": "pop-up"
}}

option 2: working on the target focus task. So, note and wait. Note: we don't have any mood, text, typing text as we don't need any pop up.
{{
    "metadata": {{
        "whats_on_the_screen": "<explain what the user is doing by looking at the current screen and linking it to the task that they're supposed to be doing. Ex: If its a youtube video, mention the video title and all. Also do internal thought on what the values for focused_productive and productive should be with reasons>",
        "focused_productive": <int 1 as they're working on the focused productive task>,
        "productive": <int 1 as they're working on the focused productive task>,
        "prominent_application": "<The most prominent applicationthat is visible, in small case and underscore. Ex: visual_studio_code or youtube>"
    }},
    "event_type": "note-and-wait"
}}
"""

    # Define headers
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    # Define payload
    payload = {
        "model": "gpt-4o",
        "temperature": 1,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": om_prompt},
                    {"type": "text", "text": "current screenshot:"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}",
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
        "max_tokens": 4096,
    }

    # Send the request
    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
    )

    # Return the response
    return response.json()["choices"][0]["message"]["content"]


# Example usage
api_key = "sk-proj-QslpKkzuoo3CHgVpmshGT3BlbkFJ3hzaZUkZKfaXVHnSAhbw"
current_task = "Integrate GenAI for Real-Time Query Analysis"
other_planned_tasks = """
- Develop User Interface for AI Agent Deployment
- Implement Secure User Authentication System
- Set Up Automated Testing for AI Agent Responses
- Create Documentation for API Integrations"""
history = """
Aggregate data of last 24 hrs:

[% of unproductive, productive, and relevant productive during the focus time]
Unproductive: 20%
Productive: 30%
Relevant Productive: 50%

last few events while the user is on this task old to recent:

1. <2024-07-05T10:00:00Z, "Integrate GenAI for Real-Time Query Analysis", {
"metadata": {
"whats_on_the_screen": "The user is reading a research paper on state-of-the-art GenAI models.",
"focused_productive": 1,
"productive": 1
},
"event_type": "note-and-wait"
}>
2. <2024-07-05T11:00:00Z, "Integrate GenAI for Real-Time Query Analysis", {
"metadata": {
"whats_on_the_screen": "The user is setting up a virtual environment in their IDE to start the GenAI integration.",
"focused_productive": 1,
"productive": 1
},
"event_type": "note-and-wait"
}>
3. <2024-07-05T13:30:00Z, "Integrate GenAI for Real-Time Query Analysis", {
"metadata": {
"whats_on_the_screen": "The user is browsing social media, unrelated to the task.",
"focused_productive": 0,
"productive": 0,
"mood": "disappointed",
"text": "You are browsing social media which is not relevant to your current task of integrating GenAI. Please return to the GenAI documentation and continue the integration.",
"typing_text": "I will stop browsing social media and return to the GenAI documentation to continue the integration."
},
"event_type": "pop-up"
}>
4. <2024-07-05T14:30:00Z, "Integrate GenAI for Real-Time Query Analysis", {
"metadata": {
"whats_on_the_screen": "The user is debugging code related to the GenAI integration.",
"focused_productive": 1,
"productive": 1
},
"event_type": "note-and-wait"
}>
5. <2024-07-05T16:00:00Z, "Integrate GenAI for Real-Time Query Analysis", {
"metadata": {
"whats_on_the_screen": "The user is watching a non-related YouTube video.",
"focused_productive": 0,
"productive": 0,
"mood": "angry",
"text": "Watching YouTube videos unrelated to your current task will delay your progress on integrating GenAI. Focus back on your task.",
"typing_text": "I will immediately close the YouTube video and return to my code editor to focus on the GenAI integration."
},
"event_type": "pop-up"
}>
6. <2024-07-05T17:30:00Z, "Integrate GenAI for Real-Time Query Analysis", {
"metadata": {
"whats_on_the_screen": "The user is integrating API calls for GenAI model training.",
"focused_productive": 1,
"productive": 1
},
"event_type": "note-and-wait"
}>
"""
image_path = "images/screenshot_20240707_000007.png"

# Call the function
# result = check_user_focus(
#     api_key, current_task, other_planned_tasks, history, image_path
# )
# print(result)

def get_llm_out(image_path):
    task = get_current_task_from_db()
    pending_tasks = format_tasks(get_pending_tasks_from_db())
    result = json.loads(check_user_focus(
    api_key, "{} : {}".format(task[1],task[2]), pending_tasks, "Empty. No History", image_path
    ))
    print(task[1],task[2],pending_tasks)
    add_history_entry(conn, task[0], result['event_type'], result['metadata'])
    print(result)
    return result

def check_if_show_popup():
    current_time = datetime.now()
    data = get_latest_history()
    timestamp = datetime.strptime(data[-1], '%Y-%m-%d %H:%M:%S')

    # Calculate the time difference
    time_difference = current_time - timestamp

    data2 = json.loads(data[3])
    # Check if the difference is less than 5 minutes
    if time_difference < timedelta(minutes=5):
        pass
    else:
        return False
    if data2.get('mood'):
        return True
    else:
        return False

if __name__ == "__main__":
    # get_llm_out("images/screenshot_20240707_000749.png")
    print(check_if_show_popup())