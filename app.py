from flask import Flask, jsonify, render_template, request
from health_genealogy_core import HealthGenealogy, llm_analysis, answer_question_with_context
import json
import anthropic
import os

app = Flask(__name__)

def load_data(language='en'):
    genealogy = HealthGenealogy()
    genealogy.load_from_json('sample_0.0.1.json')
    health_data_string = genealogy.traverse_and_dump()
    llm_result = llm_analysis(health_data_string, language)

    return genealogy, llm_result

def get_health_data_string(language="en"):
    genealogy = HealthGenealogy()
    genealogy.load_from_json('sample_0.0.1.json')
    return genealogy.traverse_and_dump()

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/user_query', methods=['POST'])
def user_query():
    data = request.json
    user_query = data.get('query')
    lang = data.get('lang')

    if not user_query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        # Extract the assistant's response
        data = get_health_data_string()
        app.logger.info(data)
        response = answer_question_with_context(data, user_query, language=lang)
        app.logger.info(response)
        return jsonify({'result': response })

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/health-data')
def get_health_data():
    language = request.args.get('lang', 'en')
    print(f"Requested language: {language}")  # Debug print
    
    genealogy, llm_result = load_data(language)
    
    nodes = []
    edges = []
    for person in genealogy.people.values():
        formal_name = person.formal_name.get(language, person.formal_name.get('en', ''))
        familiar_name = person.familiar_name.get(language, person.familiar_name.get('en', ''))
        
        nodes.append({
            'data': {
                'id': person.id,
                'label': familiar_name or formal_name,
                'conditions': person.health_data.get('conditions', [])
            }
        })
        for relationship, related_id in person.relationships.items():
            edges.append({
                'data': {
                    'source': related_id,
                    'target': person.id,
                    'label': relationship
                }
            })
    
    try:
        llm_result_json = json.loads(llm_result)
        print(f"LLM result: {llm_result_json}")  # Debug print
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM result: {e}")
        print(f"LLM result: {llm_result}")
        llm_result_json = {}
    
    response_data = {
        'nodes': nodes,
        'edges': edges,
        'analysis': llm_result_json
    }
    
    return jsonify(response_data)

@app.route('/api/condition-details', methods=['POST'])
def get_condition_details():
    data = request.json
    condition = data.get('condition')
    analysis = data.get('analysis')
    language = data.get('lang', 'en')
    
    if not condition or not analysis:
        return jsonify({'error': 'Missing condition or analysis data'}), 400

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)
    print(analysis) # Debug
    if language == 'ko':
        prompt = f"""
        다음 건강 분석을 기반으로:
        {json.dumps(analysis, indent=2)}

        다음 질환에 대한 상세 정보를 제공해주세요: {condition}

        다음 형식으로 응답을 구성해주세요:

        1. 위험도 평가:
           • 가족력을 바탕으로 사용자가 이 질환을 발병할 위험도(낮음, 중간, 높음)를 제공해주세요.
           • 이 위험도 평가의 근거를 간단히 설명해주세요.

        2. 가족력 및 유전:
           • 제공된 '유전 패턴'을 바탕으로 이 질환이 사용자의 가계도에 어떻게 나타나는지 설명해주세요.
           • 사용자 가족의 이 질환에 대한 특정 유전 패턴을 설명해주세요.
           • 가족력을 바탕으로 사용자가 이 질환을 유전받거나 발병할 위험에 대해 논의해주세요.

        3. 관련 검사:
           • 이 질환과 관련된 특정 검사를 추천해주세요. 분석의 'lab_work' 섹션에 언급된 검사를 우선으로 해주세요.
           • 이 검사들이 어떻게 질환을 모니터링하거나 진단하는 데 도움이 되는지 설명해주세요.

        4. 생활 습관 권장 사항:
           • 이 질환을 관리하거나 예방하는 데 도움이 될 수 있는 생활 습관 변화를 제안해주세요. 분석의 'lifestyle' 섹션에 언급된 내용을 중심으로 해주세요.
           • 이러한 변화가 사용자의 가족력과 위험 요인에 어떻게 특별히 관련되는지 설명해주세요.

        응답은 정보를 제공하고, 사용자의 가족력에 맞춰 개인화되어야 하며, 웹페이지에 표시하기에 적합하도록 간결해야 합니다.
        """
    else:
        prompt = f"""
        Based on the following health analysis:
        {json.dumps(analysis, indent=2)}

        Provide detailed information about the condition: {condition}

        Please structure your response in the following format:

        1. Risk Assessment:
           • Provide a risk level (Low, Medium, or High) for the user developing this condition based on their family history.
           • Briefly explain the reasoning behind this risk assessment.

        2. Family History and Inheritance:
           • Focus on how this condition appears in the user's family tree based on the provided 'inheritance_patterns'.
           • Explain the specific inheritance pattern for this condition in the user's family.
           • Discuss the user's risk of inheriting or developing this condition based on their family history.

        3. Relevant Lab Work:
           • Recommend specific lab tests related to this condition, prioritizing those mentioned in the 'lab_work' section of the analysis.
           • Explain how these tests can help monitor or diagnose the condition.

        4. Lifestyle Recommendations:
           • Suggest lifestyle changes that could help manage or prevent this condition, focusing on those mentioned in the 'lifestyle' section of the analysis.
           • Explain how these changes specifically relate to the user's family history and risk factors.

        Your response should be informative, personalized to the user's family history, and concise, suitable for display on a webpage.
        """

    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response = message.content[0].text
        print("LLM Response:", response)  # Debug print

        # Process the response to extract sections
        sections = {
            'Risk Assessment': [],
            'Family History and Inheritance': [],
            'Relevant Lab Work': [],
            'Lifestyle Recommendations': []
        }
        current_section = None
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('1. 위험도 평가:') or line.startswith('1. Risk Assessment:'):
                current_section = 'Risk Assessment'
            elif line.startswith('2. 가족력 및 유전:') or line.startswith('2. Family History and Inheritance:'):
                current_section = 'Family History and Inheritance'
            elif line.startswith('3. 관련 검사:') or line.startswith('3. Relevant Lab Work:'):
                current_section = 'Relevant Lab Work'
            elif line.startswith('4. 생활 습관 권장 사항:') or line.startswith('4. Lifestyle Recommendations:'):
                current_section = 'Lifestyle Recommendations'
            elif (line.startswith('•') or line.startswith('- ')) and current_section:
                sections[current_section].append(line[1:].strip())

        # Extract risk level from the Risk Assessment section
        risk_level = 'Unknown'
        if sections['Risk Assessment']:
            risk_text = sections['Risk Assessment'][0].lower()
            if '낮음' in risk_text or '낮은' in risk_text or 'low' in risk_text:
                risk_level = 'Low'
            elif '중간' in risk_text or '보통' in risk_text or 'medium' in risk_text:
                risk_level = 'Medium'
            elif '높음' in risk_text or '높은' in risk_text or 'high' in risk_text:
                risk_level = 'High'

        print("Processed Sections:", sections)  # Debug print
        return jsonify({'sections': sections, 'risk_level': risk_level})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)