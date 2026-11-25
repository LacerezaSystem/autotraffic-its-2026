"""Exploración interactiva y reproducción de predicciones fuera del entrenamiento."""
import csv
import tkinter as tk
from tkinter import ttk, filedialog
from main import DATA, ROOT, load, metrics, write_csv

def run():
    rows=load(DATA)
    with open(ROOT/'reports/validacion.csv',encoding='utf-8') as f:
        detail=list(csv.DictReader(f))
    for r in detail:
        for k in ['real_60min','pred_60min','base_60min']: r[k]=float(r[k])
    win=tk.Tk(); win.title('AutoTraffic | Explorador temporal'); win.geometry('1180x800'); win.minsize(900,650)
    win.configure(bg='#f4f5f7')
    tk.Label(win,text='AUTOTRAFFIC · EXPLORADOR TEMPORAL',fg='#bd2637',bg='#f4f5f7',font=('Segoe UI',13,'bold')).pack(anchor='w',padx=28,pady=(20,5))
    tk.Label(win,text='Explora el día. Comprueba el pronóstico.',bg='#f4f5f7',font=('Segoe UI',24,'bold')).pack(anchor='w',padx=28)
    controls=ttk.Frame(win); controls.pack(fill='x',padx=28,pady=16)
    road=tk.StringVar(value='V1'); day=tk.StringVar(value='2026-11-13'); hour=tk.StringVar(value='08:00')
    mode=tk.StringVar(value='Evaluación de pronósticos')
    boxes=[]
    for title,var,values,width in [('Vista',mode,['Evaluación de pronósticos','Histórico observado'],28),('Vialidad',road,['V1','V2','V3'],8),('Día',day,[],14),('Hora de origen',hour,[],9)]:
        ttk.Label(controls,text=title).pack(side='left',padx=(8,4))
        box=ttk.Combobox(controls,textvariable=var,values=values,state='readonly',width=width); box.pack(side='left'); boxes.append(box)
    cards=tk.Label(win,bg='white',font=('Segoe UI',15),anchor='w',justify='left',padx=15,pady=15)
    cards.pack(fill='x',padx=28)
    navigation=ttk.Frame(win); navigation.pack(fill='x',padx=28,pady=10)
    canvas=tk.Canvas(win,bg='white',height=340,highlightthickness=0); canvas.pack(fill='both',expand=True,padx=28)
    status=tk.Label(win,bg='#f4f5f7',justify='left',anchor='w',font=('Segoe UI',11)); status.pack(fill='x',padx=28,pady=12)
    tk.Label(win,text='El volumen mide demanda; no confirma congestión. Reservado oficial pendiente.\nEn evaluación, el modelo se entrenó hasta el 11 de noviembre. Los valores reales posteriores se muestran únicamente para comprobar el resultado.',bg='#f4f5f7',fg='#555',justify='left').pack(anchor='w',padx=28,pady=(0,18))
    state={'data':[],'playing':False}
    def update(*_):
        validation=mode.get()=='Evaluación de pronósticos'
        source=detail if validation else rows
        days=sorted({r['fecha'] for r in source if r['vialidad']==road.get()}); boxes[2]['values']=days
        if day.get() not in days: day.set(days[-1])
        selected=[r for r in source if r['vialidad']==road.get() and r['fecha']==day.get()]
        times=[r['hora'] for r in selected]; boxes[3]['values']=times
        if hour.get() not in times: hour.set(times[-1])
        idx=times.index(hour.get()); r=selected[idx]; state['data']=selected
        if validation:
            cards.config(text=f'Pronóstico: {r["pred_60min"]:,.0f}     |     Real: {r["real_60min"]:,.0f}     |     Referencia: {r["base_60min"]:,.0f} vehículos / próxima hora\nError absoluto en este origen: {abs(r["pred_60min"]-r["real_60min"]):.2f} vehículos')
            series=[('real_60min','Real','#263746'),('pred_60min','Modelo','#bd2637'),('base_60min','Promedio histórico','#b08827')]
            m=metrics(selected)
            status.config(text=f'{road.get()} · {day.get()} · {len(selected)} orígenes | MAE del día: {m["mae_modelo"]:.2f} | MAE referencia: {m["mae_base"]:.2f}\nCada punto representa el total de los 60 minutos siguientes a su hora de origen. No es tráfico en vivo.')
        else:
            cards.config(text=f'{road.get()} · {day.get()} · {hour.get()}     |     {r["volumen"]} vehículos / 15 minutos\nVelocidad media: {r["velocidad_prom"] or "No disponible"} km/h')
            series=[('volumen','Observado','#bd2637')]
            peak=max(selected,key=lambda x:x['volumen'])
            status.config(text=f'Total del día: {sum(x["volumen"] for x in selected):,} vehículos | Mayor intervalo: {peak["hora"]}, {peak["volumen"]} vehículos\nExploración descriptiva de los 24 días. Esta vista no presenta predicciones ajustadas sobre entrenamiento.')
        canvas.delete('all'); w=max(800,canvas.winfo_width()); h=max(260,canvas.winfo_height()); bottom=h-40; top=max(float(x[k]) for x in selected for k,_,_ in series)*1.15 or 1
        def xx(i): return 65+i*(w-95)/max(1,len(selected)-1)
        def yy(y): return bottom-y/top*(h-90)
        for j in range(5):
            y=top*j/4; canvas.create_line(60,yy(y),w-25,yy(y),fill='#e5e7eb'); canvas.create_text(32,yy(y),text=f'{y:.0f}')
        for j,(k,name,color) in enumerate(series):
            canvas.create_text(65+j*210,20,text=name,fill=color,anchor='w',font=('Segoe UI',11,'bold'))
            points=[c for i,x in enumerate(selected) for c in (xx(i),yy(float(x[k])))]; canvas.create_line(*points,fill=color,width=2)
            canvas.create_oval(xx(idx)-4,yy(float(r[k]))-4,xx(idx)+4,yy(float(r[k]))+4,fill=color,outline='white')
        canvas.create_line(xx(idx),40,xx(idx),bottom,fill='#64748b',dash=(4,3))
        for i in sorted({0,len(selected)//4,len(selected)//2,3*len(selected)//4,len(selected)-1}): canvas.create_text(xx(i),h-18,text=selected[i]['hora'])
    def step(delta=1):
        times=[r['hora'] for r in state['data']]
        if times: hour.set(times[(times.index(hour.get())+delta)%len(times)]); update()
    def tick():
        if state['playing']: step(); win.after(700,tick)
    def play():
        state['playing']=not state['playing']; button.config(text='Pausar' if state['playing'] else 'Reproducir día')
        if state['playing']: tick()
    def export():
        p=filedialog.asksaveasfilename(defaultextension='.csv',initialfile=f'{road.get()}_{day.get()}.csv',filetypes=[('CSV','*.csv')])
        if p:
            fields=['fecha','hora','vialidad','pred_60min','base_60min','real_60min'] if mode.get()=='Evaluación de pronósticos' else ['fecha','hora','vialidad','volumen','velocidad_prom']
            write_csv(p,state['data'],fields)
    ttk.Button(navigation,text='← 15 minutos',command=lambda:step(-1)).pack(side='left')
    button=ttk.Button(navigation,text='Reproducir día',command=play); button.pack(side='left',padx=8)
    ttk.Button(navigation,text='15 minutos →',command=step).pack(side='left')
    ttk.Button(navigation,text='Exportar selección',command=export).pack(side='right')
    def click(event):
        data=state['data']; i=round((event.x-65)*(len(data)-1)/max(1,canvas.winfo_width()-95))
        if data: hour.set(data[max(0,min(len(data)-1,i))]['hora']); update()
    canvas.bind('<Button-1>',click); canvas.bind('<Configure>',update)
    for box in boxes: box.bind('<<ComboboxSelected>>',update)
    update(); win.mainloop()

if __name__=='__main__': run()
