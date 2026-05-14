content = open('src/models/trainer.py', 'r', encoding='utf-8').read()

# Fix label file path
old = 'save_path=cfg["paths"]["processed_data"] + "features.csv"\n    )'
new = 'save_path=cfg["paths"]["processed_data"] + "features.csv",\n        label_file=cfg["paths"]["raw_data"] + "labels.csv",\n    )'
content = content.replace(old, new)

# Fix unicode characters
content = content.replace('═', '=')
content = content.replace('—', '-')
content = content.replace('→', '->')

open('src/models/trainer.py', 'w', encoding='utf-8').write(content)
print('trainer.py fixed successfully!')
