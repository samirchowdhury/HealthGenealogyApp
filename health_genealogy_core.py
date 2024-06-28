import uuid
import json
import os
import anthropic
from translations import TRANSLATIONS

class Person:
    def __init__(self, formal_name=None, familiar_name=None):
        self.id = str(uuid.uuid4())
        self.formal_name = formal_name
        self.familiar_name = familiar_name
        self.health_data = {}
        self.relationships = {}

class HealthGenealogy:
    def __init__(self, language='en'):
        self.people = {}
        self.root_person = None
        self.secret_keys = {}  # For demonstration purposes
        self.language = language
        self.translations = TRANSLATIONS[language]

    def add_person(self, formal_name=None, familiar_name=None):
        person = Person(formal_name, familiar_name)
        self.people[person.id] = person
        if self.root_person is None:
            self.root_person = person.id
        return person

    def set_relationship(self, person1_id, relationship, person2_id):
        allowed_relationships = ['mother', 'father', 'sibling']
        if relationship not in allowed_relationships:
            raise ValueError(f"Relationship must be one of {allowed_relationships}")
        self.people[person1_id].relationships[relationship] = person2_id

    def join_as_sibling(self, secret_key, formal_name=None, familiar_name=None):
        if secret_key not in self.secret_keys:
            raise ValueError("Invalid secret key")
        
        existing_person_id = self.secret_keys[secret_key]
        existing_person = self.people[existing_person_id]
        
        new_person = self.add_person(formal_name, familiar_name)
        
        # Set sibling relationship
        self.set_relationship(new_person.id, 'sibling', existing_person.id)
        self.set_relationship(existing_person.id, 'sibling', new_person.id)
        
        # Copy parent relationships
        for rel in ['mother', 'father']:
            if rel in existing_person.relationships:
                self.set_relationship(new_person.id, rel, existing_person.relationships[rel])
        
        return new_person.id

    def populate_health_data(self):
        for person in self.people.values():
            name_display = person.familiar_name or person.formal_name
            print(self.translations['enter_health_data'].format(name_display))
            person.health_data['conditions'] = input(self.translations['enter_conditions']).split(',')
            person.health_data['allergies'] = input(self.translations['enter_allergies']).split(',')

    def traverse_and_dump(self):
        def person_to_dict(person):
            return {
                "id": person.id,
                "formal_name": person.formal_name,
                "familiar_name": person.familiar_name,
                "health_data": person.health_data,
                "relationships": person.relationships
            }

        return json.dumps({p.id: person_to_dict(p) for p in self.people.values()}, indent=2)

    def save_to_json(self, filename):
        with open(filename, 'w') as f:
            f.write(self.traverse_and_dump())

    def load_from_json(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)

        self.people.clear()
        for person_id, person_data in data.items():
            person = Person(person_data['formal_name'], person_data['familiar_name'])
            person.id = person_id
            person.health_data = person_data['health_data']
            person.relationships = person_data['relationships']
            self.people[person_id] = person

        # Set root_person to the first person without parents
        for person in self.people.values():
            if 'mother' not in person.relationships and 'father' not in person.relationships:
                self.root_person = person.id
                break

    def generate_mermaid_diagram(self):
        mermaid_code = ["graph TD;"]
        for person in self.people.values():
            label = person.familiar_name or person.formal_name or person.id
            mermaid_code.append(f'    {person.id}["{label}"];')

        for person in self.people.values():
            for relationship, related_id in person.relationships.items():
                mermaid_code.append(f"    {related_id} --> |{relationship}| {person.id};")

        return "\n".join(mermaid_code)

def llm_analysis(data, language='en'):
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    prompts = {
        'en': """
    You are a health analysis AI. Given the following family health history data, please provide:
    1. Key hereditary conditions to watch for
    2. Recommended lab work
    3. Lifestyle recommendations
    4. Inheritance patterns for key conditions

    Family Health History Data:
    {data}

    Please format your response as a JSON object with the following structure:
    {{
        "conditions": ["condition1", "condition2", ...],
        "lab_work": ["test1", "test2", ...],
        "lifestyle": ["recommendation1", "recommendation2", ...],
        "inheritance_patterns": [
            {{
                "condition": "condition name",
                "pattern": "brief description of inheritance pattern",
                "affected_members": ["family member 1", "family member 2", ...]
            }},
            ...
        ]
    }}
    Limit the conditions, lab_work, and lifestyle lists to 5-7 items each, focusing on the most important points.
    For the inheritance_patterns, provide 3-5 entries for the most significant hereditary conditions.
    When referring to family members in the affected_members list, use their relationship to the central individual (e.g., "mother", "paternal grandfather", "sister") rather than names.
    """,
        'ko': """
    당신은 건강 분석 AI입니다. 다음의 가족 건강 이력 데이터를 바탕으로 다음 사항을 제공해 주세요:
    1. 주의해야 할 주요 유전적 질환
    2. 권장되는 검사
    3. 생활 습관 개선 권고사항
    4. 주요 질환의 유전 패턴

    가족 건강 이력 데이터:
    {data}

    답변을 다음 구조의 JSON 객체 형식으로 작성해 주세요:
    {{
        "conditions": ["질환1", "질환2", ...],
        "lab_work": ["검사1", "검사2", ...],
        "lifestyle": ["권고사항1", "권고사항2", ...],
        "inheritance_patterns": [
            {{
                "condition": "질환 이름",
                "pattern": "유전 패턴에 대한 간단한 설명",
                "affected_members": ["가족 구성원 1", "가족 구성원 2", ...]
            }},
            ...
        ]
    }}
    conditions, lab_work, lifestyle 리스트는 각각 5-7개 항목으로 제한하고, 가장 중요한 사항에 집중해 주세요.
    inheritance_patterns의 경우, 가장 중요한 유전적 질환 3-5개에 대해 정보를 제공해 주세요.
    affected_members 리스트에서 가족 구성원을 언급할 때는 이름 대신 중심 인물과의 관계(예: "어머니", "친할아버지", "여동생")를 사용해 주세요.
    """
    }

    prompt = prompts.get(language, prompts[language]).format(data=data)


    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"An error occurred while analyzing the health data: {str(e)}"

def answer_question_with_context(data, query, language='en'):
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""
    You are a health analysis AI. Given the following family health history data, please provide an answer to the user's question.
    Family health history data:
    {data}
    user query: {query}

    please respond in language {language}
    """

    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"An error occurred while analyzing the health data: {str(e)}"
