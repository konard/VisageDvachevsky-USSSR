"""
Enhanced AI Service with semantic search and fact generation
"""
import os
import random
import logging
from typing import List, Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)


class EnhancedAIService:
    """Enhanced AI service with sentence transformers for semantic search"""

    def __init__(self, config=None):
        """Initialize AI service with optional configuration"""
        self.config = config
        self.model = None
        self.use_transformers = config.get('USE_HUGGINGFACE', True) if config else True

        # Initialize model lazily
        if self.use_transformers:
            self._init_model()

        # Predefined interesting facts database
        self.facts_database = {
            1: [  # Lenin
                "Ленин был заядлым шахматистом и часто играл с видными революционерами.",
                "Настоящая фамилия Ленина - Ульянов. Псевдоним 'Ленин' он взял от реки Лена.",
                "Ленин владел несколькими иностранными языками, включая немецкий, французский и английский.",
                "После покушения в 1918 году в теле Ленина осталось две пули, которые врачи не решились извлечь.",
                "Ленин был автором более 50 томов сочинений по философии, экономике и политике.",
                "Ленин страдал от мигреней и бессонницы, что усугублялось напряжённой работой.",
                "Мавзолей Ленина был построен вопреки его завещанию быть похороненным рядом с матерью.",
                "Ленин очень любил кошек и часто проводил время в общении с ними."
            ],
            2: [  # Stalin
                "Сталин был семинаристом и изучал богословие в Тифлисской духовной семинарии.",
                "Настоящая фамилия Сталина - Джугашвили. 'Сталин' означает 'стальной человек'.",
                "Сталин писал стихи в молодости на грузинском языке, некоторые были опубликованы.",
                "У Сталина была повреждена левая рука из-за детской травмы, что освободило его от службы в царской армии.",
                "Сталин курил трубку и обычно работал по ночам, засыпая под утро.",
                "Рост Сталина составлял всего 165 см, что он компенсировал ношением обуви на высоких каблуках.",
                "Сталин был номинирован на Нобелевскую премию мира дважды - в 1945 и 1948 годах.",
                "Сталин обладал феноменальной памятью и мог цитировать целые страницы прочитанных книг."
            ],
            3: [  # Khrushchev
                "Хрущёв был единственным советским лидером, не имевшим высшего образования.",
                "Известен своим поступком на заседании ООН в 1960 году, когда стучал ботинком по столу.",
                "Хрущёв любил кукурузу и пытался внедрить её выращивание по всему СССР.",
                "При Хрущёве началось массовое жилищное строительство, появились знаменитые 'хрущёвки'.",
                "Хрущёв первым из советских лидеров посетил США в 1959 году.",
                "Хрущёв инициировал освоение целинных земель в Казахстане и Сибири.",
                "При Хрущёве был запущен первый искусственный спутник Земли и совершён первый полёт человека в космос.",
                "Хрущёв лично курировал строительство московского метрополитена."
            ],
            4: [  # Brezhnev
                "Брежнев был страстным коллекционером автомобилей, в его коллекции было более 50 машин.",
                "Брежнев получил звание Маршала Советского Союза, несмотря на отсутствие крупных военных заслуг.",
                "За время правления Брежнев получил более 200 наград, включая 5 звёзд Героя.",
                "Брежнев любил охоту и часто проводил время на охотничьих заказниках.",
                "Период правления Брежнева часто называют 'золотым веком' за стабильность и предсказуемость.",
                "Брежнев был заядлым курильщиком и выкуривал до трёх пачек сигарет в день.",
                "При Брежневе СССР достиг военного паритета с США и стал настоящей сверхдержавой.",
                "Брежнев страдал от множества заболеваний в последние годы жизни, но продолжал руководить страной."
            ],
            5: [  # Andropov
                "Андропов возглавлял КГБ в течение 15 лет перед тем, как стать генсеком.",
                "Андропов свободно говорил на нескольких языках и любил джаз.",
                "При Андропове началась кампания по укреплению трудовой дисциплины, включая рейды в магазинах и кинотеатрах в рабочее время.",
                "Андропов был одним из самых образованных советских лидеров, интересовался литературой и искусством.",
                "Правление Андропова было недолгим - всего 15 месяцев из-за болезни.",
                "Андропов был поклонником западной музыки и собирал коллекцию джазовых пластинок.",
                "Андропов начал подготовку экономических реформ, которые позже продолжил Горбачёв.",
                "Андропов был единственным руководителем СССР, кто лично жил в обычной квартире, а не в особняке."
            ],
            6: [  # Chernenko
                "Черненко был самым возрастным лидером, пришедшим к власти в СССР - ему было 72 года.",
                "Черненко страдал от эмфиземы лёгких и часто появлялся на публике с кислородной маской за кулисами.",
                "Правление Черненко продолжалось всего 13 месяцев - самое короткое в истории СССР.",
                "Черненко начинал карьеру как пограничник на советско-китайской границе.",
                "При Черненко были предприняты попытки вернуться к политике Брежнева.",
                "Черненко был личным другом Брежнева и курировал идеологическую работу КПСС.",
                "Во время правления Черненко здоровье лидера было настолько плохим, что он редко появлялся публично.",
                "Черненко был последним советским лидером старой гвардии перед приходом Горбачёва."
            ],
            7: [  # Gorbachev
                "Горбачёв был единственным президентом СССР и последним генеральным секретарём КПСС.",
                "Горбачёв получил Нобелевскую премию мира в 1990 году за прекращение холодной войны.",
                "Родимое пятно на лбу Горбачёва стало его узнаваемой чертой по всему миру.",
                "Горбачёв окончил юридический факультет МГУ - редкость для советских лидеров.",
                "После распада СССР Горбачёв снимался в рекламе и занимался общественной деятельностью.",
                "Политика гласности Горбачёва привела к невиданной ранее свободе слова в СССР.",
                "Горбачёв был первым советским лидером, чья жена (Раиса Горбачёва) играла заметную публичную роль.",
                "Горбачёв был единственным советским лидером, кто добровольно ушёл с поста."
            ]
        }

    def _init_model(self):
        """Initialize sentence transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            model_name = self.config.get('AI_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2') if self.config else 'sentence-transformers/all-MiniLM-L6-v2'
            cache_dir = self.config.get('AI_CACHE_DIR', './cache/models') if self.config else './cache/models'

            # Create cache directory if it doesn't exist
            os.makedirs(cache_dir, exist_ok=True)

            logger.info(f"Loading sentence transformer model: {model_name}")
            self.model = SentenceTransformer(model_name, cache_folder=cache_dir)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load sentence transformer model: {e}. Using fallback search.")
            self.model = None
            self.use_transformers = False

    def generate_facts(self, leader: Dict, count: int = 3) -> List[str]:
        """
        Generate interesting facts about a leader

        Args:
            leader: Dictionary containing leader information
            count: Number of facts to return

        Returns:
            List of facts about the leader
        """
        leader_id = leader.get('id')

        if leader_id in self.facts_database:
            # Return random selection of facts
            facts = self.facts_database[leader_id].copy()
            random.shuffle(facts)
            return facts[:count]

        # Fallback to basic facts from database
        basic_facts = [
            f"{leader['name_ru']} родился в {leader['birth_year']} году в {leader['birth_place']}.",
            f"Занимал должность: {leader['position']}.",
            leader['achievements']
        ]

        return basic_facts[:count]

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using sentence transformer

        Args:
            text: Text to encode

        Returns:
            Embedding vector as list of floats, or None if model not available
        """
        if not self.model or not self.use_transformers:
            return None

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def semantic_search(self, query: str, leaders: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        Perform semantic search on leaders using embeddings

        Args:
            query: Search query
            leaders: List of all leaders
            top_k: Number of results to return

        Returns:
            List of matching leaders sorted by relevance
        """
        if not self.model or not self.use_transformers:
            # Fallback to simple keyword matching
            return self._simple_search(query, leaders)

        try:
            # Generate query embedding
            query_embedding = self.model.encode(query, convert_to_numpy=True)

            # Calculate similarity scores
            results = []
            for leader in leaders:
                # Create searchable text
                searchable_text = f"{leader['name_ru']} {leader['name_en']} {leader.get('position', '')} {leader.get('achievements', '')}"

                # Generate embedding for leader
                leader_embedding = self.model.encode(searchable_text, convert_to_numpy=True)

                # Calculate cosine similarity
                similarity = np.dot(query_embedding, leader_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(leader_embedding)
                )

                results.append((leader, float(similarity)))

            # Sort by similarity and return top k
            results.sort(key=lambda x: x[1], reverse=True)
            return [leader for leader, score in results[:top_k] if score > 0.3]  # Threshold of 0.3

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return self._simple_search(query, leaders)

    def _simple_search(self, query: str, leaders: List[Dict]) -> List[Dict]:
        """
        Simple keyword-based search fallback

        Args:
            query: Search query
            leaders: List of all leaders

        Returns:
            List of matching leaders
        """
        query_lower = query.lower()
        results = []

        for leader in leaders:
            searchable_text = f"{leader['name_ru']} {leader['name_en']} {leader.get('position', '')} {leader.get('achievements', '')}".lower()

            if query_lower in searchable_text:
                results.append(leader)

        return results

    def get_recommendations(self, leader: Dict, all_leaders: List[Dict], count: int = 3) -> List[Dict]:
        """
        Get similar leaders based on semantic similarity

        Args:
            leader: The leader to find similar ones for
            all_leaders: List of all leaders
            count: Number of recommendations to return

        Returns:
            List of similar leaders
        """
        if not self.model or not self.use_transformers:
            # Fallback: return random leaders
            others = [l for l in all_leaders if l['id'] != leader['id']]
            random.shuffle(others)
            return others[:count]

        try:
            # Create text for current leader
            leader_text = f"{leader['name_ru']} {leader.get('position', '')} {leader.get('achievements', '')}"
            leader_embedding = self.model.encode(leader_text, convert_to_numpy=True)

            # Calculate similarities
            similarities = []
            for other in all_leaders:
                if other['id'] == leader['id']:
                    continue

                other_text = f"{other['name_ru']} {other.get('position', '')} {other.get('achievements', '')}"
                other_embedding = self.model.encode(other_text, convert_to_numpy=True)

                similarity = np.dot(leader_embedding, other_embedding) / (
                    np.linalg.norm(leader_embedding) * np.linalg.norm(other_embedding)
                )

                similarities.append((other, float(similarity)))

            # Sort and return top matches
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [leader for leader, score in similarities[:count]]

        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            others = [l for l in all_leaders if l['id'] != leader['id']]
            random.shuffle(others)
            return others[:count]
