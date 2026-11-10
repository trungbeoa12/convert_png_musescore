"""Conservative image preparation. Never invent/remove musical symbols."""
from pathlib import Path
import json
import hashlib
import xml.etree.ElementTree as ET
from zipfile import ZipFile
import cv2
import numpy as np
from PIL import Image, ImageOps


def background_map(gray):
    # Morphology estimates paper lighting only, never applied to the ink output.
    h,w=gray.shape
    small=cv2.resize(gray,(max(1,w//4),max(1,h//4)))
    background=cv2.morphologyEx(small,cv2.MORPH_CLOSE,
                               cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(31,31)))
    background=cv2.GaussianBlur(background,(0,0),5)
    return cv2.resize(background,(w,h))


def deskew_image(gray):
    """Estimate a small global rotation from long horizontal segments.
    No page/sample-specific coordinates; no nonlinear dewarp or perspective warp.
    """
    a=np.array(gray);h,w=a.shape
    lines=cv2.HoughLinesP(cv2.Canny(a,80,180),1,np.pi/1800,150,
                          minLineLength=w//4,maxLineGap=30)
    angles=[] if lines is None else [float(np.degrees(np.arctan2(y2-y1,x2-x1)))
        for x1,y1,x2,y2 in lines[:,0] if abs(y2-y1)<abs(x2-x1)*.05]
    if len(angles)<5:
        return gray, {'applied':False,'reason':'insufficient long horizontal segments'}
    angle=float(np.median(angles));mad=float(np.median(np.abs(np.array(angles)-angle)))
    if mad>.5 or abs(angle)<.1:
        return gray, {'applied':False,'angle_degrees':angle,'mad_degrees':mad,
                      'reason':'inconsistent or negligible skew'}
    # Existing white margin protects symbols during this small rotation.
    matrix=cv2.getRotationMatrix2D((w/2,h/2),angle,1)
    ys,xs=np.where(a<128)
    if len(xs):
        corners=np.array([[xs.min(),ys.min(),1],[xs.max(),ys.min(),1],
                          [xs.min(),ys.max(),1],[xs.max(),ys.max(),1]]) @ matrix.T
        if (corners[:,0].min()<0 or corners[:,0].max()>=w or
                corners[:,1].min()<0 or corners[:,1].max()>=h):
            return gray, {'applied':False,'angle_degrees':angle,'reason':'rotation risks clipping ink'}
    result=cv2.warpAffine(a,matrix,
                         (w,h),flags=cv2.INTER_CUBIC,borderValue=255)
    return Image.fromarray(result), {'applied':True,'angle_degrees':angle,
                                    'mad_degrees':mad,'segments':len(angles)}


def prepare(source, target, enhance=True, profile='auto'):
    if profile not in ('auto','legacy','original','illumination','deskew'):
        raise ValueError('Unknown image profile')
    target=Path(target);folder=target.parent/'preprocessing';folder.mkdir(exist_ok=True)
    with Image.open(source) as im:
        source_size=list(im.size)
        source_mode=im.mode
        source_dpi=im.info.get('dpi')
        if getattr(im,'n_frames',1)>1:raise ValueError('Chỉ nhận ảnh một trang.')
        if im.width*im.height>40_000_000:raise ValueError('Ảnh quá lớn (trên 40 triệu pixel).')
        im=ImageOps.exif_transpose(im)
        rgba=im.convert('RGBA');white=Image.new('RGBA',rgba.size,'white');white.alpha_composite(rgba)
        gray=white.convert('L');gray.save(folder/'01_gray.png')
    a=np.array(gray);bg=background_map(a)
    p10,p50,p90=[float(v) for v in np.percentile(bg,[10,50,90])]
    report={'requested_profile':profile,'source_size':source_size,'source_mode':source_mode,
            'source_dpi':source_dpi,'enhance':enhance,'paper_brightness_percentiles':[p10,p50,p90],
            'uneven_or_dark_paper':p50<235 or p90-p10>18,
            'warnings':[],'operations':['EXIF orientation','alpha composite on white','grayscale'],
            'decision':'auto retains legacy pixels; geometry and lighting correction require explicit profiles; no accuracy ranking'}
    Image.fromarray(bg).save(folder/'02_background_estimate.png')
    if report['uneven_or_dark_paper']:
        report['warnings'].append('Nền tối/không đều: cần kiểm tra ký hiệu nhỏ. Cân bằng nền chưa được chứng minh luôn tốt hơn.')
    if profile=='illumination' and enhance:
        a=np.clip(a.astype(np.float32)*255/np.maximum(bg,1),0,255).astype(np.uint8)
        gray=Image.fromarray(a);gray.save(folder/'03_illumination.png')
        report['operations'].append('divide by low-frequency background (experimental)')
    if enhance and profile!='original':
        gray=ImageOps.autocontrast(gray,cutoff=0.1)
        if max(gray.size)<2000 and gray.width*gray.height<=10_000_000:
            gray=gray.resize((gray.width*2,gray.height*2),Image.Resampling.BICUBIC)
            report['operations'].append('legacy 2x bicubic')
        gray=ImageOps.expand(gray,border=30,fill=255)
        report['operations'].append('legacy contrast and 30px white margin')
    if enhance and profile=='deskew':
        gray.save(folder/'04_before_deskew.png')
        gray,report['deskew']=deskew_image(gray)
        report['operations'].append('experimental global deskew (see measured angle)')
    gray.save(target,dpi=(300,300))
    report['prepared_size']=list(gray.size)
    report['prepared_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    report['encoding']='lossless PNG; 300 DPI is metadata, not measured source resolution'
    report['variants']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.png')}
    (folder/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report


def straighten_staff_lines(input_path, omr_path, output_path):
    """Experimental second-pass vertical dewarp from measured full staff lines.
    Does not crop systems, change pitches, or infer page corners. Reject incomplete,
    crossing, strongly divergent or large displacements instead of forcing a warp.
    Keeps the full page and the header context. Always keep first-pass result.
    """
    a=np.array(Image.open(input_path).convert('L'));h,w=a.shape;xs=np.arange(w)
    curves=[]
    with ZipFile(omr_path) as z:
        sheets=[n for n in z.namelist() if n.startswith('sheet#') and n.endswith('.xml')]
        if len(sheets)!=1:raise ValueError('Chỉ sửa hình học ảnh một trang.')
        root=ET.fromstring(z.read(sheets[0]))
    for staff in root.findall('.//staff'):
        lines=staff.findall('lines/line')
        if len(lines)!=5:raise ValueError('Không đủ 5 đường khuông; bỏ sửa hình học.')
        staff_curves=[]
        for line in lines:
            points=np.array([(float(p.get('x')),float(p.get('y'))) for p in line.findall('point')])
            if len(points)<2 or points[-1,0]-points[0,0]<w*.4:
                raise ValueError('Đường khuông quá ngắn; không tự sửa hình học.')
            if np.any(np.diff(points[:,0])<=0):raise ValueError('Tọa độ đường khuông không hợp lệ.')
            staff_curves.append(np.interp(xs,points[:,0],points[:,1]))
        spacing=np.diff(staff_curves,axis=0)
        if np.min(spacing)<3 or np.max(spacing)/np.min(spacing)>1.6:
            raise ValueError('Khoảng cách khuông không ổn định; cần sửa phối cảnh thủ công.')
        curves.extend(staff_curves)
    if not curves:raise ValueError('Không tìm được khuông để sửa hình học.')
    curves=np.array(curves);curves=curves[np.argsort(np.median(curves,axis=1))]
    targets=np.median(curves,axis=1)
    if np.min(np.diff(curves,axis=0))<=0:raise ValueError('Đường khuông giao nhau; không tự sửa.')
    displacement=float(np.max(np.abs(curves-targets[:,None])))
    if displacement>h*.08:raise ValueError('Độ cong/nghiêng quá lớn; cần xử lý ảnh thủ công.')
    if targets[0]<=0 or targets[-1]>=h-1:raise ValueError('Khuông sát mép; không tự sửa.')
    mapy=np.empty((h,w),np.float32)
    for x in range(w):mapy[:,x]=np.interp(np.arange(h),np.r_[0,targets,h-1],np.r_[0,curves[:,x],h-1])
    result=cv2.remap(a,np.tile(xs,(h,1)).astype(np.float32),mapy,cv2.INTER_CUBIC,
                     borderMode=cv2.BORDER_CONSTANT,borderValue=255)
    Image.fromarray(result).save(output_path)
    info={'max_vertical_displacement_px':displacement,'staff_count':len(curves)//5,
          'horizontal_perspective_corrected':False,'experimental':True,
          'target_y':targets.tolist(),'sample_x':xs[::max(1,w//20)].tolist(),
          'source_y_samples':curves[:,::max(1,w//20)].tolist()}
    Path(output_path).with_suffix('.json').write_text(json.dumps(info,indent=2))
    return info
