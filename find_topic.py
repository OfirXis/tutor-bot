import json

c = json.load(open('db/curriculum.json', encoding='utf-8'))
for week in c['weeks']:
    for topic in week['topics']:
        if 'rami' in topic['name'].lower():
            print(f"Week {week['week']}: {topic['id']}")
            print(f"  Name: {topic['name']}")
            print(f"  Aliases: {topic.get('aliases', [])}")
