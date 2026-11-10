"""Read-only semantic audits; no correction of musical content."""
from collections import Counter
from fractions import Fraction
import json
import re
from difflib import SequenceMatcher
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from pathlib import Path
from PIL import Image, ImageDraw


def normalize_short_page(root, target):
    """Create a layout-only import copy for cropped strips with unusable paper size.
    The caller retains raw MusicXML. A semantic invariant prevents note changes.
    """
    import copy
    defaults=root.find('defaults')
    if defaults is None or defaults.find('page-layout') is None:
        return False
    scaling=defaults.find('scaling')
    if scaling is None:
        return False
    unit=float(scaling.findtext('millimeters','7'))/float(scaling.findtext('tenths','40'))
    height=float(defaults.findtext('page-layout/page-height','1000'))*unit
    if height>=120:
        return False
    original=snapshot(root)
    result=copy.deepcopy(root)
    defaults=result.find('defaults')
    defaults.find('scaling/millimeters').text='7'
    defaults.find('scaling/tenths').text='40'
    layout=defaults.find('page-layout')
    for child in list(layout):
        layout.remove(child)
    for tag,value in [('page-width',297*40/7),('page-height',210*40/7)]:
        ET.SubElement(layout,tag).text=str(value)
    margins=ET.SubElement(layout,'page-margins',type='both')
    for tag in ('left-margin','right-margin','top-margin','bottom-margin'):
        ET.SubElement(margins,tag).text=str(10*40/7)
    for element in result.iter():
        element.attrib.pop('default-x',None)
        element.attrib.pop('default-y',None)
        if element.tag=='measure':element.attrib.pop('width',None)
        if element.tag=='print':
            for child in list(element):
                if child.tag in ('system-layout','staff-layout','page-layout'):element.remove(child)
    if snapshot(result)!=original:
        raise ValueError('Layout normalization unexpectedly changed musical content')
    ET.ElementTree(result).write(target,encoding='utf-8',xml_declaration=True)
    return True


def snapshot(root):
    parts=[]
    for part in root.findall('part'):
        divisions=1; context={'clefs':[], 'key':None,'time':None};measures=[]
        for measure in part.findall('measure'):
            a=measure.find('attributes')
            if a is not None:
                divisions=int(a.findtext('divisions',str(divisions)))
                if a.find('key') is not None:context['key']=a.findtext('key/fifths')
                if a.find('time') is not None:context['time']='/'.join([a.findtext('time/beats','?'),a.findtext('time/beat-type','?')])
                if a.findall('clef'):context['clefs']=[(c.get('number','1'),c.findtext('sign'),c.findtext('line'),c.findtext('clef-octave-change','0')) for c in a.findall('clef')]
            events=[];cursor=Fraction();onset=Fraction()
            for n in measure:
                if n.tag in ('backup','forward'):
                    cursor+=Fraction(n.findtext('duration','0'))/divisions*(-1 if n.tag=='backup' else 1)
                if n.tag!='note':continue
                grace=n.find('grace') is not None
                duration=Fraction(n.findtext('duration','0'))/divisions
                if n.find('chord') is None:onset=cursor
                pitch='R' if n.find('rest') is not None else ':'.join(n.findtext('pitch/'+f,'0') for f in ('step','alter','octave'))
                events.append({'pitch':pitch,'duration':str(duration),'type':n.findtext('type'),
                               'dots':len(n.findall('dot')),'accidental':n.findtext('accidental'),
                               'grace':grace,'ties':sorted(t.get('type') for t in n.findall('tie')),
                               'slurs':sorted(s.get('type') for s in n.findall('notations/slur')),
                               'voice':n.findtext('voice','1'),'staff':n.findtext('staff','1'),
                               'onset':str(onset),'beams':[(b.get('number'),b.text) for b in n.findall('beam')]})
                if not grace and n.find('chord') is None:cursor+=duration
            measures.append({'number':measure.get('number'), 'implicit':measure.get('implicit'),
                             'context':dict(context),'events':events,
                             'words':[e.text for e in measure.findall('.//words')],
                             'barlines':[(b.get('location','right'),b.findtext('bar-style'),
                                          b.find('repeat').get('direction') if b.find('repeat') is not None else None)
                                         for b in measure.findall('barline')]})
        parts.append({'id':part.get('id'),'measures':measures})
    return {'parts':parts, 'credits':[e.text for e in root.findall('.//credit-words')]}


