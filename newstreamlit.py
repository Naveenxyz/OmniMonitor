import streamlit as st
import sqlite3
import uuid
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import numpy as np
# Database setup
def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id TEXT PRIMARY KEY, task TEXT, note TEXT, done BOOLEAN, priority BOOLEAN)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    return conn

def fetch_history_data(date):
    conn = sqlite3.connect('tasks.db')
    query = f"""
    SELECT * FROM history 
    WHERE date(timestamp) = '{date}'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def parse_metadata(metadata_str):
    metadata = json.loads(metadata_str)
    return pd.Series({
        'focused_productive': metadata.get('focused_productive', 0),
        'productive': metadata.get('productive', 0),
        'whats_on_screen': metadata.get('whats_on_the_screen', '')
    })
    
def fetch_tasks():
    c = conn.cursor()
    c.execute('SELECT * FROM tasks')
    tasks = [{'id': row[0], 'task': row[1], 'note': row[2], 'done': bool(row[3]), 'priority': bool(row[4])}
             for row in c.fetchall()]
    return tasks

def add_task_to_db(task, note):
    task_id = str(uuid.uuid4())
    c = conn.cursor()
    c.execute('INSERT INTO tasks VALUES (?, ?, ?, ?, ?)', (task_id, task, note, False, False))
    conn.commit()

def update_task_in_db(task_id, task, note, done, priority):
    c = conn.cursor()
    c.execute('UPDATE tasks SET task = ?, note = ?, done = ?, priority = ? WHERE id = ?',
              (task, note, done, priority, task_id))
    conn.commit()

def get_setting(key, default_value):
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = c.fetchone()
    if result:
        return result[0]
    else:
        set_setting(key, str(default_value))
        return str(default_value)

def set_setting(key, value):
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()

# Initialize database connection
conn = init_db()

# Load tasks from database
if 'tasks' not in st.session_state:
    st.session_state.tasks = fetch_tasks()

# Load settings from database
if 'settings' not in st.session_state:
    st.session_state.settings = {
        'paused': get_setting('paused', 'false'),
        'frequency': get_setting('frequency', '1')
    }

def update_task_state(task_id, new_state):
    task = next(task for task in st.session_state.tasks if task['id'] == task_id)
    if new_state == "current":
        task['done'] = False
        task['priority'] = False
    elif new_state == "priority":
        task['done'] = False
        task['priority'] = True
    elif new_state == "done":
        task['done'] = True
        task['priority'] = False
    update_task_in_db(task['id'], task['task'], task['note'], task['done'], task['priority'])
    st.rerun()

def edit_task(task_id):
    task = next(task for task in st.session_state.tasks if task['id'] == task_id)
    task['editing'] = True
    st.rerun()

def save_task(task_id):
    task = next(task for task in st.session_state.tasks if task['id'] == task_id)
    task['task'] = st.session_state[f'edit_title_{task_id}']
    task['note'] = st.session_state[f'edit_note_{task_id}']
    task['editing'] = False
    update_task_in_db(task['id'], task['task'], task['note'], task['done'], task['priority'])
    st.rerun()

def display_tasks(task_type):
    for task in st.session_state.tasks:
        if ((task_type == "current" and not task['done'] and not task['priority']) or
            (task_type == "priority" and task['priority']) or
            (task_type == "done" and task['done'])):
            
            task_name = task['task']
            task_key = f'{task_type}_{task["id"]}'
            
            with st.expander(f"{'🔴' if task['priority'] else '✅' if task['done'] else '⚪'} {task_name}", expanded=False):
                if task.get('editing', False):
                    st.text_input("Edit task title:", key=f'edit_title_{task["id"]}', value=task['task'])
                    st.text_area("Edit task note:", key=f'edit_note_{task["id"]}', value=task['note'], height=100)
                    if st.button('Save', key=f'save_{task_key}'):
                        save_task(task['id'])
                else:
                    st.write(f"**Note:** {task['note']}")
                    col1, col2, col3 = st.columns(3)
                    
                    if task_type == "current":
                        if col1.button('Mark Priority', key=f'mark_priority_{task_key}'):
                            update_task_state(task['id'], "priority")
                        if col2.button('Mark as Done', key=f'mark_done_{task_key}'):
                            update_task_state(task['id'], "done")
                    elif task_type == "priority":
                        if col1.button('Move to Current', key=f'move_current_{task_key}'):
                            update_task_state(task['id'], "current")
                        if col2.button('Mark as Done', key=f'mark_done_{task_key}'):
                            update_task_state(task['id'], "done")
                    elif task_type == "done":
                        if col1.button('Move to Current', key=f'move_current_{task_key}'):
                            update_task_state(task['id'], "current")
                        if col2.button('Mark Priority', key=f'mark_priority_{task_key}'):
                            update_task_state(task['id'], "priority")
                    
                    if col3.button('Edit', key=f'edit_{task_key}'):
                        edit_task(task['id'])

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Tasks", "Settings", "Analytics"])

if page == "Tasks":
    st.title("Task Manager")

    # Add Task section at the top
    st.header("Add New Task")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_task = st.text_input("Enter new task:")
        new_note = st.text_area("Enter task note:", height=100)
    with col2:
        st.write("")  # This empty space aligns the button with the input fields
        st.write("")
        if st.button("Add Task", use_container_width=True):
            if new_task.strip():
                add_task_to_db(new_task.strip(), new_note.strip())
                st.session_state.tasks = fetch_tasks()  # Refresh tasks from DB
                st.success(f'Task "{new_task}" added!')
                st.rerun()
            else:
                st.error("Please enter a task before adding.")
    
    st.header('Priority Task:')
    display_tasks("priority")

    st.header('Current Tasks:')
    display_tasks("current")

    st.header('Completed Tasks:')
    display_tasks("done")

elif page == "Settings":
    st.title("Settings")

    # Resume/Pause toggle
    paused = st.toggle("Pause Tasks", value=st.session_state.settings['paused'].lower() == 'true')
    if paused != (st.session_state.settings['paused'].lower() == 'true'):
        st.session_state.settings['paused'] = str(paused).lower()
        set_setting('paused', st.session_state.settings['paused'])
        st.success("Task status updated!")

    # Frequency input
    frequency = st.number_input("Task Frequency (seconds)", 
                                min_value=1, 
                                value=int(st.session_state.settings['frequency']), 
                                step=1)
    if frequency != int(st.session_state.settings['frequency']):
        st.session_state.settings['frequency'] = str(frequency)
        set_setting('frequency', st.session_state.settings['frequency'])
        st.success("Frequency updated!")

    # Display current settings
    st.subheader("Current Settings")
    st.write(f"Tasks are currently: {'Paused' if st.session_state.settings['paused'].lower() == 'true' else 'Active'}")
    st.write(f"Task frequency: Every {st.session_state.settings['frequency']} second(s)")


elif page == "Analytics":
    st.title("Productivity Analytics")

    # Date selector
    max_date = datetime.now().date()
    min_date = max_date - timedelta(days=30)  # Allow selection up to 30 days in the past
    selected_date = st.date_input("Select Date", max_date, min_value=min_date, max_value=max_date)

    # Fetch and process data
    df = fetch_history_data(selected_date)
    
    if df.empty:
        st.write("No data available for the selected date.")
    else:
        # Parse metadata
        metadata_df = df['metadata'].apply(parse_metadata)
        df = pd.concat([df, metadata_df], axis=1)

        # Calculate productivity metrics
        total_entries = len(df)
        productive_entries = df['productive'].sum()
        focused_productive_entries = df['focused_productive'].sum()
        productivity_percentage = (productive_entries / total_entries) * 100
        focus_percentage = (focused_productive_entries / total_entries) * 100
        unproductive_entries = total_entries - productive_entries
        unproductive_percentage = (unproductive_entries / total_entries) * 100

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Entries", total_entries)
        col2.metric("Productivity", f"{productivity_percentage:.2f}%")
        col3.metric("Focus", f"{focus_percentage:.2f}%")
        col4.metric("UnProductive", f"{unproductive_percentage:.2f}%")

        # Productivity over time
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])  # Remove rows with invalid timestamps
        
        if not df.empty:
            df = df.set_index('timestamp')
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df_resampled = df[numeric_columns].resample('h').sum().reset_index()
            
            fig = px.line(df_resampled, x='timestamp', y=['productive', 'focused_productive'], 
                          title='Productivity Over Time')
            st.plotly_chart(fig)
        else:
            st.write("Not enough data to plot productivity over time.")

        # Top activities
        if 'whats_on_screen' in df.columns:
            top_activities = df['whats_on_screen'].value_counts().head(5)
            st.subheader("Top Activities")
            st.bar_chart(top_activities)
        else:
            st.write("No activity data available.")

        # Raw data
        if st.checkbox("Show raw data"):
            st.subheader("Raw Data")
            st.write(df)

# Debug: Display current state
if st.checkbox("Show current state"):
    st.write(st.session_state.tasks)
    st.write(st.session_state.settings)