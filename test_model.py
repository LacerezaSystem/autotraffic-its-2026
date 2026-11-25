import unittest
from datetime import datetime, timedelta
import main

def synthetic_rows():
    start=datetime(2026,10,25)
    return [dict(fecha=(start+timedelta(minutes=15*i)).strftime('%Y-%m-%d'),
                 hora=(start+timedelta(minutes=15*i)).strftime('%H:%M'),
                 t=start+timedelta(minutes=15*i),vialidad=v,volumen=20+(i%96),velocidad_prom='50')
            for v in ['V1','V2','V3'] for i in range(24*96)]

class ModelTests(unittest.TestCase):
    def test_temporal_prediction_and_coverage(self):
        rows=synthetic_rows()
        tr=[r for r in rows if r['t']<datetime(2026,11,12)]
        va=[r for r in rows if r['t']>=datetime(2026,11,12)]
        model=main.fit(tr,.25)
        detail=main.evaluate(model,va)
        self.assertEqual(len(detail),1716)
        self.assertAlmostEqual(main.metrics(detail)['mae_modelo'],0)
        origin=va[0]; expected=main.predict(model,origin)
        # Perturb all future observations: prediction at origin must be unchanged.
        for r in va[1:]: r['volumen']=999999
        self.assertEqual(main.predict(model,origin),expected)

    def test_target_excludes_current_interval(self):
        rows=synthetic_rows(); model=main.fit(rows,.25)
        g=[r for r in rows if r['vialidad']=='V1'][:5]
        result=main.evaluate(model,g)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['real_60min'],sum(r['volumen'] for r in g[1:]))

if __name__=='__main__': unittest.main()
