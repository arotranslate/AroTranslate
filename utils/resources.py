FUH = {}
FAH = {}

with open("resources/fuh.json", "r") as json_file:
    FUH = json.load(json_file)
with open("resources/fah.json", "r") as json_file:
    FAH = json.load(json_file)

df = pd.read_csv("resources/cunia_diaro.csv")
CUNIA2DIARO_WD_MAP = dict(zip(df.cunia, df.diaro))
