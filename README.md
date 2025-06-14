Installation des dépendances
- (conseillé) en utilisant `uv` (https://docs.astral.sh/uv/#installation)

```
git clone https://github.com/velo-cite/BxMetroDataAnalysis.git
uv sync
```

- en utilisant `pip`
```
git clone https://github.com/velo-cite/BxMetroDataAnalysis.git
cd BxMetroDataAnalysis
python -m venv .venv
source .venv/bin/activate
pip install .
```

Vous devez demander une clé pour acceder à l'API de Bordeaux Metropole (https://data.bordeaux-metropole.fr/opendata/key) puis la coller dans le fichier .env.local en prenant exemple sur le fichier .env

Scripts:
- vitesses_bus.py: affiche les vitesses des bus de la Metropole de Bordeaux.
