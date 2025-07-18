import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
import random

# Load API key
from dotenv import load_dotenv
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# Initialize Gemini Model
llm = ChatGoogleGenerativeAI(
    model="models/gemini-1.5-flash-latest",
    temperature=0.3
)

# Appliance Power Consumption Data (in watts)
APPLIANCE_POWER = {
    "fan": 75,
    "ac": 1500,
    "lights": 60,
    "refrigerator": 150,
    "tv": 120,
    "washing_machine": 500,
    "water_heater": 1200,
    "microwave": 800
}

# Energy cost per kWh (in rupees)
ENERGY_COST_PER_KWH = 6.5

# Simulate User Energy Usage Data
def simulate_energy_data(days: int = 7) -> Dict[str, Any]:
    """Simulate realistic energy usage data for multiple days"""
    data = {
        "user_id": str(uuid.uuid4()),
        "period": f"{days} days",
        "daily_usage": []
    }
    
    for day in range(days):
        date = datetime.now() - timedelta(days=days-day-1)
        daily_data = {
            "date": date.strftime("%Y-%m-%d"),
            "appliances": {}
        }
        
        # Simulate usage hours for each appliance
        for appliance, power in APPLIANCE_POWER.items():
            if appliance == "refrigerator":
                # Refrigerator runs 24/7
                hours = 24
            elif appliance == "ac":
                # AC usage varies by season/weather
                hours = random.uniform(6, 12)
            elif appliance == "fan":
                hours = random.uniform(8, 16)
            elif appliance == "lights":
                hours = random.uniform(4, 8)
            elif appliance == "tv":
                hours = random.uniform(3, 6)
            elif appliance == "washing_machine":
                hours = random.uniform(0.5, 1.5) if random.random() > 0.3 else 0
            elif appliance == "water_heater":
                hours = random.uniform(1, 3)
            else:
                hours = random.uniform(0.5, 2)
            
            daily_data["appliances"][appliance] = {
                "hours": round(hours, 2),
                "power_watts": power,
                "energy_kwh": round((hours * power) / 1000, 2),
                "cost_rupees": round(((hours * power) / 1000) * ENERGY_COST_PER_KWH, 2)
            }
        
        daily_data["total_kwh"] = sum(app["energy_kwh"] for app in daily_data["appliances"].values())
        daily_data["total_cost"] = sum(app["cost_rupees"] for app in daily_data["appliances"].values())
        
        data["daily_usage"].append(daily_data)
    
    return data

# Data Validator
def data_validator(state: dict) -> dict:
    """Validate and clean energy usage data"""
    try:
        if not state.get("energy_data"):
            state["energy_data"] = simulate_energy_data()
        
        # Calculate totals
        total_kwh = sum(day["total_kwh"] for day in state["energy_data"]["daily_usage"])
        total_cost = sum(day["total_cost"] for day in state["energy_data"]["daily_usage"])
        avg_daily_kwh = total_kwh / len(state["energy_data"]["daily_usage"])
        avg_daily_cost = total_cost / len(state["energy_data"]["daily_usage"])
        
        state["summary"] = {
            "total_kwh": round(total_kwh, 2),
            "total_cost": round(total_cost, 2),
            "avg_daily_kwh": round(avg_daily_kwh, 2),
            "avg_daily_cost": round(avg_daily_cost, 2),
            "days_analyzed": len(state["energy_data"]["daily_usage"])
        }
        
        return state
    except Exception as e:
        state["error"] = f"Data validation error: {str(e)}"
        return state

# Usage Pattern Analyzer
def usage_pattern_analyzer(state: dict) -> dict:
    """Analyze energy usage patterns and identify inefficiencies"""
    prompt = f"""
You are an expert energy efficiency analyst. Analyze the following energy usage data:

Total Energy Consumption: {state['summary']['total_kwh']} kWh over {state['summary']['days_analyzed']} days
Average Daily Usage: {state['summary']['avg_daily_kwh']} kWh
Total Cost: ₹{state['summary']['total_cost']}
Average Daily Cost: ₹{state['summary']['avg_daily_cost']}

Appliance-wise analysis:
"""
    
    # Add appliance analysis
    appliance_totals = {}
    for day in state["energy_data"]["daily_usage"]:
        for appliance, data in day["appliances"].items():
            if appliance not in appliance_totals:
                appliance_totals[appliance] = {"total_kwh": 0, "total_cost": 0, "avg_hours": 0}
            appliance_totals[appliance]["total_kwh"] += data["energy_kwh"]
            appliance_totals[appliance]["total_cost"] += data["cost_rupees"]
            appliance_totals[appliance]["avg_hours"] += data["hours"]
    
    for appliance, totals in appliance_totals.items():
        totals["avg_hours"] = round(totals["avg_hours"] / state['summary']['days_analyzed'], 2)
        prompt += f"\n- {appliance.title()}: {totals['total_kwh']} kWh, ₹{totals['total_cost']}, avg {totals['avg_hours']} hours/day"
    
    prompt += """

Analyze this data and provide:
1. Overall energy consumption assessment
2. Identify top 3 energy-consuming appliances
3. Detect any unusual patterns or wastage
4. Brief efficiency rating (Excellent/Good/Average/Poor)

Keep the analysis concise and actionable.
"""
    
    response = llm.invoke(prompt)
    state["pattern_analysis"] = response.content.strip()
    state["appliance_totals"] = appliance_totals
    return state

