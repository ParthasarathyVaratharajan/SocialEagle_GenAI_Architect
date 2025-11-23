import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Page configuration
st.set_page_config(
    page_title="Gym Workout Logger",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-title {
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-align: center;
    }
    .main-subtitle {
        color: #e0e7ff;
        font-size: 1.1rem;
        text-align: center;
        margin-top: 0.5rem;
    }
    .workout-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .exercise-badge {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.2rem;
    }
    .divider {
        height: 2px;
        background: linear-gradient(to right, transparent, #667eea, transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'workouts' not in st.session_state:
    st.session_state.workouts = []

# Exercise library
EXERCISE_LIBRARY = {
    'Chest': ['Bench Press', 'Incline Bench Press', 'Dumbbell Press', 'Push-ups', 'Cable Flyes', 'Chest Press Machine'],
    'Back': ['Deadlift', 'Pull-ups', 'Barbell Row', 'Lat Pulldown', 'Seated Cable Row', 'T-Bar Row'],
    'Legs': ['Squat', 'Leg Press', 'Romanian Deadlift', 'Leg Curl', 'Leg Extension', 'Calf Raises', 'Lunges'],
    'Shoulders': ['Overhead Press', 'Dumbbell Shoulder Press', 'Lateral Raises', 'Front Raises', 'Face Pulls', 'Shrugs'],
    'Arms': ['Barbell Curl', 'Tricep Dips', 'Hammer Curl', 'Tricep Pushdown', 'Preacher Curl', 'Skull Crushers'],
    'Core': ['Plank', 'Crunches', 'Russian Twists', 'Leg Raises', 'Ab Wheel', 'Cable Crunches']
}

def save_workout(date, exercise, muscle_group, sets, reps, weight, notes=""):
    """Save workout entry"""
    workout = {
        'date': date.strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M:%S'),
        'exercise': exercise,
        'muscle_group': muscle_group,
        'sets': sets,
        'reps': reps,
        'weight': weight,
        'total_volume': sets * reps * weight,
        'notes': notes
    }
    st.session_state.workouts.append(workout)
    return True

def get_workouts_df():
    """Convert workouts to DataFrame"""
    if st.session_state.workouts:
        return pd.DataFrame(st.session_state.workouts)
    return pd.DataFrame()

def calculate_stats():
    """Calculate workout statistics"""
    df = get_workouts_df()
    if df.empty:
        return None
    
    stats = {
        'total_workouts': len(df),
        'total_volume': df['total_volume'].sum(),
        'unique_exercises': df['exercise'].nunique(),
        'this_week': len(df[pd.to_datetime(df['date']) >= datetime.now() - timedelta(days=7)]),
        'avg_sets': df['sets'].mean(),
        'max_weight': df['weight'].max()
    }
    return stats

def get_weekly_progress():
    """Get weekly workout progress"""
    df = get_workouts_df()
    if df.empty:
        return None
    
    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.to_period('W')
    
    weekly = df.groupby('week').agg({
        'total_volume': 'sum',
        'exercise': 'count'
    }).reset_index()
    
    weekly['week'] = weekly['week'].astype(str)
    return weekly

# Header
st.markdown("""
<div class='main-header'>
    <h1 class='main-title'>🏋️‍♂️ Gym Workout Logger</h1>
    <p class='main-subtitle'>Track Your Progress | Build Your Strength</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 💪 Quick Stats")
    
    stats = calculate_stats()
    if stats:
        st.metric("Total Workouts", stats['total_workouts'])
        st.metric("This Week", stats['this_week'])
        st.metric("Total Volume (kg)", f"{stats['total_volume']:,.0f}")
        st.metric("Unique Exercises", stats['unique_exercises'])
    else:
        st.info("Start logging workouts to see stats!")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    st.markdown("### 🎯 Muscle Groups")
    for muscle in EXERCISE_LIBRARY.keys():
        st.text(f"💪 {muscle}")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Data Management")
    
    if st.button("📥 Export Data", use_container_width=True):
        df = get_workouts_df()
        if not df.empty:
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"workout_log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No data to export")
    
    if st.button("🗑️ Clear All Data", type="secondary", use_container_width=True):
        if st.session_state.workouts:
            st.session_state.workouts = []
            st.rerun()
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.caption("Workout Logger v1.0")
    st.caption("Stay consistent! 💪")

# Main Content - Tabs
tab1, tab2, tab3, tab4 = st.tabs(["➕ Log Workout", "📊 Progress", "📋 History", "🏆 Achievements"])

with tab1:
    st.markdown("### ➕ Log New Workout")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Workout entry form
        with st.form("workout_form", clear_on_submit=True):
            # Date
            workout_date = st.date_input(
                "Workout Date",
                value=datetime.now(),
                max_value=datetime.now()
            )
            
            # Muscle group selection
            muscle_group = st.selectbox(
                "Muscle Group",
                options=list(EXERCISE_LIBRARY.keys())
            )
            
            # Exercise selection
            exercise = st.selectbox(
                "Exercise",
                options=EXERCISE_LIBRARY[muscle_group]
            )
            
            # Custom exercise option
            custom_exercise = st.text_input("Or enter custom exercise (optional)")
            if custom_exercise:
                exercise = custom_exercise
            
            # Sets, Reps, Weight
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                sets = st.number_input("Sets", min_value=1, max_value=20, value=3)
            
            with col_b:
                reps = st.number_input("Reps", min_value=1, max_value=100, value=10)
            
            with col_c:
                weight = st.number_input("Weight (kg)", min_value=0.0, max_value=500.0, value=20.0, step=2.5)
            
            # Notes
            notes = st.text_area("Notes (optional)", placeholder="How did it feel? Any observations?")
            
            # Calculate total volume
            total_volume = sets * reps * weight
            st.info(f"💪 Total Volume: {total_volume:,.0f} kg")
            
            # Submit button
            submitted = st.form_submit_button("✅ Log Workout", type="primary", use_container_width=True)
            
            if submitted:
                success = save_workout(workout_date, exercise, muscle_group, sets, reps, weight, notes)
                if success:
                    st.success(f"✅ Logged: {exercise} - {sets}x{reps} @ {weight}kg")
                    st.balloons()
                    st.rerun()
    
    with col2:
        st.markdown("### 📝 Quick Tips")
        st.markdown("""
        <div class='workout-card'>
            <h4>💡 Logging Tips</h4>
            <ul>
                <li>Log immediately after each exercise</li>
                <li>Be consistent with your measurements</li>
                <li>Add notes about form or difficulty</li>
                <li>Track progressive overload weekly</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Today's Summary")
        df = get_workouts_df()
        if not df.empty:
            today = datetime.now().strftime('%Y-%m-%d')
            today_workouts = df[df['date'] == today]
            
            if not today_workouts.empty:
                st.metric("Exercises Today", len(today_workouts))
                st.metric("Total Volume Today", f"{today_workouts['total_volume'].sum():,.0f} kg")
                
                st.markdown("**Exercises:**")
                for exercise in today_workouts['exercise'].unique():
                    st.markdown(f"<span class='exercise-badge'>{exercise}</span>", unsafe_allow_html=True)
            else:
                st.info("No workouts logged today yet!")
        else:
            st.info("Start logging to see today's summary!")

with tab2:
    st.markdown("### 📊 Progress & Analytics")
    
    df = get_workouts_df()
    
    if not df.empty:
        # Stats overview
        col1, col2, col3, col4 = st.columns(4)
        
        stats = calculate_stats()
        
        with col1:
            st.markdown(f"""
            <div class='stat-box'>
                <div class='stat-label'>Total Workouts</div>
                <div class='stat-number'>{stats['total_workouts']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='stat-box'>
                <div class='stat-label'>Total Volume (kg)</div>
                <div class='stat-number'>{stats['total_volume']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class='stat-box'>
                <div class='stat-label'>Avg Sets/Workout</div>
                <div class='stat-number'>{stats['avg_sets']:.1f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class='stat-box'>
                <div class='stat-label'>Max Weight (kg)</div>
                <div class='stat-number'>{stats['max_weight']:.1f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Weekly volume chart
        st.markdown("### 📈 Weekly Total Volume")
        weekly = get_weekly_progress()
        
        if weekly is not None and not weekly.empty:
            fig_volume = px.bar(
                weekly,
                x='week',
                y='total_volume',
                title='Weekly Total Volume (kg)',
                labels={'week': 'Week', 'total_volume': 'Total Volume (kg)'},
                color='total_volume',
                color_continuous_scale='Purples'
            )
            fig_volume.update_layout(
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_volume, use_container_width=True)
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Exercise frequency
        st.markdown("### 🎯 Exercise Frequency")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            exercise_counts = df['exercise'].value_counts().head(10)
            fig_exercises = px.bar(
                x=exercise_counts.values,
                y=exercise_counts.index,
                orientation='h',
                title='Top 10 Exercises',
                labels={'x': 'Count', 'y': 'Exercise'},
                color=exercise_counts.values,
                color_continuous_scale='Purples'
            )
            fig_exercises.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_exercises, use_container_width=True)
        
        with col_b:
            muscle_counts = df['muscle_group'].value_counts()
            fig_muscles = px.pie(
                values=muscle_counts.values,
                names=muscle_counts.index,
                title='Muscle Group Distribution',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Purples
            )
            fig_muscles.update_layout(height=400)
            st.plotly_chart(fig_muscles, use_container_width=True)
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Progress over time for selected exercise
        st.markdown("### 📉 Exercise Progress Tracker")
        
        selected_exercise = st.selectbox(
            "Select Exercise to Track",
            options=df['exercise'].unique()
        )
        
        exercise_df = df[df['exercise'] == selected_exercise].copy()
        exercise_df['date'] = pd.to_datetime(exercise_df['date'])
        exercise_df = exercise_df.sort_values('date')
        
        fig_progress = go.Figure()
        
        fig_progress.add_trace(go.Scatter(
            x=exercise_df['date'],
            y=exercise_df['weight'],
            mode='lines+markers',
            name='Weight',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8)
        ))
        
        fig_progress.update_layout(
            title=f'{selected_exercise} - Weight Progress',
            xaxis_title='Date',
            yaxis_title='Weight (kg)',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_progress, use_container_width=True)
        
    else:
        st.info("📊 Start logging workouts to see your progress and analytics!")

with tab3:
    st.markdown("### 📋 Workout History")
    
    df = get_workouts_df()
    
    if not df.empty:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_filter = st.date_input(
                "Filter by Date",
                value=None,
                help="Leave empty to show all"
            )
        
        with col2:
            muscle_filter = st.multiselect(
                "Filter by Muscle Group",
                options=df['muscle_group'].unique(),
                default=None
            )
        
        with col3:
            exercise_filter = st.multiselect(
                "Filter by Exercise",
                options=df['exercise'].unique(),
                default=None
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if date_filter:
            filtered_df = filtered_df[filtered_df['date'] == date_filter.strftime('%Y-%m-%d')]
        
        if muscle_filter:
            filtered_df = filtered_df[filtered_df['muscle_group'].isin(muscle_filter)]
        
        if exercise_filter:
            filtered_df = filtered_df[filtered_df['exercise'].isin(exercise_filter)]
        
        # Display table
        st.markdown(f"**Showing {len(filtered_df)} workouts**")
        
        # Format display
        display_df = filtered_df[['date', 'exercise', 'muscle_group', 'sets', 'reps', 'weight', 'total_volume', 'notes']].copy()
        display_df = display_df.sort_values('date', ascending=False)
        display_df['total_volume'] = display_df['total_volume'].apply(lambda x: f"{x:,.0f} kg")
        display_df['weight'] = display_df['weight'].apply(lambda x: f"{x:.1f} kg")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": "Date",
                "exercise": "Exercise",
                "muscle_group": "Muscle Group",
                "sets": "Sets",
                "reps": "Reps",
                "weight": "Weight",
                "total_volume": "Total Volume",
                "notes": "Notes"
            }
        )
        
        # Delete option
        if st.checkbox("Show delete options"):
            row_to_delete = st.number_input(
                "Enter row number to delete (from original data)",
                min_value=0,
                max_value=len(st.session_state.workouts)-1,
                value=0
            )
            if st.button("🗑️ Delete Selected Row", type="secondary"):
                st.session_state.workouts.pop(row_to_delete)
                st.success("Row deleted!")
                st.rerun()
    
    else:
        st.info("📋 No workout history yet. Start logging!")

with tab4:
    st.markdown("### 🏆 Achievements & Milestones")
    
    df = get_workouts_df()
    
    if not df.empty:
        # Personal records
        st.markdown("### 💪 Personal Records")
        
        col1, col2, col3 = st.columns(3)
        
        stats = calculate_stats()
        
        achievements = []
        
        # Check milestones
        if stats['total_workouts'] >= 10:
            achievements.append(("🎯", "10 Workouts", "Consistency King!"))
        if stats['total_workouts'] >= 50:
            achievements.append(("🔥", "50 Workouts", "On Fire!"))
        if stats['total_workouts'] >= 100:
            achievements.append(("⭐", "100 Workouts", "Century Club!"))
        if stats['total_volume'] >= 10000:
            achievements.append(("💎", "10,000 kg Volume", "Volume Beast!"))
        if stats['unique_exercises'] >= 20:
            achievements.append(("🎨", "20 Different Exercises", "Exercise Variety!"))
        
        # Display achievements
        st.markdown("### 🎖️ Unlocked Achievements")
        
        if achievements:
            for emoji, title, desc in achievements:
                st.markdown(f"""
                <div class='workout-card'>
                    <h3>{emoji} {title}</h3>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Keep working out to unlock achievements!")
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Exercise PRs
        st.markdown("### 🏅 Exercise Personal Records")
        
        pr_data = df.groupby('exercise')['weight'].max().sort_values(ascending=False).head(10)
        
        for exercise, max_weight in pr_data.items():
            st.markdown(f"""
            <div class='workout-card'>
                <strong>{exercise}</strong>: {max_weight:.1f} kg
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.info("🏆 Start logging to unlock achievements!")

# Footer
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 1rem;'>
    <p><strong>💪 Keep pushing your limits!</strong></p>
    <p style='font-size: 0.9rem;'>Consistency is key to success</p>
</div>
""", unsafe_allow_html=True)