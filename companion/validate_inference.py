"""Reproducible synthetic product check; explicitly invokes local model only."""
import io,json,os,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from fastapi.testclient import TestClient
import server

def main():
    out=Path(__file__).parent/'examples';out.mkdir(exist_ok=True)
    # Original self-created illustration; no third-party photo or personal data.
    image=Image.new('RGB',(768,768),(237,232,225))
    draw=ImageDraw.Draw(image)
    for y in range(768):
        c=int(244-22*y/768); draw.line((0,y,768,y),fill=(c,c-3,c-8))
    shadow=Image.new('RGBA',image.size)
    ImageDraw.Draw(shadow).ellipse((200,628,590,700),fill=(30,20,10,65))
    image=Image.alpha_composite(image.convert('RGBA'),shadow.filter(ImageFilter.GaussianBlur(17)))
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((270,195,495,658),radius=46,fill='#517563',outline='#314e40',width=3)
    draw.rounded_rectangle((294,133,471,236),radius=20,fill='#344138')
    draw.rectangle((298,160,467,206),fill='#2d3730')
    draw.rounded_rectangle((292,326,473,532),radius=7,fill='#f5edda')
    draw.text((327,376),'BOTANIC',fill='#334d3b',stroke_width=1)
    draw.text((332,418),'HAND SOAP',fill='#53614b')
    draw.text((343,478),'300 ml',fill='#53614b')
    draw.rounded_rectangle((286,250,305,575),radius=9,fill=(113,145,125))
    image.convert('RGB').save(out/'synthetic-bottle-input.jpg',quality=95)
    source=(out/'synthetic-bottle-input.jpg').read_bytes()
    client=TestClient(server.app,base_url='http://127.0.0.1:4174')
    started=time.monotonic()
    r=client.post('/api/remove-background',headers={'Origin':'http://127.0.0.1:4173','X-Seller-Frame':'local'},files={'image':('bottle.jpg',source,'image/jpeg')})
    elapsed=time.monotonic()-started
    if r.status_code!=200: raise RuntimeError(f'{r.status_code}: {r.text}')
    (out/'synthetic-bottle-cutout.png').write_bytes(r.content)
    result=Image.open(io.BytesIO(r.content)).convert('RGBA'); alpha=np.asarray(result.getchannel('A'))
    comparison=Image.new('RGB',(1536,768),'#e9e9e9');comparison.paste(image.convert('RGB'),(0,0))
    for y in range(0,768,32):
        for x in range(768,1536,32):
            ImageDraw.Draw(comparison).rectangle((x,y,x+31,y+31),fill='#f5f5f5' if (x//32+y//32)%2 else '#dddddd')
    comparison.paste(result,(768,0),result);comparison.save(out/'synthetic-bottle-comparison.jpg',quality=90)
    metrics={'status':r.status_code,'seconds':round(elapsed,2),'size':list(result.size),'alpha_min':int(alpha.min()),'alpha_max':int(alpha.max()),'background_mean_alpha':float(alpha[:100,:100].mean()),'subject_mean_alpha':float(alpha[300:600,330:430].mean()),'input':'self-created synthetic bottle illustration, not a real photograph'}
    (out/'inference-result.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics),flush=True)

if __name__=='__main__':main()