def edit_distance(a,b):
    row=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        new=[i]
        for j,y in enumerate(b,1):new.append(min(new[-1]+1,row[j]+1,row[j-1]+(x!=y)))
        row=new
    return row[-1]


def compare(reference, actual):
    """Distances on ordered feature streams; not accuracy percentages.
    Order is XML order (within each part); multi-voice ordering can differ.
    """
    flatten=lambda s:[e for p in s['parts'] for m in p['measures'] for e in m['events']]
    ref,got=flatten(reference),flatten(actual)
    fields=['pitch','duration','dots','accidental','grace','ties','slurs','voice','staff','onset','beams']
    distances={f:edit_distance([e[f] for e in ref],[e[f] for e in got]) for f in fields}
    distances['pitch_duration']=edit_distance([(e['pitch'],e['duration']) for e in ref],[(e['pitch'],e['duration']) for e in got])
    locations=lambda s:[{'part':p['id'],'measure':m['number'],'event':i+1,'pitch':e['pitch'],'duration':e['duration']}
                        for p in s['parts'] for m in p['measures'] for i,e in enumerate(m['events'])]
    ref_locations,got_locations=locations(reference),locations(actual)
    alignment=SequenceMatcher(None,[(e['pitch'],e['duration']) for e in ref],
                              [(e['pitch'],e['duration']) for e in got],autojunk=False)
    changed=[{'operation':tag,'reference':ref_locations[a:b],'actual':got_locations[c:d]}
             for tag,a,b,c,d in alignment.get_opcodes() if tag!='equal']
    contexts=lambda s:[m['context'] for p in s['parts'] for m in p['measures']]
    # Flat note streams alone miss moved barlines and shifted onsets. Compare
    # measure-local events independently of cosmetic measure numbers/implicit flags.
    structure=lambda s:[[[ (e['pitch'],e['duration'],e['onset'],e['voice'],e['staff'])
                           for e in m['events']] for m in p['measures']] for p in s['parts']]
    annotations=lambda s:[(m.get('words',[]),m.get('barlines',[])) for p in s['parts'] for m in p['measures']]
    return {'reference_events':len(ref),'actual_events':len(got), 'edit_distances':distances,
            'structure_equal':structure(reference)==structure(actual),
            'annotations_equal':annotations(reference)==annotations(actual),
            'credits_equal':reference.get('credits',[])==actual.get('credits',[]),
            'changed_event_regions':changed,'contexts_equal':contexts(reference)==contexts(actual),
            'reference_measures':sum(len(p['measures']) for p in reference['parts']),
            'actual_measures':sum(len(p['measures']) for p in actual['parts']),
            'note':'Independent feature edit distances; insertions/deletions also affect feature distances. Not calibrated accuracy.'}


def summarize(s):
    events=[e for p in s['parts'] for m in p['measures'] for e in m['events']]
    return {'parts':len(s['parts']),'measures':sum(len(p['measures']) for p in s['parts']),
            'notes':sum(e['pitch']!='R' for e in events),'rests':sum(e['pitch']=='R' for e in events),
            'dots':sum(e['dots'] for e in events),'grace':sum(e['grace'] for e in events),
            'accidentals':dict(Counter(e['accidental'] for e in events if e['accidental'])),
            'ties':dict(Counter(t for e in events for t in e['ties'])),
            'slurs':dict(Counter(t for e in events for t in e['slurs'])),
            'voices':sorted(set(e['voice'] for e in events)), 'staves':sorted(set(e['staff'] for e in events)),
            'contexts':[m['context'] for p in s['parts'] for m in p['measures']][:1]}


