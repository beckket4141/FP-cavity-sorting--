import zipfile
import xml.etree.ElementTree as ET

NS = {
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
}

def get_text(elem):
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

    if tag == 'r':
        texts = []
        for t in elem.findall('.//m:t', NS):
            if t.text:
                texts.append(t.text)
        return ''.join(texts)

    if tag == 'f':
        num_elem = elem.find('m:num', NS)
        den_elem = elem.find('m:den', NS)
        num = get_text(num_elem) if num_elem is not None else '?'
        den = get_text(den_elem) if den_elem is not None else '?'
        return f'({num})/({den})'

    if tag == 'sSub':
        e_elems = [c for c in elem if c.tag.split('}')[-1] == 'e']
        sub_elems = [c for c in elem if c.tag.split('}')[-1] == 'sub']
        base = get_text(e_elems[0]) if e_elems else ''
        sub = get_text(sub_elems[0]) if sub_elems else ''
        return f'{base}_{{{sub}}}'

    if tag == 'sSup':
        e_elems = [c for c in elem if c.tag.split('}')[-1] == 'e']
        sup_elems = [c for c in elem if c.tag.split('}')[-1] == 'sup']
        base = get_text(e_elems[0]) if e_elems else ''
        sup = get_text(sup_elems[0]) if sup_elems else ''
        return f'{base}^{{{sup}}}'

    if tag == 'sSubSup':
        parts = {'e': '', 'sub': '', 'sup': ''}
        for c in elem:
            t = c.tag.split('}')[-1]
            if t in parts:
                parts[t] = get_text(c)
        result = parts['e']
        if parts['sub']:
            result += f'_{{{parts["sub"]}}}'
        if parts['sup']:
            result += f'^{{{parts["sup"]}}}'
        return result

    if tag == 'rad':
        deg_elem = elem.find('m:deg', NS)
        rad_elem = elem.find('m:e', NS)
        deg = get_text(deg_elem) if deg_elem is not None else ''
        rad = get_text(rad_elem) if rad_elem is not None else ''
        if deg:
            return f'cbrt[{deg}]({rad})'
        return f'sqrt({rad})'

    if tag == 'd':
        parts = []
        for c in elem:
            parts.append(get_text(c))
        return ''.join(parts)

    if tag == 'acc':
        acc_elem = elem.find('m:accPr', NS)
        acc_char = ''
        if acc_elem is not None:
            chr_elem = acc_elem.find('m:chr', NS)
            if chr_elem is not None:
                acc_char = chr_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val', '')
        base_elem = elem.find('m:e', NS)
        base = get_text(base_elem) if base_elem is not None else ''
        return f'{base}{acc_char}'

    if tag == 'box':
        base_elem = elem.find('m:e', NS)
        if base_elem is not None:
            return get_text(base_elem)
        return ''

    if tag == 'func':
        fname_elem = elem.find('m:fName', NS)
        fname = get_text(fname_elem) if fname_elem is not None else ''
        arg_elem = elem.find('m:e', NS)
        arg = get_text(arg_elem) if arg_elem is not None else ''
        return f'{fname}({arg})'

    if tag == 'nary':
        chr_elem = elem.find('.//m:chr', NS)
        op = chr_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val', '?') if chr_elem is not None else '?'
        sub_elem = elem.find('m:sub', NS)
        sup_elem = elem.find('m:sup', NS)
        sub = get_text(sub_elem) if sub_elem is not None else ''
        sup = get_text(sup_elem) if sup_elem is not None else ''
        arg_elem = elem.find('m:e', NS)
        arg = get_text(arg_elem) if arg_elem is not None else ''
        result = op
        if sub and sup:
            result = f'{op}_{{{sub}}}^{{{sup}}}'
        elif sub:
            result = f'{op}_{{{sub}}}'
        elif sup:
            result = f'{op}^{{{sup}}}'
        return f'{result}({arg})'

    if tag == 'limLow':
        base_elem = elem.find('m:e', NS)
        lim_elem = elem.find('m:lim', NS)
        base = get_text(base_elem) if base_elem is not None else ''
        lim = get_text(lim_elem) if lim_elem is not None else ''
        return f'{base}_{{{lim}}}'

    if tag == 'eqArr':
        rows = []
        for c in elem:
            t = get_text(c)
            if t.strip():
                rows.append(t)
        return '; '.join(rows)

    if tag == 'bar':
        pos_elem = elem.find('m:barPr/m:pos', NS)
        pos = ''
        if pos_elem is not None:
            pos = pos_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val', '')
        base_elem = elem.find('m:e', NS)
        base = get_text(base_elem) if base_elem is not None else ''
        if pos == 'bot':
            return f'floor({base})'
        return f'||{base}||'

    # recurse into children
    parts = []
    for c in elem:
        t = get_text(c)
        if t.strip():
            parts.append(t)
    return ''.join(parts)


import sys
sys.stdout.reconfigure(encoding='utf-8')

docx_path = r'D:\自制软件\1.thesis\最终提交版本\Sorting in FP cavities\南大学报\manuscript\nju_jns_fp_lg_draft_template_format_authorinfo.docx'
z = zipfile.ZipFile(docx_path)
doc = z.read('word/document.xml')
root = ET.fromstring(doc)

paragraphs = root.findall('.//w:p', NS)

eq_count = 0
current_section = ''

for p in paragraphs:
    pStyle = p.find('.//w:pStyle', NS)
    if pStyle is not None:
        style_val = pStyle.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '')
        if 'Heading' in style_val or 'heading' in style_val:
            text = ''.join(t.text or '' for t in p.findall('.//w:t', NS))
            if text.strip():
                current_section = text.strip()

    maths = p.findall('.//m:oMath', NS)
    if not maths:
        maths = p.findall('.//m:oMathPara', NS)

    if maths:
        # Gather text before the first math element
        context_parts = []
        for r in p.findall('.//w:r', NS):
            t_elems = r.findall('.//w:t', NS)
            txt = ''.join(t.text or '' for t in t_elems)
            # stop at first math
            if r.find('.//m:oMath', NS) is not None or r.find('m:oMath', NS) is not None:
                break
            if txt.strip():
                context_parts.append(txt)
        context = ''.join(context_parts).strip()
        if context and len(context) > 5:
            print(f'[{current_section}] ...{context[-80:]}...')
        elif context:
            print(f'[{current_section}] ...{context}...')

        for m in maths:
            eq_count += 1
            formula = get_text(m)
            print(f'  [{eq_count}] {formula}')
        print()

z.close()
print(f'Total: {eq_count} equations')