# Consumption Router
def consumption_router(state: dict) -> str:
    """Route based on energy consumption level"""
    avg_daily_kwh = state['summary']['avg_daily_kwh']
    
    # Classification based on typical Indian household consumption
    if avg_daily_kwh <= 8:
        return "efficient"
    elif avg_daily_kwh <= 15:
        return "moderate"
    else:
        return "excessive"

# Efficient User Agent
def efficient_user_agent(state: dict) -> dict:
    """Handle users with efficient energy consumption"""
    prompt = f"""
Excellent energy management! Your consumption analysis:

{state['pattern_analysis']}

Average daily usage: {state['summary']['avg_daily_kwh']} kWh
Daily cost: ₹{state['summary']['avg_daily_cost']}

As an efficient energy user:
1. Provide 2 lines of encouragement
2. Suggest 2 advanced tips to maintain or improve efficiency
3. Recommend one eco-friendly upgrade

Keep it motivational and forward-looking.
"""
    
    response = llm.invoke(prompt)
    state["recommendation"] = response.content.strip()
    state["category"] = "efficient"
    return state

# Moderate User Agent
def moderate_user_agent(state: dict) -> dict:
    """Handle users with moderate energy consumption"""
    prompt = f"""
Your energy usage shows room for improvement:

{state['pattern_analysis']}

Average daily usage: {state['summary']['avg_daily_kwh']} kWh
Daily cost: ₹{state['summary']['avg_daily_cost']}

As a moderate energy user:
1. Identify 3 specific areas for improvement
2. Provide practical tips to reduce consumption by 15-20%
3. Suggest behavioral changes for better efficiency
4. Estimate potential monthly savings

Be encouraging but actionable.
"""
    
    response = llm.invoke(prompt)
    state["recommendation"] = response.content.strip()
    state["category"] = "moderate"
    return state

# Excessive User Agent
def excessive_user_agent(state: dict) -> dict:
    """Handle users with excessive energy consumption"""
    prompt = f"""
Your energy consumption needs immediate attention:

{state['pattern_analysis']}

Average daily usage: {state['summary']['avg_daily_kwh']} kWh
Daily cost: ₹{state['summary']['avg_daily_cost']}

As a high-consumption user:
1. Gently highlight the environmental and financial impact
2. Provide 4 immediate action steps to reduce consumption
3. Suggest priority appliances to optimize first
4. Recommend consulting an energy audit professional
5. Estimate potential monthly savings with improvements

Be supportive while emphasizing urgency.
"""
    
    response = llm.invoke(prompt)
    state["recommendation"] = response.content.strip()
    state["category"] = "excessive"
    return state

# Wastage Detector
def wastage_detector(state: dict) -> dict:
    """Detect specific wastage patterns"""
    wastage_issues = []
    
    for appliance, totals in state["appliance_totals"].items():
        avg_hours = totals["avg_hours"]
        
        # Define wastage thresholds
        if appliance == "ac" and avg_hours > 10:
            wastage_issues.append(f"AC running {avg_hours} hours/day - consider using timer/thermostat")
        elif appliance == "lights" and avg_hours > 6:
            wastage_issues.append(f"Lights on {avg_hours} hours/day - check for unnecessary usage")
        elif appliance == "fan" and avg_hours > 14:
            wastage_issues.append(f"Fan running {avg_hours} hours/day - optimize based on occupancy")
        elif appliance == "tv" and avg_hours > 5:
            wastage_issues.append(f"TV on {avg_hours} hours/day - consider reducing screen time")
        elif appliance == "water_heater" and avg_hours > 2.5:
            wastage_issues.append(f"Water heater on {avg_hours} hours/day - check for leaks/insulation")
    
    state["wastage_issues"] = wastage_issues
    return state

# Smart Suggestions Generator
def smart_suggestions_generator(state: dict) -> dict:
    """Generate smart, personalized suggestions"""
    prompt = f"""
Based on the energy analysis, generate smart suggestions:

Category: {state['category']}
Wastage Issues: {state.get('wastage_issues', [])}
Top Energy Consumers: {sorted(state['appliance_totals'].items(), key=lambda x: x[1]['total_kwh'], reverse=True)[:3]}

Provide:
1. 3 immediate actionable tips
2. 2 long-term improvements
3. 1 behavioral change recommendation
4. Estimated monthly savings potential

Make suggestions specific and practical for Indian households.
"""
    
    response = llm.invoke(prompt)
    state["smart_suggestions"] = response.content.strip()
    return state

