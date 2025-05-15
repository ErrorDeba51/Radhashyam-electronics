# radhashyam/chatbot/views.py
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import requests


class ApplianceChatbot:
    PRODUCT_CATEGORIES = [
        'TV', 'Fridge', 'AC', 'Washing Machine', 'Room Heater'
    ]

    def __init__(self):
        self.fallbacks = {
            'hi': "Hello! How can I assist you today?",
            'hello': "Hello! How can I assist you today?",
            'hey': "Hello! How can I assist you today?",
            'number': "Call us at 1234567890 or visit Labpur store",

            'help': "I can help you with product information, pricing, availability, features, specifications, warranty, return policy, delivery options, and payment methods.",
            'product': "We have a wide range of appliances including TVs, refrigerators, air conditioners, washing machines, and room heaters.",
            'price': "Prices vary by model and brand. Please specify the product you're interested in.",
            'availability': "We have stock available for most products. Please specify the product you're interested in.",
            'features': "Please specify the product you're interested in for detailed features.",
            'specs': "Please specify the product you're interested in for detailed specifications.",

            'warranty': "Most products come with a 1-year standard warranty. Please check the specific product for details.",
            'return': "We have a 7-day return policy for defective products. Please keep the original packaging.",
            'delivery': "Delivery within Birbhum district in 2-3 days",
            'payment': "We accept cash on delivery, UPI, and credit/debit cards",

            'contact': "Call us at 1234567890 or visit Labpur store",
            'hours': "Open daily 9AM-9PM,  except Thursdays",
            'location': "We are located in Labpur, West Bengal. Visit us for more information.",
            'tv': "we have a wide range of TVs including LED, OLED, and Smart TVs. Brands include Samsung, LG, Sony, and more.",
            'fridge': "We offer a variety of refrigerators, including single door, double door, and side-by-side models. Brands include Whirlpool, LG, Samsung, and more.",
            'ac': "We have a range of air conditioners, including window and split ACs. Brands include LG, Daikin, and Voltas.",
            'washing machine': "We offer both front-load and top-load washing machines. Brands include LG, Samsung, and Whirlpool.",
            'room heater': "We have various types of room heaters, including oil-filled and fan heaters. Brands include Bajaj, Usha, and Havells.",
            'appliance': "We have a wide range of appliances including TVs, refrigerators, air conditioners, washing machines, and room heaters. Brands include LG, Samsung, Whirlpool, and more.",
        }

    def get_response(self, query):
        try:

            response = requests.post(
                "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
                headers={"Authorization": f"Bearer {settings.HF_API_KEY}"},
                json={"inputs": query}
            )

            if response.status_code == 200:
                return response.json()['generated_text']
            return self._handle_fallback(query)

        except Exception as e:
            return self._handle_fallback(query)

    def _handle_fallback(self, query):
        query_lower = query.lower()
        for keyword in self.fallbacks:
            if keyword in query_lower:
                return self.fallbacks[keyword]
        return self.fallbacks['contact']


# @csrf_exempt
@require_POST
def chatbot_view(request):
    if request.method == 'POST':
        try:
            query = request.POST.get('query', '').strip()
            if not query:
                return JsonResponse({'response': 'Please enter a question about appliances'})

            chatbot = ApplianceChatbot()
            response = chatbot.get_response(query)
            return JsonResponse({'response': response})

        except Exception as e:
            return JsonResponse({
                'response': 'Service unavailable. Please visit our store or call 9876543210.'
            }, status=503)

    return render(request, 'chatbot/chatbot.html')
