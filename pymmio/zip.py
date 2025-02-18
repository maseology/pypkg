
import zipfile 
from pymmio.files import dirList, removeExt, getFileName
from tqdm import tqdm

def batchExtract(idir):
    fps = dirList(idir)
    with tqdm(total=len(fps)) as pbar:
        for fp in fps:
            pbar.update()
            pbar.set_description(getFileName(fp, False))
            with zipfile.ZipFile(fp, 'r') as zf: 
                path=removeExt(fp)
                for member in tqdm(zf.infolist(), desc='Extracting ', leave=False):
                    try:
                        zf.extract(member, path)
                    except zipfile.error as e:
                        pass