# Usage Logger
def usage_logger(state: dict) -> dict:
    """Log the energy usage analysis session"""
    log = {
        "id": str(uuid.uuid4()),
        "timestamp": str(datetime.now()),
        "user_id": state["energy_data"]["user_id"],
        "analysis_period": state["energy_data"]["period"],
        "summary": state["summary"],
        "category": state.get("category", ""),
        "wastage_issues": state.get("wastage_issues", []),
        "recommendation": state.get("recommendation", ""),
        "smart_suggestions": state.get("smart_suggestions", "")
    }
    
    os.makedirs("energy_logs", exist_ok=True)
    with open(f"energy_logs/session_{log['id']}.json", "w") as f:
        json.dump(log, f, indent=2)
    
    state["log_id"] = log["id"]
    return state

# Action Plan Generator
def action_plan_generator(state: dict) -> dict:
    """Generate a comprehensive action plan"""
    prompt = f"""
Create a 30-day action plan based on the analysis:

Category: {state['category']}
Current Usage: {state['summary']['avg_daily_kwh']} kWh/day
Current Cost: ₹{state['summary']['avg_daily_cost']}/day

Generate:
1. Week 1-2 immediate actions
2. Week 3-4 implementation phase
3. Monthly review checkpoints
4. Success metrics to track
5. Motivational milestones

Make it a practical, easy-to-follow plan.
"""
    
    response = llm.invoke(prompt)
    state["action_plan"] = response.content.strip()
    return state

# Build EcoAgent Workflow
def run_eco_agent(user_data: dict = None) -> dict:
    """Main function to run the EcoAgent workflow"""
    
    # Initialize state
    if user_data is None:
        user_data = {}
    
    # Build the workflow graph
    builder = StateGraph(dict)
    
    # Set entry point
    builder.set_entry_point("data_validator")
    
    # Add nodes
    builder.add_node("data_validator", data_validator)
    builder.add_node("usage_pattern_analyzer", usage_pattern_analyzer)
    builder.add_node("consumption_router", usage_pattern_analyzer)  # Reuse for routing
    builder.add_node("efficient_user", efficient_user_agent)
    builder.add_node("moderate_user", moderate_user_agent)
    builder.add_node("excessive_user", excessive_user_agent)
    builder.add_node("wastage_detector", wastage_detector)
    builder.add_node("smart_suggestions", smart_suggestions_generator)
    builder.add_node("usage_logger", usage_logger)
    builder.add_node("action_plan", action_plan_generator)
    
    # Add edges
    builder.add_edge("data_validator", "usage_pattern_analyzer")
    builder.add_edge("usage_pattern_analyzer", "consumption_router")
    
    # Add conditional edges based on consumption level
    builder.add_conditional_edges("consumption_router", consumption_router, {
        "efficient": "efficient_user",
        "moderate": "moderate_user",
        "excessive": "excessive_user"
    })
    
    # All paths lead to wastage detection
    builder.add_edge("efficient_user", "wastage_detector")
    builder.add_edge("moderate_user", "wastage_detector")
    builder.add_edge("excessive_user", "wastage_detector")
    
    # Continue the workflow
    builder.add_edge("wastage_detector", "smart_suggestions")
    builder.add_edge("smart_suggestions", "usage_logger")
    builder.add_edge("usage_logger", "action_plan")
    builder.add_edge("action_plan", END)
    
    # Compile and run the graph
    graph = builder.compile()
    result = graph.invoke(user_data)
    
    return result

# Demo function
def demo_eco_agent():
    """Demonstrate the EcoAgent system"""
    print("🌱 EcoAgent: Smart Energy Usage Advisor")
    print("=" * 50)
    
    # Run the agent
    result = run_eco_agent()
    
    # Display results
    print(f"\n📊 Energy Usage Summary:")
    print(f"Period: {result['summary']['days_analyzed']} days")
    print(f"Total Consumption: {result['summary']['total_kwh']} kWh")
    print(f"Total Cost: ₹{result['summary']['total_cost']}")
    print(f"Average Daily: {result['summary']['avg_daily_kwh']} kWh (₹{result['summary']['avg_daily_cost']})")
    print(f"Category: {result['category'].upper()}")
    
    print(f"\n🔍 Pattern Analysis:")
    print(result['pattern_analysis'])
    
    print(f"\n💡 Recommendations:")
    print(result['recommendation'])
    
    if result.get('wastage_issues'):
        print(f"\n⚠️  Wastage Issues Detected:")
        for issue in result['wastage_issues']:
            print(f"• {issue}")
    
    print(f"\n🎯 Smart Suggestions:")
    print(result['smart_suggestions'])
    
    print(f"\n📋 30-Day Action Plan:")
    print(result['action_plan'])
    
    print(f"\n💾 Session logged with ID: {result['log_id']}")

if __name__ == "__main__":
    demo_eco_agent()