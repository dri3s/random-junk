

import pypdfium2 as pdfium
import os
#import cv2
#from skimage import io
from PIL import Image
import numpy as np
import pandas as pd
from scipy.signal import argrelextrema as x
#import os

path = r"C:\Users\Owner\Downloads\IMSLP06010-Medtner_8moods_op1.pdf"
outfolder = r"C:\Users\Owner\Documents\pngs"

pdf = pdfium.PdfDocument(path)
os.startfile(path)


for pg in range(18, 23):
    outpath = os.path.join(outfolder, f'{pg}.png')
    
    page = pdf.get_page(pg)
    
    pil_image = page.render().to_pil()
    pil_image.save(outpath)
    img = Image.open(outpath)    
    
    arr = np.asarray(img)
    
    arr = arr/255
    arr = np.round(arr)
    
    wtff = pd.DataFrame(arr.mean(axis=(2)))
    wtff = wtff.mean(axis=1)
    
    starts = x(wtff.values, np.greater_equal, order=80)[0]
    
    starts = np.split(starts, np.where(np.diff(starts) > 10 )[0]+1)
    starts = [s.mean().round() for s in starts]
    starts = np.array(starts)
    
    print(starts)
    
    width, height = img.size
    
    for crop in range(len(starts)):
        if crop < len(starts) - 1:
            im_crop = img.copy().crop((0, starts[crop], width, starts[crop+1]))
            croppath = os.path.join(outfolder, f'{pg}_{crop}.png')
            im_crop.save(croppath)
        
    
    
    
    
