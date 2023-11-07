# Russian text normalization for TTS
Normalize Text in Russian.


Usage:
Add russian.py into `text` folder of your TTS system and import it from there. 

```
from text.russian import normalize_russian

complex_test_text = """У меня есть $1234 и 5678 рублей. Кроме того, я должен 90.50€ и взял в долг 4321 GBP.
В моем кошельке было 876 UAH и 543.21 RUB, а также я нашел 20 центов."""
​
normalized_text = normalize_russian(complex_test_text)
print(normalized_text)
```

​Prints:

```
У меня есть одна тысяча двести тридцать четыре доллара и пять тысяч шестьсот семьдесят восемь рублей. Кроме того, я должен девяносто евро пятьдесят евроцентов и взял в долг четыре тысячи триста двадцать один фунт.\nВ моем кошельке было восемьсот семьдесят шесть гривен и пятьсот сорок три рубля двадцать один копейка, а также я нашел 20 центов.
```

# Implemented 
1. Cyrrilization of letters such as "apple" -> "эппл". 
2. Abbreviations expansion such as "СССР" -> "эс эс эс эр". 
3. Numbers conversion of any size
4. Currency expansion
5. Phone number expansion
6. Date

# Not implemented
1. Time
2. Percentages
3. Short forms like "г." -> "город"
3. Probably a lot more

# Acknowledgements
I want to thank OpenAI's ChatGPT for writing this code. I would've never been able to write it myself since I'm too lazy for that.

# Call for collaboration
Feel free to use this code. You can share it, copy it, modify as you wish. However, pretty please, *if you improved the solution somehow, add your modifications here too.*

