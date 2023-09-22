import torch

model, example_texts, languages, punct, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                                                  model='silero_te')

def enhance(text, lan='en'):
    return model.enhance_text(text, lan)

def warmup():
    model.enhance_text('test', 'en')
    model.enhance_text('test', 'en')