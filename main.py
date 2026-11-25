"""AutoTraffic: prototipo local, sin dependencias externas."""
import argparse, csv, json, math, statistics, hashlib
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/trafico_desarrollo.csv'

def load(path):
    with open(path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    seen = set()
    for r in rows:
        r['t'] = datetime.fromisoformat(r['fecha']+'T'+r['hora'])
        r['volumen'] = int(r['volumen'])
        key = (r['vialidad'], r['t'])
        if key in seen or r['volumen'] < 0: raise ValueError('Duplicado o volumen negativo')
        seen.add(key)
    rows.sort(key=lambda r: (r['vialidad'], r['t']))
    for v in {r['vialidad'] for r in rows}:
        g = [r for r in rows if r['vialidad']==v]
        if any(b['t']-a['t'] != timedelta(minutes=15) for a,b in zip(g,g[1:])):
            raise ValueError('La serie contiene huecos: '+v)
    return rows

def key(v,t): return f'{v}/{t.weekday()}/{t:%H:%M}'

def fit(rows, alpha):
    groups = {}
    for r in rows: groups.setdefault(key(r['vialidad'],r['t']),[]).append(r['volumen'])
    return {'alpha':alpha, 'profile':{k:statistics.mean(x) for k,x in groups.items()},
            'training_end':max(r['t'] for r in rows).isoformat(), 'method':'Perfil semanal con correccion aprendida'}

def predict(model,r):
    p=model['profile']; t=r['t']; v=r['vialidad']
    base=sum(p[key(v,t+timedelta(minutes=15*k))] for k in range(1,5))
    pred=max(0,base+4*model['alpha']*(r['volumen']-p[key(v,t)]))
    return pred,base

def evaluate(model, rows):
    lookup={(r['vialidad'],r['t']):r['volumen'] for r in rows}; result=[]
    for r in rows:
        keys=[(r['vialidad'],r['t']+timedelta(minutes=15*k)) for k in range(1,5)]
        if not all(k in lookup for k in keys): continue
        pred,base=predict(model,r)
        result.append({'fecha':r['fecha'],'hora':r['hora'],'vialidad':r['vialidad'],
                       'pred_60min':pred,'base_60min':base,'real_60min':sum(lookup[k] for k in keys)})
    if not result: raise ValueError('No hay origenes evaluables')
    return result

def metrics(rows):
    mae=statistics.mean(abs(r['pred_60min']-r['real_60min']) for r in rows)
    base=statistics.mean(abs(r['base_60min']-r['real_60min']) for r in rows)
    return {'origenes':len(rows),'mae_modelo':mae,'mae_base':base,'mejora_pct':100*(1-mae/base) if base else None}

def write_csv(path,rows,fields):
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)