def engine_review(omr_path, input_path, folder, log_path=None):
    """Retain real engine grades, bounds, stack IDs and source crops.
    Grades are internal classifier scores, NOT probabilities of correctness.
    Review priority <0.5 is a heuristic, and excludes no symbols from the export.
    """
    folder=Path(folder);folder.mkdir(exist_ok=True,parents=True)
    records=[];regions=[]
    log=Path(log_path).read_text(encoding='utf-8',errors='replace') if log_path else ''
    # Do not mark a repaired second-pass region using first-pass rhythm errors.
    sections=[s for s in log.split('\nCOMMAND: ')
              if str(Path(omr_path).parent) in s.split('\n',1)[0] and 'Audiveris' in s.split('\n',1)[0]]
    if sections:
        log=sections[-1]
    bad_stacks=set(re.findall(r'S(\d+) MeasureStack#(-?\d+) no correct rhythm',log))
    with ZipFile(omr_path) as z:
        for member in z.namelist():
            if not re.fullmatch(r'sheet#\d+/sheet#\d+\.xml',member):continue
            root=ET.fromstring(z.read(member))
            for system in root.findall('.//system'):
                sid=system.get('id');points=system.findall('./part/staff/lines/line/point')
                ys=[float(pt.get('y')) for pt in points]
                if not ys:continue
                interline=float(root.find('scale/interline').get('main','20')) if root.find('scale/interline') is not None else 20
                top=max(0,min(ys)-3*interline);bottom=max(ys)+3*interline
                for stack in system.findall('stack'):
                    regions.append({'sheet':member.split('/')[0],'system':sid,'stack':stack.get('id'),
                                    'bounds':[float(stack.get('left')),top,float(stack.get('right')),bottom],
                                    'expected':stack.get('expected'),'duration':stack.get('duration'),
                                    'special':stack.get('special'),
                                    'rhythm_warning':(sid,stack.get('id')) in bad_stacks})
                for inter in system.findall('./sig/inters/*'):
                    bounds=inter.find('bounds')
                    if bounds is None or 'grade' not in inter.attrib:continue
                    grade=float(inter.get('ctx-grade',inter.get('grade')))
                    if inter.tag not in ('head','small-head','rest','flag','beam','beam-hook','alter','augmentation-dot','slur','clef','key','time-number'):continue
                    b=[float(bounds.get(k)) for k in ('x','y','w','h')];x=b[0]+b[2]/2
                    stack=next((s['stack'] for s in regions if s['sheet']==member.split('/')[0] and s['system']==sid and s['bounds'][0]<=x<=s['bounds'][2]),None)
                    records.append({'sheet':member.split('/')[0],'system':sid,'stack':stack,'inter_id':inter.get('id'),
                                    'symbol':inter.tag,'shape':inter.get('shape'),'bounds_xywh':b,
                                    'engine_grade':float(inter.get('grade')), 'engine_context_grade':grade,
                                    'review_priority':grade<0.5})
            for binary in (member.split('/')[0]+'/BINARY.png',):
                if binary in z.namelist():(folder/(member.split('/')[0]+'_binary.png')).write_bytes(z.read(binary))
    im=Image.open(input_path).convert('RGB');draw=ImageDraw.Draw(im)
    for i,region in enumerate(regions,1):
        b=tuple(round(v) for v in region['bounds']);box=(max(0,b[0]),max(0,b[1]),min(im.width,b[2]),min(im.height,b[3]))
        region['crop']=f'region_{i:03}.png'
        with Image.open(input_path) as original:original.crop(box).save(folder/region['crop'])
        color='red' if region['rhythm_warning'] else 'blue'
        draw.rectangle(box,outline=color,width=3);draw.text((box[0]+3,box[1]+2),f"S{region['system']} stack {region['stack']}",fill=color)
    for rec in records:
        if rec['review_priority']:
            x,y,w,h=rec['bounds_xywh'];draw.rectangle((x,y,x+w,y+h),outline='red',width=2)
    im.save(folder/'review_overlay.png')
    result={'notice':'Engine grades are not confidence percentages. Red boxes: heuristic review priority. Stack IDs may differ from exported measure numbers.',
            'regions':regions,'symbols':records,'priority_count':sum(r['review_priority'] for r in records),
            'rhythm_region_count':sum(r['rhythm_warning'] for r in regions)}
    (folder/'locations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return result
