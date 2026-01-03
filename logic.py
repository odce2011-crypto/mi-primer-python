import random
from collections import Counter

def generar_melate():
    eq = sorted(random.sample(range(1, 57), 6))
    cz = sorted(random.sample(range(1, 57), 6))
    return eq, cz

def procesar_analitica(df):
    nums = []
    for _, r in df.iterrows():
        nums.extend(r['serie_eq'].split(','))
        nums.extend(r['serie_cz'].split(','))
    return Counter(nums).most_common(10)
