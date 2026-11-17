from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
(HERE/'inputs').mkdir(parents=True,exist_ok=True)
(HERE/'raw').mkdir(exist_ok=True)
(HERE/'media').mkdir(exist_ok=True)
src=ROOT/'src/.tmp/fire-kit-showcase-v19/current/FIR_03/000.jpg'
Image.open(src).crop((210,60,660,450)).save(HERE/'inputs/native-player-crop.png')
print(HERE/'inputs/native-player-crop.png')
