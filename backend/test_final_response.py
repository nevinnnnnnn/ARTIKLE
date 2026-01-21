from app.services.chat_service import chat_service
import time

query = 'What is AI?'
print(f'Question: {query}')
print()

context = chat_service.retrieve_context(1, query)
print(f'Context chunks: {len(context)}')
print()

print('AI Response:')
print('=' * 70)
start = time.time()
response = []
for token in chat_service.generate_response(query, context):
    response.append(token)
    print(token, end='', flush=True)

elapsed = time.time() - start
full_response = ''.join(response)
print()
print('=' * 70)
print(f'Response length: {len(full_response)} chars')
print(f'Time: {elapsed:.1f}s')
print()
print('Analysis:')
if 'cannot find' in full_response.lower():
    print('- Model says info not found')
elif 'artificial' in full_response.lower() and 'intelligence' in full_response.lower():
    print('- Model answered from context (mentions AI)')
if len(full_response) > 100:
    print('- Response is detailed')
else:
    print('- Response is brief')
if 'training' not in full_response.lower() and 'hallucinate' not in full_response.lower():
    print('- No obvious hallucinations')
