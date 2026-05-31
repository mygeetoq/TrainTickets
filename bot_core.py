import json
import random
import nltk
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

# Ensure NLTK data is downloaded
nltk.download('punkt', quiet=True)

class TrainTicketBot:
    def __init__(self, intents_path='intents.json', dialogues_path='dialogues.txt', products_path='products.json'):
        self.load_data(intents_path, dialogues_path, products_path)
        self.prepare_ml()
        self.prepare_dialogues()
        self.message_count = 0 # To track dialogue length for ad injection

    def load_data(self, intents_path, dialogues_path, products_path):
        with open(intents_path, 'r', encoding='utf-8') as f:
            self.intents = json.load(f)
        
        with open(products_path, 'r', encoding='utf-8') as f:
            self.products = json.load(f)
            
        if os.path.exists(dialogues_path):
            with open(dialogues_path, 'r', encoding='utf-8') as f:
                self.dialogues_raw = f.read()
        else:
            self.dialogues_raw = ""

    def clear_phrase(self, text):
        text = text.lower()
        alphabet = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяabcdefghijklmnopqrstuvwxyz0123456789 '
        result = ''.join(c for c in text if c in alphabet)
        return result.strip()

    def prepare_ml(self):
        X_text = []
        y = []
        for intent, data in self.intents.items():
            for pattern in data['patterns']:
                X_text.append(self.clear_phrase(pattern))
                y.append(intent)
        
        self.vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(3, 3))
        X = self.vectorizer.fit_transform(X_text)
        self.clf = LinearSVC()
        self.clf.fit(X, y)

    def prepare_dialogues(self):
        self.dialogues_structured = {}
        if not self.dialogues_raw:
            return
            
        dialogues_str = self.dialogues_raw.split('\n\n')
        for d_str in dialogues_str:
            lines = d_str.strip().split('\n')
            if len(lines) >= 2:
                q = self.clear_phrase(lines[0][2:] if lines[0].startswith('- ') else lines[0])
                a = lines[1][2:] if lines[1].startswith('- ') else lines[1]
                
                if q:
                    words = set(q.split())
                    for word in words:
                        if word not in self.dialogues_structured:
                            self.dialogues_structured[word] = []
                        self.dialogues_structured[word].append((q, a))

    def get_intent_ml(self, text):
        cleaned = self.clear_phrase(text)
        if not cleaned:
            return None
        
        vector = self.vectorizer.transform([cleaned])
        scores = self.clf.decision_function(vector)[0]
        # Using a threshold to avoid false positives for unrelated topics
        if hasattr(scores, "__len__"):
            max_score = max(scores)
        else:
            max_score = scores
            
        if max_score < 0.2: 
             return None
             
        intent = self.clf.predict(vector)[0]
        return intent

    def get_answer_from_dialogues(self, text):
        cleaned = self.clear_phrase(text)
        words = set(cleaned.split())
        candidates = []
        for word in words:
            if word in self.dialogues_structured:
                candidates.extend(self.dialogues_structured[word])
        
        candidates = list(set(candidates))
        best_answer = None
        min_dist = 1.0
        
        for q, a in candidates:
            if abs(len(cleaned) - len(q)) / max(len(q), 1) < 0.3:
                dist = nltk.edit_distance(cleaned, q) / max(len(q), 1)
                if dist < min_dist and dist < 0.3:
                    min_dist = dist
                    best_answer = a
        
        return best_answer

    def get_ad(self, smooth_transition=True):
        product = random.choice(self.products)
        if smooth_transition:
            transitions = [
                "Кстати, раз уж мы заговорили, возможно вам будет интересно:",
                "Пока вы думаете о поездке, посмотрите наше предложение:",
                "Чтобы ваше путешествие стало еще комфортнее, рекомендуем:",
                "Интересный факт: многие наши пассажиры также выбирают:"
            ]
            prefix = random.choice(transitions)
            return f"\n\n{prefix}\n💎 {product['name']}: {product['description']}\n🔗 {product['link']}"
        else:
            return f"\n\n📢 Рекомендуем: {product['name']}\n{product['description']}\nПодробнее: {product['link']}"

    def get_response(self, text):
        self.message_count += 1
        response = ""
        
        # 1. Try ML Intent (Covers small talk and ticket topics)
        intent = self.get_intent_ml(text)
        if intent and intent in self.intents:
            response = random.choice(self.intents[intent]['responses'])
        
        # 2. Try Dialogues dataset if no intent found
        if not response:
            response = self.get_answer_from_dialogues(text)
            
        # 3. Default fallback
        if not response:
            response = "Интересная мысль! Я как раз думал о том, как здорово путешествовать на поезде. " \
                       "Могу помочь вам с билетами или просто поболтать о поездках."
            
        # 4. AD INJECTION LOGIC (Smooth transition)
        # Inject ad every 3 messages or if the topic is ticket-related
        is_ticket_topic = intent in ["buy_ticket", "price", "schedule"]
        if self.message_count % 3 == 0 or is_ticket_topic:
            # If it's a ticket topic, 50% chance. If it's every 3rd message, 100% chance.
            if not is_ticket_topic or random.random() < 0.5:
                response += self.get_ad(smooth_transition=True)
                
        return response

if __name__ == "__main__":
    bot = TrainTicketBot()
    print("Бот запущен. Введите сообщение (или 'exit' для выхода):")
    while True:
        user_input = input("> ")
        if user_input.lower() == 'exit':
            break
        print(bot.get_response(user_input))
