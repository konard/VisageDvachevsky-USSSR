"""
AI Service module for generating facts and semantic search
"""
import os
import random
from typing import List, Dict

class AIService:
    """AI service for generating facts and semantic search"""

    def __init__(self):
        """Initialize AI service"""
        # Predefined interesting facts about each leader
        self.facts_database = {
            1: [  # Lenin
                "Ленин был заядлым шахматистом и часто играл с видными революционерами.",
                "Настоящая фамилия Ленина - Ульянов. Псевдоним 'Ленин' он взял от реки Лена.",
                "Ленин владел несколькими иностранными языками, включая немецкий, французский и английский.",
                "После покушения в 1918 году в теле Ленина осталось две пули, которые врачи не решились извлечь.",
                "Ленин был автором более 50 томов сочинений по философии, экономике и политике."
            ],
            2: [  # Stalin
                "Сталин был семинаристом и изучал богословие в Тифлисской духовной семинарии.",
                "Настоящая фамилия Сталина - Джугашвили. 'Сталин' означает 'стальной человек'.",
                "Сталин писал стихи в молодости на грузинском языке, некоторые были опубликованы.",
                "У Сталина была повреждена левая рука из-за детской травмы, что освободило его от службы в царской армии.",
                "Сталин курил трубку и обычно работал по ночам, засыпая под утро."
            ],
            3: [  # Khrushchev
                "Хрущёв был единственным советским лидером, не имевшим высшего образования.",
                "Известен своим поступком на заседании ООН в 1960 году, когда стучал ботинком по столу.",
                "Хрущёв любил кукурузу и пытался внедрить её выращивание по всему СССР.",
                "При Хрущёве началось массовое жилищное строительство, появились знаменитые 'хрущёвки'.",
                "Хрущёв первым из советских лидеров посетил США в 1959 году."
            ],
            4: [  # Brezhnev
                "Брежнев был страстным коллекционером автомобилей, в его коллекции было более 50 машин.",
                "Брежнев получил звание Маршала Советского Союза, несмотря на отсутствие крупных военных заслуг.",
                "За время правления Брежнев получил более 200 наград, включая 5 звёзд Героя.",
                "Брежнев любил охоту и часто проводил время на охотничьих заказниках.",
                "Период правления Брежнева часто называют 'золотым веком' за стабильность и предсказуемость."
            ],
            5: [  # Andropov
                "Андропов возглавлял КГБ в течение 15 лет перед тем, как стать генсеком.",
                "Андропов свободно говорил на нескольких языках и любил джаз.",
                "При Андропове началась кампания по укреплению трудовой дисциплины, включая рейды в магазинах и кинотеатрах в рабочее время.",
                "Андропов был одним из самых образованных советских лидеров, интересовался литературой и искусством.",
                "Правление Андропова было недолгим - всего 15 месяцев из-за болезни."
            ],
            6: [  # Chernenko
                "Черненко был самым возрастным лидером, пришедшим к власти в СССР - ему было 72 года.",
                "Черненко страдал от эмфиземы лёгких и часто появлялся на публике с кислородной маской за кулисами.",
                "Правление Черненко продолжалось всего 13 месяцев - самое короткое в истории СССР.",
                "Черненко начинал карьеру как пограничник на советско-китайской границе.",
                "При Черненко были предприняты попытки вернуться к политике Брежнева."
            ],
            7: [  # Gorbachev
                "Горбачёв был единственным президентом СССР и последним генеральным секретарём КПСС.",
                "Горбачёв получил Нобелевскую премию мира в 1990 году за прекращение холодной войны.",
                "Родимое пятно на лбу Горбачёва стало его узнаваемой чертой по всему миру.",
                "Горбачёв окончил юридический факультет МГУ - редкость для советских лидеров.",
                "После распада СССР Горбачёв снимался в рекламе и занимался общественной деятельностью."
            ]
        }

    def generate_facts(self, leader: Dict) -> List[str]:
        """
        Generate interesting facts about a leader

        Args:
            leader: Dictionary containing leader information

        Returns:
            List of facts about the leader
        """
        leader_id = leader.get('id')
        if leader_id in self.facts_database:
            # Return random selection of facts
            facts = self.facts_database[leader_id].copy()
            random.shuffle(facts)
            return facts[:3]  # Return 3 random facts

        # Fallback to basic facts from database
        return [
            f"{leader['name_ru']} родился в {leader['birth_year']} году в {leader['birth_place']}.",
            f"Занимал должность: {leader['position']}.",
            leader['achievements']
        ]

    def semantic_search(self, query: str, leaders: List[Dict]) -> List[Dict]:
        """
        Perform semantic search on leaders

        Args:
            query: Search query
            leaders: List of all leaders

        Returns:
            List of matching leaders
        """
        query_lower = query.lower()
        results = []

        for leader in leaders:
            # Simple keyword matching (can be enhanced with embeddings later)
            searchable_text = f"{leader['name_ru']} {leader['name_en']} {leader['position']} {leader['achievements']}".lower()

            if query_lower in searchable_text:
                results.append(leader)

        return results

    def get_ai_response(self, prompt: str, leader: Dict = None) -> str:
        """
        Get AI-generated response (placeholder for future LLM integration)

        Args:
            prompt: The prompt for the AI
            leader: Optional leader context

        Returns:
            AI-generated response
        """
        # Placeholder for OpenAI API or local LLM integration
        # This can be implemented with:
        # - OpenAI API
        # - Anthropic Claude API
        # - Local models via Ollama/LM Studio
        # - HuggingFace transformers

        return "AI integration placeholder - connect your LLM API here"