def train():
    rows=load(DATA); out=ROOT/'reports'; out.mkdir(exist_ok=True)
    initial=[r for r in rows if r['t']<datetime(2026,11,6)]
    tuning=[r for r in rows if datetime(2026,11,6)<=r['t']<datetime(2026,11,12)]
    candidates=[]
    for a in [0,.25,.5,.75,1]:
        candidates.append({'alpha':a,**metrics(evaluate(fit(initial,a),tuning))})
    alpha=min(candidates,key=lambda r:r['mae_modelo'])['alpha']
    training=[r for r in rows if r['t']<datetime(2026,11,12)]
    validation=[r for r in rows if r['t']>=datetime(2026,11,12)]
    detail=evaluate(fit(training,alpha),validation)
    summary={'seleccion':candidates,'alpha':alpha,'validacion':metrics(detail),
             'por_vialidad':{v:metrics([r for r in detail if r['vialidad']==v]) for v in ['V1','V2','V3']},
             'advertencia':'Validacion de desarrollo; reservado pendiente. Ventana 12-17 noviembre ya explorada previamente.'}
    (out/'metricas.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    write_csv(out/'validacion.csv',detail,list(detail[0]))
    model=fit(rows,alpha); model['data_sha256']=hashlib.sha256(DATA.read_bytes()).hexdigest()
    (ROOT/'modelo.json').write_text(json.dumps(model,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

def final(path):
    model=json.loads((ROOT/'modelo.json').read_text(encoding='utf-8')); rows=load(path)
    if min(r['t'] for r in rows)<=datetime.fromisoformat(model['training_end']):
        raise ValueError('El reservado debe ser posterior al entrenamiento')
    detail=evaluate(model,rows)
    if len(detail)!=1716: raise ValueError(f'Se esperan 1716 origenes, recibidos {len(detail)}')
    write_csv(ROOT/'predicciones.csv',detail,['fecha','hora','vialidad','pred_60min'])
    (ROOT/'reports/evaluacion_final.json').write_text(json.dumps(metrics(detail),indent=2),encoding='utf-8')
    print(metrics(detail))

def gui():
    import tkinter as tk
    from tkinter import ttk
    rows=load(DATA)
    model=json.loads((ROOT/'modelo.json').read_text(encoding='utf-8'))
    summary=json.loads((ROOT/'reports/metricas.json').read_text(encoding='utf-8'))
    win=tk.Tk(); win.title('AutoTraffic | Pronostico de demanda'); win.geometry('1100x740'); win.configure(bg='#f5f5f3')
    tk.Label(win,text='AUTOTRAFFIC  /  PROTOTIPO',font=('Segoe UI',12,'bold'),fg='#ba2335',bg='#f5f5f3').pack(anchor='w',padx=30,pady=(24,8))
    tk.Label(win,text='La siguiente hora, con evidencia.',font=('Segoe UI',26,'bold'),bg='#f5f5f3').pack(anchor='w',padx=30)
    tk.Label(win,text='Datos historicos · Tres vialidades · Sin fuentes en vivo',bg='#f5f5f3',font=('Segoe UI',11)).pack(anchor='w',padx=30,pady=8)
    controls=ttk.Frame(win); controls.pack(fill='x',padx=30,pady=12)
    road=tk.StringVar(value='V1'); picker=ttk.Combobox(controls,textvariable=road,values=['V1','V2','V3'],state='readonly',width=10); picker.pack(side='left')
    label=tk.Label(win,font=('Segoe UI',15),bg='#f5f5f3',justify='left'); label.pack(anchor='w',padx=30,pady=8)
    canvas=tk.Canvas(win,bg='white',height=290,highlightthickness=0); canvas.pack(fill='x',padx=30,pady=10)
    info=tk.Label(win,font=('Segoe UI',11),bg='#f5f5f3',justify='left'); info.pack(anchor='w',padx=30,pady=8)
    tk.Label(win,text='El volumen indica demanda. No confirma congestion.\nPronostico desde el ultimo intervalo observado; las metricas corresponden a validacion temporal.',bg='#f5f5f3',fg='#555',justify='left').pack(anchor='w',padx=30,pady=12)
    def update(*_):
        g=[r for r in rows if r['vialidad']==road.get()]; r=g[-1]; pred,base=predict(model,r); m=summary['por_vialidad'][road.get()]
        label.config(text=f'Siguiente hora: {pred:,.0f} vehiculos     |     Referencia: {base:,.0f}\nOrigen: {r["fecha"]} {r["hora"]} · Modelo entrenado hasta este origen')
        canvas.delete('all'); w=max(canvas.winfo_width(),900); vals=[x['volumen'] for x in g[-96:]]; top=max(vals)*1.15
        canvas.create_text(20,20,text='Ultimas 24 horas · vehiculos por intervalo de 15 minutos',anchor='w',font=('Segoe UI',11,'bold'))
        points=[]
        for i,y in enumerate(vals): points.extend([55+i*(w-90)/95,245-y/top*185])
        canvas.create_line(*points,fill='#bd2637',width=2)
        for i in range(5):
            y=245-i*185/4; canvas.create_text(30,y,text=str(round(top*i/4))); canvas.create_line(50,y,w-25,y,fill='#eeeeee')
        for i in [0,24,48,72,95]: canvas.create_text(55+i*(w-90)/95,270,text=g[-96+i]['hora'])
        slots={}
        for x in g: slots.setdefault(x['hora'],[]).append(x['volumen'])
        peak=max(slots,key=lambda k:statistics.mean(slots[k]))
        info.config(text=f'Validacion 12–17 nov. | MAE modelo: {m["mae_modelo"]:.2f} | MAE referencia: {m["mae_base"]:.2f} | Mejora: {m["mejora_pct"]:.1f}%\nFranja de mayor demanda media: {peak} | Reservado: pendiente')
    picker.bind('<<ComboboxSelected>>',update); win.after(100,update); win.mainloop()

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['train','app','final']); p.add_argument('--reservado'); a=p.parse_args()
    if a.command=='train': train()
    elif a.command=='app':
        from dashboard import run
        run()
    elif a.reservado: final(a.reservado)
    else: p.error('Falta --reservado')
