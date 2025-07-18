from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
from app import run_eco_agent, simulate_energy_data, APPLIANCE_POWER, ENERGY_COST_PER_KWH
app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/appliances', methods=['GET'])
def get_appliances():
    """Get appliance data for the frontend"""
    return jsonify({
        'appliances': APPLIANCE_POWER,
        'energy_cost': ENERGY_COST_PER_KWH
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_usage():
    """Analyze user energy usage"""
    try:
        data = request.get_json()
        
        if not data or 'usage' not in data:
            return jsonify({'error': 'No usage data provided'}), 400
        
        usage_data = data['usage']
        days = data.get('days', 7)
        
        # Create energy data structure
        energy_data = create_energy_data_from_usage(usage_data, days)
        
        # Run the EcoAgent analysis
        result = run_eco_agent({'energy_data': energy_data})
        
        # Format response for frontend
        response = {
            'success': True,
            'analysis': {
                'summary': result['summary'],
                'category': result['category'],
                'pattern_analysis': result['pattern_analysis'],
                'recommendation': result['recommendation'],
                'wastage_issues': result.get('wastage_issues', []),
                'smart_suggestions': result['smart_suggestions'],
                'action_plan': result['action_plan'],
                'appliance_breakdown': result['appliance_totals']
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_energy_data_from_usage(usage_data, days):
    """Create energy data structure from user input"""
    energy_data = {
        'user_id': f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'period': f"{days} days",
        'daily_usage': []
    }
    
    for day in range(days):
        date = datetime.now().strftime('%Y-%m-%d')
        daily_data = {
            'date': date,
            'appliances': {}
        }
        
        total_kwh = 0
        total_cost = 0
        
        for appliance, hours in usage_data.items():
            if appliance in APPLIANCE_POWER:
                power = APPLIANCE_POWER[appliance]
                energy_kwh = (hours * power) / 1000
                cost = energy_kwh * ENERGY_COST_PER_KWH
                
                daily_data['appliances'][appliance] = {
                    'hours': hours,
                    'power_watts': power,
                    'energy_kwh': energy_kwh,
                    'cost_rupees': cost
                }
                
                total_kwh += energy_kwh
                total_cost += cost
        
        daily_data['total_kwh'] = total_kwh
        daily_data['total_cost'] = total_cost
        energy_data['daily_usage'].append(daily_data)
    
    return energy_data

@app.route('/api/simulate', methods=['POST'])
def simulate_usage():
    """Generate simulated energy usage data"""
    try:
        data = request.get_json()
        days = data.get('days', 7) if data else 7
        
        # Generate simulated data
        simulated_data = simulate_energy_data(days)
        
        # Run analysis on simulated data
        result = run_eco_agent({'energy_data': simulated_data})
        
        response = {
            'success': True,
            'simulated_data': simulated_data,
            'analysis': {
                'summary': result['summary'],
                'category': result['category'],
                'pattern_analysis': result['pattern_analysis'],
                'recommendation': result['recommendation'],
                'wastage_issues': result.get('wastage_issues', []),
                'smart_suggestions': result['smart_suggestions'],
                'action_plan': result['action_plan']
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent analysis logs"""
    try:
        logs_dir = 'energy_logs'
        if not os.path.exists(logs_dir):
            return jsonify({'logs': []})
        
        log_files = []
        for filename in os.listdir(logs_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(logs_dir, filename)
                with open(filepath, 'r') as f:
                    log_data = json.load(f)
                    log_files.append(log_data)
        
        # Sort by timestamp (most recent first)
        log_files.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({'logs': log_files[:10]})  # Return last 10 logs
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tips', methods=['GET'])
def get_energy_tips():
    """Get general energy saving tips"""
    tips = [
        {
            'category': 'Cooling',
            'tip': 'Set your AC to 24°C or higher. Every degree lower increases energy consumption by 6-8%.',
            'savings': 'Up to 20% reduction in cooling costs'
        },
        {
            'category': 'Lighting',
            'tip': 'Replace incandescent bulbs with LED bulbs. They use 75% less energy and last 25 times longer.',
            'savings': '₹500-800 annually per household'
        },
        {
            'category': 'Appliances',
            'tip': 'Unplug electronics when not in use. Many devices consume power even when turned off.',
            'savings': '5-10% reduction in electricity bills'
        },
        {
            'category': 'Water Heating',
            'tip': 'Insulate your water heater and pipes. Set water heater temperature to 120°F (49°C).',
            'savings': '10-15% reduction in water heating costs'
        },
        {
            'category': 'Refrigeration',
            'tip': 'Keep your refrigerator at 37-40°F and freezer at 0-5°F. Clean coils regularly.',
            'savings': '10-15% reduction in refrigeration costs'
        },
        {
            'category': 'Washing',
            'tip': 'Wash clothes in cold water when possible. 90% of energy used by washing machines goes to heating water.',
            'savings': '₹200-400 annually per household'
        }
    ]
    
    return jsonify({'tips': tips})

@app.route('/api/benchmarks', methods=['GET'])
def get_benchmarks():
    """Get energy consumption benchmarks"""
    benchmarks = {
        'household_types': {
            'small_apartment': {
                'description': '1-2 BHK apartment',
                'daily_kwh': '5-8',
                'monthly_cost': '₹975-1560'
            },
            'medium_house': {
                'description': '2-3 BHK house',
                'daily_kwh': '8-15',
                'monthly_cost': '₹1560-2925'
            },
            'large_house': {
                'description': '3+ BHK house',
                'daily_kwh': '15-25',
                'monthly_cost': '₹2925-4875'
            }
        },
        'efficiency_ratings': {
            'excellent': {'range': '< 6 kWh/day', 'description': 'Highly efficient usage'},
            'good': {'range': '6-10 kWh/day', 'description': 'Above average efficiency'},
            'average': {'range': '10-15 kWh/day', 'description': 'Typical household usage'},
            'poor': {'range': '15-20 kWh/day', 'description': 'Below average efficiency'},
            'very_poor': {'range': '> 20 kWh/day', 'description': 'Highly inefficient usage'}
        }
    }
    
    return jsonify({'benchmarks': benchmarks})

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('energy_logs', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Create a basic HTML template if it doesn't exist
    template_path = 'templates/index.html'
    if not os.path.exists(template_path):
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EcoAgent - Smart Energy Advisor</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-blue-50 to-green-50 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">
                🌱 EcoAgent
            </h1>
            <p class="text-lg text-gray-600">Smart Energy Usage Advisor</p>
        </div>
        
        <div class="max-w-4xl mx-auto">
            <div class="bg-white rounded-xl shadow-lg p-8 mb-8">
                <h2 class="text-2xl font-semibold mb-6">Flask API Server Running</h2>
                <p class="text-gray-600 mb-4">
                    The EcoAgent Flask server is running successfully. You can access the following endpoints:
                </p>
                <ul class="list-disc list-inside space-y-2 text-gray-700">
                    <li><code>/api/appliances</code> - Get appliance data</li>
                    <li><code>/api/analyze</code> - Analyze energy usage (POST)</li>
                    <li><code>/api/simulate</code> - Generate simulated data (POST)</li>
                    <li><code>/api/logs</code> - Get recent analysis logs</li>
                    <li><code>/api/tips</code> - Get energy saving tips</li>
                    <li><code>/api/benchmarks</code> - Get consumption benchmarks</li>
                </ul>
                <p class="text-gray-600 mt-4">
                    For the full web interface, please use the standalone HTML file provided.
                </p>
            </div>
        </div>
    </div>
</body>
</html>
            """)
    
    app.run(debug=True, host='0.0.0.0', port=5000)