from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.gemini_client import analyze_image
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)
bp=Blueprint("reports", __name__)

# Fast template-based descriptions by category (instant, no AI needed)
CATEGORY_TEMPLATES = {
    "Roads": {
        "title": "Road Damage Report",
        "description": "Road surface damage including potholes, cracks, or uneven patches observed at the reported location. This poses safety risks to vehicles and pedestrians and requires immediate inspection and repair.",
        "priority": 4,
    },
    "Water": {
        "title": "Water Supply Issue",
        "description": "Water-related problem such as leakage, pipe burst, or supply disruption reported at this location. This affects daily water access for residents and requires urgent attention from the water works department.",
        "priority": 5,
    },
    "Sanitation": {
        "title": "Sanitation Problem",
        "description": "Sanitation issue including garbage accumulation, drain blockage, or public toilet maintenance needed at the reported location. This creates health hazards and requires prompt cleaning and maintenance.",
        "priority": 4,
    },
    "Electricity": {
        "title": "Electrical Hazard",
        "description": "Electrical issue such as exposed wiring, non-functional street lights, or power supply problems at the reported location. This poses safety risks and requires immediate attention from electrical services.",
        "priority": 5,
    },
    "Parks": {
        "title": "Park Maintenance Needed",
        "description": "Park or green space maintenance issue including overgrown vegetation, broken equipment, or cleanliness problems at the reported location. This affects public recreation and requires maintenance attention.",
        "priority": 2,
    },
    "Street Lights": {
        "title": "Street Light Not Working",
        "description": "Non-functional or damaged street lighting at the reported location. This creates safety concerns for pedestrians and vehicles during night hours and requires immediate electrical repair.",
        "priority": 4,
    },
    "Encroachment": {
        "title": "Illegal Encroachment",
        "description": "Unauthorized construction or encroachment on public property or roads at the reported location. This affects traffic flow and public space availability and requires enforcement action.",
        "priority": 3,
    },
    "Others": {
        "title": "Civic Issue Report",
        "description": "Civic issue reported at the location that requires municipal attention and resolution. Please inspect the area and take appropriate action based on the severity and nature of the problem.",
        "priority": 3,
    },
}

def _fast_describe(category, address):
    """Generate instant description without AI - always fast"""
    template = CATEGORY_TEMPLATES.get(category, CATEGORY_TEMPLATES["Others"])
    location_text = f" at {address}" if address else ""
    return {
        "title": template["title"],
        "description": f"{template['description']}{location_text}.",
        "suggested_category": category,
        "priority": template["priority"],
        "summary": f"Instant analysis based on category: {category}",
    }

@bp.post("/ai/describe-issue")
def describe_issue():
    try:
        data = request.get_json()
        image_data = data.get('image')
        category = data.get('category', 'Others')
        address = data.get('address', '')

        if not image_data:
            logger.error("No image provided in request")
            return jsonify({"error": "No image provided"}), 400

        logger.info(f"Analyzing image for category: {category}, address: {address}")
        
        # Try AI analysis directly
        try:
            logger.info("Attempting AI image analysis with Ollama")
            analysis = analyze_image(image_data, category, address)
            logger.info(f"AI analysis result: {analysis.get('summary')}")
            
            # Check if this is a successful AI analysis
            summary = analysis.get('summary', '')
            is_successful = 'Image analyzed' in summary or 'analyzed successfully' in summary.lower()
            
            if is_successful:
                logger.info("AI analysis successful, returning AI result")
                return jsonify({
                    "title": analysis.get('title', 'Issue Report'),
                    "description": analysis.get('description', 'Image analysis completed'),
                    "suggested_category": analysis.get('category', category),
                    "priority": analysis.get('priority', 3),
                    "summary": analysis.get('summary', 'AI analysis completed'),
                })
            else:
                logger.warning(f"AI analysis returned error: {summary}")
                fast_result = _fast_describe(category, address)
                return jsonify(fast_result)
        except Exception as ai_err:
            logger.warning(f"AI analysis exception: {ai_err}")
            fast_result = _fast_describe(category, address)
            return jsonify(fast_result)

    except Exception as e:
        logger.exception(f"Error in describe_issue: {str(e)}")
        return jsonify({"error": str(e), "title": "Issue Report", "description": "Image analysis failed"}), 500

@bp.post("/ai/weekly-report")
def weekly_report():
    ward_id=request.json.get("ward_id", "all")
    html=f"<h2>Weekly District Summary ({ward_id})</h2><p>Generated {datetime.utcnow().isoformat()}Z</p><ul><li>Resolution trending upward</li><li>Top categories: Roads, Water</li></ul>"
    return jsonify({"summary_html": html})
