"""
AI service for generating facts and content
"""
from typing import List, Optional
import logging

from app.models.leader import Leader
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered features"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL

    async def generate_facts(self, leader: Leader) -> List[str]:
        """Generate interesting facts about a leader using AI"""

        # If OpenAI API key is not configured, return mock facts
        if not self.api_key:
            return self._get_mock_facts(leader)

        try:
            # Import OpenAI only if API key is available
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            prompt = f"""
            Generate 5 interesting, lesser-known historical facts about {leader.name_en} ({leader.name_ru}).

            Context:
            - Born: {leader.birth_year} in {leader.birth_place}
            - Died: {leader.death_year or 'Still alive'} {f'in {leader.death_place}' if leader.death_place else ''}
            - Position: {leader.position}
            - Achievements: {leader.achievements}

            Requirements:
            - Each fact should be concise (1-2 sentences)
            - Focus on lesser-known details
            - Be historically accurate
            - Write in Russian language
            - Return only the facts, one per line
            """

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a historian specializing in USSR history. Provide accurate, interesting historical facts.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=0.7,
            )

            facts_text = response.choices[0].message.content.strip()
            facts = [fact.strip() for fact in facts_text.split("\n") if fact.strip()]

            # Return first 5 facts
            return facts[:5]

        except Exception as e:
            logger.error(f"Error generating facts with OpenAI: {e}")
            return self._get_mock_facts(leader)

    def _get_mock_facts(self, leader: Leader) -> List[str]:
        """Get mock facts when AI is not available"""

        # Mock facts for each leader (in Russian)
        mock_facts_by_name = {
            "Vladimir Ilyich Lenin": [
                "Ленин был заядлым шахматистом и часто играл в свободное время.",
                "Настоящая фамилия Ленина - Ульянов, псевдоним появился в 1901 году.",
                "Ленин свободно владел несколькими иностранными языками, включая немецкий и французский.",
                "В молодости Ленин был отличным пловцом и любил охоту.",
                "Ленин написал более 50 томов работ по философии, экономике и политике.",
            ],
            "Joseph Stalin": [
                "Сталин начинал свою карьеру как поэт и публиковался в грузинских журналах.",
                "Настоящее имя Сталина - Иосиф Джугашвили.",
                "Сталин получил духовное образование в Тбилисской семинарии.",
                "Сталин любил смотреть фильмы и имел собственный кинотеатр в Кремле.",
                "Сталин был заядлым курильщиком трубки.",
            ],
            "Nikita Khrushchev": [
                "Хрущёв был единственным советским лидером, работавшим шахтёром в молодости.",
                "Хрущёв известен своим выступлением на ООН, где стучал ботинком по трибуне.",
                "При Хрущёве началось массовое строительство жилья ('хрущёвки').",
                "Хрущёв любил кукурузу и пытался внедрить её выращивание по всему СССР.",
                "Хрущёв был первым советским лидером, посетившим США.",
            ],
            "Leonid Brezhnev": [
                "Брежнев был страстным коллекционером автомобилей.",
                "Брежнев получил более 200 наград и медалей за свою жизнь.",
                "Брежнев любил охоту и часто проводил время в охотничьих угодьях.",
                "При Брежневе СССР достиг военного паритета с США.",
                "Брежнев писал мемуары, за которые получил Ленинскую премию по литературе.",
            ],
            "Yuri Andropov": [
                "Андропов был главой КГБ до того, как стать генсеком.",
                "Андропов свободно владел несколькими иностранными языками.",
                "Андропов любил джаз и имел большую коллекцию записей.",
                "Андропов начал борьбу с коррупцией и пьянством в СССР.",
                "Андропов был серьёзно болен большую часть своего правления.",
            ],
            "Konstantin Chernenko": [
                "Черненко был самым пожилым лидером СССР при вступлении в должность (72 года).",
                "Черненко страдал от серьёзных проблем со здоровьем всё время своего правления.",
                "Черненко работал пограничником в молодости.",
                "Черненко был близким соратником Брежнева.",
                "Черненко правил всего 13 месяцев - самый короткий срок среди советских лидеров.",
            ],
            "Mikhail Gorbachev": [
                "Горбачёв был единственным советским лидером, получившим Нобелевскую премию мира.",
                "Горбачёв имел родимое пятно на лбу, ставшее его характерной чертой.",
                "Горбачёв получил юридическое образование в МГУ.",
                "Горбачёв был первым и последним президентом СССР.",
                "Горбачёв снялся в рекламе Pizza Hut после распада СССР.",
            ],
        }

        facts = mock_facts_by_name.get(
            leader.name_en,
            [
                f"{leader.name_ru} был выдающейся личностью в истории СССР.",
                f"Родился в {leader.birth_year} году в {leader.birth_place}.",
                f"{leader.position} сыграл важную роль в развитии страны.",
                f"Достижения: {leader.achievements[:100]}...",
                f"Исторический период правления оставил значительный след в истории.",
            ],
        )

        return facts

    async def semantic_search(self, query: str, leaders: List[Leader]) -> List[Leader]:
        """Perform semantic search on leaders"""
        # Simple keyword-based search for now
        # TODO: Implement vector embeddings for true semantic search
        query_lower = query.lower()
        results = []

        for leader in leaders:
            if (
                query_lower in leader.name_ru.lower()
                or query_lower in leader.name_en.lower()
                or query_lower in leader.position.lower()
                or query_lower in leader.achievements.lower()
            ):
                results.append(leader)

        return results
