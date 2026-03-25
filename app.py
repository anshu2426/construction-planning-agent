"""
Streamlit UI for Construction Planning Assistant Agent
Main application interface for the AI-powered construction planning system
"""
import streamlit as st
import json
import os
from datetime import datetime
from simple_crew import SimpleConstructionPlanner
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# Configure Streamlit page
st.set_page_config(
    page_title="Construction Planning Assistant",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def check_api_key():
    """Check if Groq API key is configured"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("⚠️ GROQ_API_KEY environment variable not set!")
        st.info("Please set the GROQ_API_KEY environment variable and restart the application.")
        st.code("export GROQ_API_KEY='your-api-key-here'")
        return False
    return True


def display_project_metadata(metadata):
    """Display project metadata in a formatted way"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tasks", metadata.get("total_tasks", 0))
    
    with col2:
        duration = metadata.get("total_duration_days", 0)
        st.metric("Duration (Days)", duration)
    
    with col3:
        cost = metadata.get("total_estimated_cost", "$0")
        st.metric("Estimated Cost", cost)
    
    with col4:
        created_date = metadata.get("created_date", "").split()[0]
        st.metric("Created", created_date)


def display_task_breakdown(task_breakdown):
    """Display task breakdown with visualizations"""
    tasks = task_breakdown.get("tasks", [])
    
    if not tasks:
        st.warning("No tasks available")
        return
    
    st.subheader("📋 Task Overview")
    
    # Create DataFrame for visualization
    df = pd.DataFrame(tasks)
    
    # Task categories distribution
    if 'category' in df.columns:
        fig = px.pie(
            df, 
            names='category', 
            title='Task Distribution by Category',
            color_discrete_map={
                'permits': '#FF6B6B',
                'site_preparation': '#4ECDC4',
                'foundation': '#45B7D1',
                'structural': '#96CEB4',
                'utilities': '#FFEAA7',
                'finishing': '#DDA0DD'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Task duration timeline
    if 'estimated_duration_days' in df.columns and 'name' in df.columns:
        df_sorted = df.sort_values('estimated_duration_days')
        fig = px.bar(
            df_sorted,
            x='estimated_duration_days',
            y='name',
            orientation='h',
            title='Task Duration Timeline',
            color='estimated_duration_days',
            color_continuous_scale='Blues'
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed task list
    st.subheader("📝 Detailed Task List")
    
    for i, task in enumerate(tasks, 1):
        with st.expander(f"Task {i}: {task.get('name', 'Unnamed Task')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {task.get('id', 'N/A')}")
                st.write(f"**Category:** {task.get('category', 'N/A')}")
                st.write(f"**Duration:** {task.get('estimated_duration_days', 0)} days")
            
            with col2:
                dependencies = task.get('dependencies', [])
                if dependencies:
                    st.write(f"**Dependencies:** {', '.join(dependencies)}")
                else:
                    st.write("**Dependencies:** None")
            
            st.write(f"**Description:** {task.get('description', 'No description available')}")


def display_resource_validation(validation_results):
    """Display resource validation results"""
    validated_tasks = validation_results.get("validated_tasks", [])
    approved_tasks = validation_results.get("approved_tasks", 0)
    blocked_tasks = validation_results.get("blocked_tasks", 0)
    
    st.subheader("✅ Resource Validation Results")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Tasks", len(validated_tasks))
    
    with col2:
        st.metric("Approved", approved_tasks, delta=None, delta_color="normal")
    
    with col3:
        st.metric("Blocked", blocked_tasks, delta=None, delta_color="inverse")
    
    # Validation status distribution
    if validated_tasks:
        status_counts = {}
        for task in validated_tasks:
            status = task.get('validation_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        fig = px.pie(
            values=list(status_counts.values()),
            names=list(status_counts.keys()),
            title='Validation Status Distribution'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed validation results
    st.subheader("🔍 Detailed Validation")
    
    for task in validated_tasks:
        status = task.get('validation_status', 'unknown')
        task_name = task.get('task_name', 'Unnamed Task')
        
        # Color code based on status
        if status == 'approved':
            icon = "✅"
            color = "success"
        elif status == 'needs_review':
            icon = "⚠️"
            color = "warning"
        else:
            icon = "❌"
            color = "error"
        
        with st.expander(f"{icon} {task_name} - {status.upper()}"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Labor availability
                labor = task.get('labor', {})
                labor_available = labor.get('available', False)
                labor_icon = "✅" if labor_available else "❌"
                st.write(f"**Labor:** {labor_icon} {'Available' if labor_available else 'Not Available'}")
                if labor.get('details'):
                    st.write(f"Details: {labor['details']}")
            
            with col2:
                # Material availability
                materials = task.get('materials', {})
                material_available = materials.get('available', False)
                material_icon = "✅" if material_available else "❌"
                st.write(f"**Materials:** {material_icon} {'Available' if material_available else 'Not Available'}")
                if materials.get('details'):
                    st.write(f"Details: {materials['details']}")
            
            # Equipment availability
            equipment = task.get('equipment', {})
            equipment_available = equipment.get('available', False)
            equipment_icon = "✅" if equipment_available else "❌"
            st.write(f"**Equipment:** {equipment_icon} {'Available' if equipment_available else 'Not Available'}")
            if equipment.get('details'):
                st.write(f"Details: {equipment['details']}")
            
            # Cost and notes
            st.write(f"**Estimated Cost:** {task.get('total_estimated_cost', 'N/A')}")
            st.write(f"**Notes:** {task.get('validation_notes', 'No notes available')}")


def display_project_schedule(schedule_results):
    """Display project schedule with timeline visualization"""
    schedule = schedule_results.get("schedule", [])
    total_duration = schedule_results.get("total_project_duration", 0)
    critical_path_tasks = schedule_results.get("critical_path_tasks", [])
    
    st.subheader("📅 Project Schedule")
    
    # Schedule overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Duration", f"{total_duration} days")
    
    with col2:
        st.metric("Critical Path Tasks", len(critical_path_tasks))
    
    with col3:
        buffer_days = schedule_results.get("buffer_days", 0)
        if buffer_days > 0:
            st.metric("Buffer Days", buffer_days)
        else:
            st.metric("Buffer Days", "None")
    
    # Gantt chart visualization
    if schedule:
        st.subheader("📊 Project Timeline (Gantt Chart)")
        
        # Prepare data for Gantt chart
        gantt_data = []
        for task in schedule:
            gantt_data.append({
                'Task': task.get('task_name', 'Unnamed'),
                'Start': task.get('start_day', 0),
                'Finish': task.get('end_day', 0),
                'Category': task.get('task_id', 'general'),
                'Critical Path': 'Critical' if task.get('critical_path', False) else 'Regular'
            })
        
        df_gantt = pd.DataFrame(gantt_data)
        
        # Create Gantt chart
        fig = px.timeline(
            df_gantt,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Critical Path",
            title="Construction Project Timeline",
            color_discrete_map={'Critical': '#FF6B6B', 'Regular': '#4ECDC4'}
        )
        
        fig.update_yaxes(categoryorder='total ascending')
        fig.update_layout(
            xaxis_title="Project Day",
            yaxis_title="Tasks",
            height=max(400, len(schedule) * 30)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Project phases
    phases = schedule_results.get("project_phases", [])
    if phases:
        st.subheader("🏗️ Project Phases")
        
        for phase in phases:
            with st.expander(f"📋 {phase.get('phase', 'Unnamed Phase')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Start Day:** {phase.get('start_day', 'N/A')}")
                    st.write(f"**End Day:** {phase.get('end_day', 'N/A')}")
                    st.write(f"**Duration:** {phase.get('end_day', 0) - phase.get('start_day', 0) + 1} days")
                
                with col2:
                    tasks = phase.get('tasks', [])
                    st.write(f"**Number of Tasks:** {len(tasks)}")
                    if tasks:
                        st.write("**Task IDs:**")
                        for task_id in tasks[:5]:  # Show first 5 tasks
                            st.write(f"- {task_id}")
                        if len(tasks) > 5:
                            st.write(f"... and {len(tasks) - 5} more")
    
    # Schedule optimization insights
    optimization_suggestions = schedule_results.get("optimization_suggestions", [])
    if optimization_suggestions:
        st.subheader("💡 Schedule Optimization")
        for suggestion in optimization_suggestions:
            st.write(f"• {suggestion}")


def display_project_health(health_metrics):
    """Display project health and risk assessment"""
    st.subheader("🏥 Project Health Assessment")
    
    # Health metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        approval_rate = health_metrics.get("approval_rate_percentage", 0)
        st.metric("Task Approval Rate", f"{approval_rate}%")
    
    with col2:
        confidence = health_metrics.get("schedule_confidence", 0)
        st.metric("Schedule Confidence", f"{confidence}/10")
    
    with col3:
        risk_level = health_metrics.get("risk_level", "Unknown")
        risk_color = {"Low": "normal", "Medium": "inverse", "High": "inverse"}[risk_level]
        st.metric("Risk Level", risk_level, delta=None, delta_color=risk_color)


def main():
    """Main application function"""
    # Header
    st.markdown('<h1 class="main-header">🏗️ Construction Planning Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666; margin-bottom: 2rem;">AI-powered construction project planning and resource management</p>', unsafe_allow_html=True)
    
    # Check API key
    if not check_api_key():
        st.stop()
    
    # Sidebar for configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Example goals
    example_goals = [
        "Build a residential home",
        "Construct a commercial office building",
        "Site preparation for new development",
        "Foundation planning for warehouse",
        "Permit requirements for renovation project"
    ]
    
    st.sidebar.subheader("📝 Example Goals")
    for goal in example_goals:
        if st.sidebar.button(goal):
            st.session_state.example_goal = goal
    
    # Main input section
    st.header("🎯 Project Input")
    
    # Get goal from session state or input
    if 'example_goal' in st.session_state:
        default_goal = st.session_state.example_goal
        del st.session_state.example_goal
    else:
        default_goal = ""
    
    construction_goal = st.text_input(
        "Enter your construction goal:",
        placeholder="e.g., Build a 2-story residential home with 3 bedrooms",
        value=default_goal
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        generate_button = st.button("🚀 Generate Plan", type="primary", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ Clear Results", use_container_width=True)
    
    # Clear results
    if clear_button:
        if 'planning_results' in st.session_state:
            del st.session_state.planning_results
        st.rerun()
    
    # Generate plan
    if generate_button and construction_goal:
        if not construction_goal.strip():
            st.error("Please enter a construction goal!")
            return
        
        with st.spinner("🤖 AI Agents are working on your construction plan..."):
            try:
                # Initialize the planner
                planner = SimpleConstructionPlanner()
                
                # Execute planning workflow
                results = planner.plan_construction_project(construction_goal)
                
                # Store results in session state
                st.session_state.planning_results = results
                
                if results.get("status") == "completed":
                    st.success("✅ Construction plan generated successfully!")
                else:
                    st.error("❌ Failed to generate construction plan")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Please check your API configuration and try again.")
    
    # Display results
    if 'planning_results' in st.session_state:
        results = st.session_state.planning_results
        
        if results.get("status") == "completed":
            # Project metadata
            st.header("📊 Project Overview")
            metadata = results.get("project_metadata", {})
            display_project_metadata(metadata)
            
            # Summary section
            summary = results.get("summary", {})
            if summary:
                st.subheader("📋 Project Summary")
                st.write(summary.get("project_overview", ""))
                
                highlights = summary.get("key_highlights", [])
                if highlights:
                    st.write("**Key Highlights:**")
                    for highlight in highlights:
                        st.write(f"• {highlight}")
            
            # Tabbed interface for detailed results
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Tasks", "✅ Validation", "📅 Schedule", "🏥 Health"])
            
            with tab1:
                task_breakdown = results.get("task_breakdown", {})
                display_task_breakdown(task_breakdown)
            
            with tab2:
                validation_results = results.get("resource_validation", {})
                display_resource_validation(validation_results)
            
            with tab3:
                schedule_results = results.get("project_schedule", {})
                display_project_schedule(schedule_results)
            
            with tab4:
                health_metrics = results.get("project_health", {})
                display_project_health(health_metrics)
            
            # Next steps
            next_steps = summary.get("next_steps", [])
            if next_steps:
                st.header("🎯 Recommended Next Steps")
                for i, step in enumerate(next_steps, 1):
                    st.write(f"{i}. {step}")
            
            # Download results
            st.header("💾 Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Download JSON"):
                    json_data = json.dumps(results, indent=2)
                    st.download_button(
                        label="Download construction_plan.json",
                        data=json_data,
                        file_name=f"construction_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            
            with col2:
                if st.button("📋 Download Summary"):
                    summary_text = f"""
Construction Planning Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Goal: {metadata.get('goal', 'N/A')}

Key Metrics:
- Total Tasks: {metadata.get('total_tasks', 0)}
- Duration: {metadata.get('total_duration_days', 0)} days
- Estimated Cost: {metadata.get('total_estimated_cost', 'N/A')}

Project Overview:
{summary.get('project_overview', 'N/A')}

Key Highlights:
{chr(10).join(f"• {h}" for h in summary.get('key_highlights', []))}

Next Steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(next_steps))}
                    """
                    st.download_button(
                        label="Download summary.txt",
                        data=summary_text,
                        file_name=f"construction_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
        
        else:
            # Display error
            error_info = results.get("error", {})
            st.error(f"❌ Error: {error_info.get('message', 'Unknown error')}")
            
            suggestions = results.get("fallback_suggestions", [])
            if suggestions:
                st.subheader("💡 Suggestions")
                for suggestion in suggestions:
                    st.write(f"• {suggestion}")


if __name__ == "__main__":
    main()
