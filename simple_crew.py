"""
Hybrid Construction Planning: Deterministic Costs + LLM Task Planning
Rule-based cost and duration calculations with LLM for task breakdown only
"""
import os
import json
import re
from datetime import datetime
from typing import Dict, Any
from tools.resource_tools import (
    validate_all_resources, 
    calculate_project_cost, 
    calculate_project_duration
)
from config.llm_config import get_groq_client


class SimpleConstructionPlanner:
    """Hybrid construction planning with deterministic costs and LLM task planning"""
    
    def __init__(self):
        self.client = get_groq_client()
    
    def plan_construction_project(self, project_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete construction planning workflow with structured inputs"""
        try:
            # Extract project parameters
            area = project_params.get("area", 2000)
            floors = project_params.get("floors", 2)
            building_type = project_params.get("building_type", "Residential")
            quality = project_params.get("quality", "Standard")
            location = project_params.get("location", "Tier 2")
            description = project_params.get("description", f"{building_type} building")
            
            # Step 1: Calculate deterministic costs and duration
            cost_analysis = calculate_project_cost(area, quality, location, floors)
            duration_analysis = calculate_project_duration(area, floors, building_type)
            
            # Step 2: Generate task breakdown using LLM (without costs/durations)
            tasks = self._create_task_breakdown(description, building_type, duration_analysis)
            
            if not tasks or "error" in tasks:
                return self._create_error_response("planning", "Failed to generate tasks", description)
            
            # Step 3: Resource Validation with deterministic costs
            validation_results = self._validate_resources(tasks.get("tasks", []), cost_analysis)
            
            # Step 4: Create schedule based on deterministic duration
            schedule_results = self._create_schedule(
                validation_results.get("validated_tasks", []), 
                duration_analysis
            )
            
            # Step 5: Compile Results
            final_result = self._compile_final_results(
                project_params, cost_analysis, duration_analysis, 
                tasks, validation_results, schedule_results
            )
            
            return final_result
            
        except Exception as e:
            return self._create_error_response("workflow", str(e), str(project_params))
    
    def _create_task_breakdown(self, description: str, building_type: str, duration_analysis: Dict[str, Any]) -> dict:
        """Create task breakdown using Groq LLM (without cost/duration estimation)"""
        try:
            total_days = duration_analysis["total_days"]
            foundation_days = duration_analysis["foundation_days"]
            structure_days = duration_analysis["structure_days"]
            finishing_days = duration_analysis["finishing_days"]
            
            prompt = f"""
            You are a construction planning expert. Break down this {building_type.lower()} project into detailed tasks: "{description}"
            
            Project Timeline:
            - Total Duration: {total_days} days
            - Foundation Phase: {foundation_days} days
            - Structural Phase: {structure_days} days  
            - Finishing Phase: {finishing_days} days
            
            Return ONLY JSON format with tasks and realistic durations:
            {{
              "goal": "{description}",
              "tasks": [
                {{
                  "id": "task_1",
                  "name": "Task name",
                  "description": "Detailed, comprehensive description explaining what this task involves, materials needed, and key considerations",
                  "category": "permits|site_preparation|foundation|structural|utilities|finishing",
                  "estimated_duration_days": 5,
                  "dependencies": []
                }}
              ]
            }}
            
            Create 10-12 realistic tasks with proper sequencing and detailed descriptions:
            
            TASK DISTRIBUTION GUIDELINES:
            - Permits: 1-2 tasks (5-10 days total)
            - Site Preparation: 1-2 tasks (5-10 days total)
            - Foundation: 2-3 tasks ({foundation_days} days total)
            - Structural: 3-4 tasks ({structure_days} days total)
            - Utilities: 1-2 tasks (5-10 days total)
            - Finishing: 2-3 tasks ({finishing_days} days total)
            
            DESCRIPTION REQUIREMENTS:
            - Each description should be 2-3 sentences
            - Explain what the task involves
            - Mention key materials or equipment needed
            - Include important considerations or quality checks
            
            DO NOT include any cost estimates.
            Focus on realistic construction sequencing and detailed explanations.
            """
            
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "Could not parse response", "raw": content}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _validate_resources(self, tasks: list, cost_analysis: Dict[str, Any]) -> dict:
        """Validate resources for all tasks using deterministic costs"""
        validated_tasks = []
        
        for task in tasks:
            validation_result = validate_all_resources(task, cost_analysis)
            # Preserve LLM-generated duration
            validation_result['estimated_duration_days'] = task.get('estimated_duration_days', 0)
            validated_tasks.append(validation_result)
        
        return {
            "validated_tasks": validated_tasks,
            "total_tasks": len(validated_tasks),
            "approved_tasks": len([t for t in validated_tasks if t["overall_available"]]),
            "blocked_tasks": len([t for t in validated_tasks if not t["overall_available"]])
        }
    
    def _create_schedule(self, validated_tasks: list, duration_analysis: Dict[str, Any]) -> dict:
        """Create project schedule based on deterministic duration analysis"""
        if not validated_tasks:
            return {"schedule": [], "total_project_duration": 0}
        
        # Sort tasks by category priority
        category_priority = {
            'permits': 1,
            'site_preparation': 2,
            'foundation': 3,
            'structural': 4,
            'utilities': 5,
            'finishing': 6
        }
        
        sorted_tasks = sorted(validated_tasks, key=lambda t: (
            category_priority.get(t.get('category', ''), 99),
            len(t.get('dependencies', []))
        ))
        
        schedule_tasks = []
        current_day = 1
        
        # Allocate days based on deterministic analysis
        foundation_days = duration_analysis["foundation_days"]
        structure_days = duration_analysis["structure_days"]
        finishing_days = duration_analysis["finishing_days"]
        
        category_day_allocation = {
            'permits': max(3, int(foundation_days * 0.2)),
            'site_preparation': max(5, int(foundation_days * 0.3)),
            'foundation': max(7, int(foundation_days * 0.5)),
            'structural': max(10, int(structure_days * 0.7)),
            'utilities': max(5, int(structure_days * 0.3)),
            'finishing': max(7, int(finishing_days * 1.0))
        }
        
        for task in sorted_tasks:
            # Use LLM-generated duration if available, otherwise fallback to category allocation
            task_category = task.get('category', '')
            llm_duration = task.get('estimated_duration_days', 0)
            
            if llm_duration > 0:
                duration = llm_duration
            else:
                # Fallback to category-based allocation
                duration = category_day_allocation.get(task_category, 5)
            
            start_day = current_day
            end_day = start_day + duration - 1
            
            schedule_task = {
                "task_id": task.get('task_id', task.get('id', '')),
                "task_name": task.get('task_name', task.get('name', '')),
                "start_day": start_day,
                "end_day": end_day,
                "duration_days": duration,
                "dependencies_completed": task.get('dependencies', []),
                "critical_path": task.get('category') in ['foundation', 'structural'],
                "validation_status": task.get('validation_status', 'unknown')
            }
            
            schedule_tasks.append(schedule_task)
            current_day += duration
        
        total_duration = duration_analysis["total_days"]
        
        return {
            "schedule": schedule_tasks,
            "total_project_duration": total_duration,
            "critical_path_tasks": [task["task_id"] for task in schedule_tasks if task["critical_path"]],
            "optimization_suggestions": [
                "Monitor resource availability",
                "Build buffer time for weather",
                "Consider parallel tasks where possible"
            ],
            "schedule_confidence": 8,
            "duration_breakdown": {
                "foundation_days": foundation_days,
                "structure_days": structure_days,
                "finishing_days": finishing_days
            }
        }
    
    def _compile_final_results(self, project_params: Dict[str, Any], cost_analysis: Dict[str, Any], 
                             duration_analysis: Dict[str, Any], tasks: dict, validation: dict, 
                             schedule: dict) -> Dict[str, Any]:
        """Compile final results with deterministic costs and durations"""
        total_tasks = len(tasks.get("tasks", []))
        approved_tasks = validation.get("approved_tasks", 0)
        total_duration = duration_analysis["total_days"]
        total_cost = cost_analysis["total_cost"]
        
        return {
            "project_metadata": {
                "goal": project_params.get("description", ""),
                "area": project_params.get("area"),
                "floors": project_params.get("floors"),
                "building_type": project_params.get("building_type"),
                "quality": project_params.get("quality"),
                "location": project_params.get("location"),
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_tasks": total_tasks,
                "total_duration_days": total_duration,
                "total_estimated_cost": f"₹{total_cost:,}"
            },
            "cost_breakdown": {
                "total_cost": f"₹{total_cost:,}",
                "labor_cost": f"₹{cost_analysis['labor_cost']:,}",
                "material_cost": f"₹{cost_analysis['material_cost']:,}",
                "equipment_cost": f"₹{cost_analysis['equipment_cost']:,}",
                "cost_per_sqft": f"₹{cost_analysis['cost_per_sqft']:,}",
                "location_factor": cost_analysis['location_factor'],
                "ground_floor_area": project_params.get("area"),
                "effective_floors": cost_analysis.get('effective_floors', 1.0),
                "total_builtup_area": cost_analysis.get('total_builtup_area', project_params.get("area", 0))
            },
            "duration_breakdown": {
                "total_days": total_duration,
                "foundation_days": duration_analysis["foundation_days"],
                "structure_days": duration_analysis["structure_days"],
                "finishing_days": duration_analysis["finishing_days"],
                "base_duration": duration_analysis.get("base_duration", 0),
                "floor_factor": duration_analysis.get("floor_factor", 1.0),
                "area_factor": duration_analysis.get("area_factor", 1.0),
                "days_per_sqft": round(duration_analysis["duration_per_sqft"], 3)
            },
            "task_breakdown": tasks,
            "resource_validation": validation,
            "project_schedule": schedule,
            "project_health": {
                "approval_rate_percentage": round((approved_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1),
                "schedule_confidence": schedule.get("schedule_confidence", 8),
                "risk_level": "Low" if approved_tasks >= total_tasks * 0.8 else "Medium"
            },
            "summary": {
                "project_overview": f"Construction plan for '{project_params.get('description', '')}' - {project_params.get('area')} sq ft, {project_params.get('floors')} floors",
                "key_highlights": [
                    f"{approved_tasks} of {total_tasks} tasks approved for execution",
                    f"Estimated project duration: {total_duration} days",
                    f"Total estimated cost: ₹{total_cost:,}",
                    f"Cost per sq ft: ₹{cost_analysis['cost_per_sqft']:,}"
                ]
            },
            "estimation_methodology": "Deterministic rule-based calculations with industry-standard benchmarks",
            "status": "completed"
        }
    
    def _create_error_response(self, error_type: str, error_message: str, project_info: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "project_metadata": {
                "goal": project_info,
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "error": {
                "type": error_type,
                "message": error_message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "status": "failed"
        }


# Update the app.py to use this improved version
def plan_construction_project(project_params: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function"""
    planner = SimpleConstructionPlanner()
    return planner.plan_construction_project(project_params)
