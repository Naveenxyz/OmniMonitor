# OmniMonitor

OmniMonitor is an intelligent productivity monitoring system that helps users stay focused on their priority tasks by combining automated screen monitoring with AI-powered activity analysis and engaging feedback mechanisms.

## Features

### 1. Task Management
- Create and manage tasks with priority levels
- Add detailed notes to tasks
- Mark tasks as complete
- Move tasks between current, priority, and completed states

### 2. Intelligent Screen Monitoring
- Takes periodic screenshots of your screen
- Uses GPT-4V to analyze screen content in real-time
- Determines if you're focused on your priority task
- Identifies productive vs unproductive activities

### 3. Smart Interruption System
- Shows popup alerts only when you're off-track
- Displays random motivational memes
- Requires typing challenges to dismiss popups, ensuring mindful acknowledgment
- Adapts feedback tone based on distraction frequency (sad → disappointed → angry)

### 4. Productivity Analytics
- Track daily productivity metrics
- View focused vs unfocused time distribution
- Monitor top activities and applications
- Analyze productivity trends over time

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your OpenAI API key in llm.py

3. Create a 'memes' directory and add some motivational meme images (supported formats: .png, .jpg, .jpeg, .gif, .bmp)

## Usage

1. Start the main interface:
```bash
python newstreamlit.py
```

2. Start the monitoring system:
```bash
python modifiedtk.py
```

### Task Management
- Use the "Tasks" tab to create and manage your tasks
- Set priority tasks that need focus
- Add notes and context to your tasks
- Track task completion

### Settings
- Configure monitoring frequency
- Pause/resume monitoring
- Adjust system settings

### Analytics
- View your productivity metrics
- Analyze focus patterns
- Track improvement over time

## How It Works

1. **Screen Monitoring**: The system takes periodic screenshots of your screen.

2. **AI Analysis**: Each screenshot is analyzed by GPT-4V to determine:
   - What's currently on screen
   - Whether it's related to your priority task
   - If the activity is productive
   - The prominent application being used

3. **Smart Notifications**: If you're off-track, the system shows a popup with:
   - A random motivational meme
   - Context about why you're off-track
   - A typing challenge to acknowledge and return to work

4. **Adaptive Feedback**: The system's tone changes based on distraction frequency:
   - First time: Gentle reminder
   - Second time: Disappointed tone
   - Third+ time: Stronger motivation

5. **Analytics**: All activities are logged to provide insights into:
   - Daily productivity patterns
   - Focus metrics
   - Most common distractions
   - Improvement trends

## Dependencies

- Python 3.x
- Streamlit
- Tkinter
- Pillow
- pyautogui
- sqlite3
- OpenAI API (GPT-4V)
- plotly
- pandas
